import pandas as pd
from typing import Dict, List
import time
import os
import shutil

def select_environment() -> str:
    """
    Let user select the environment (dev/prod).
    Default is 'dev' if no input is provided.
    
    Returns:
        str: Selected environment ('dev' or 'prod')
    """
    while True:
        env = input("Select environment (dev/prod) [default: dev]: ").lower().strip()
        if env == '':
            return 'dev'
        if env in ['dev', 'prod']:
            return env
        print("Invalid environment. Please enter 'dev' or 'prod' (or press Enter for dev)")

def ensure_output_dir(env: str) -> None:
    """
    Ensure output directory exists for the selected environment.
    
    Args:
        env (str): Selected environment ('dev' or 'prod')
    """
    output_dir = f"{env}/output"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def load_data_files(primekg_file: str, other_resources_file: str) -> pd.DataFrame:
    """
    Load and merge data from PrimeKG and other resources files.
    
    Args:
        primekg_file (str): Path to PrimeKG CSV file
        other_resources_file (str): Path to other resources CSV file
        
    Returns:
        pd.DataFrame: Merged dataframe
    """
    # Load both files
    primekg_df = pd.read_csv(primekg_file)
    other_df = pd.read_csv(other_resources_file) if other_resources_file else pd.DataFrame()
    
    # Merge dataframes if other_df exists
    if not other_df.empty:
        df = pd.concat([primekg_df, other_df], ignore_index=True)
    else:
        df = primekg_df
        
    return df

def load_properties(properties_file: str) -> pd.DataFrame:
    """
    Load properties from CSV file.
    
    Args:
        properties_file (str): Path to properties CSV file
        
    Returns:
        pd.DataFrame: Properties dataframe
    """
    return pd.read_csv(properties_file)

def create_nodes_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create nodes dataframe from input dataframe's x and y columns.
    
    Args:
        df (pd.DataFrame): Input dataframe containing node information
        
    Returns:
        pd.DataFrame: Combined nodes dataframe
    """
    # Create nodes dataframe from x and y columns
    x_nodes = df[['x_type', 'x_name']].rename(columns={
        'x_type': 'TYPE', 
        'x_name': 'NAME'
    })
    
    y_nodes = df[['y_type', 'y_name']].rename(columns={
        'y_type': 'TYPE',
        'y_name': 'NAME'
    })
    
    # Combine and process nodes
    nodes_df = pd.concat([x_nodes, y_nodes], ignore_index=True).drop_duplicates()
    nodes_df = nodes_df.reset_index(drop=True)
    nodes_df['NODE_ID'] = 'n_' + nodes_df.index.astype(str)
    
    return nodes_df

def create_source_nodes(df: pd.DataFrame, properties_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create source nodes dataframe with properties.
    
    Args:
        df (pd.DataFrame): Input dataframe
        properties_df (pd.DataFrame): Properties dataframe
        
    Returns:
        pd.DataFrame: Source nodes dataframe with properties
    """
    # First create a mapping of source_secondary to es_id from properties
    source_mapping = {}
    if not properties_df.empty:
        for _, row in properties_df.iterrows():
            if pd.notna(row['source_secondary']):
                source_mapping[row['source_secondary']] = row['external_source_id']
    
    # Map source names to es_ids where possible
    source_ids = []
    for source in pd.concat([df['x_source'].dropna(), df['y_source'].dropna()]).unique():
        if str(source).startswith('es_'):
            source_ids.append(source)
        else:
            # If the source name exists in mapping, use the es_id
            source_ids.append(source_mapping.get(source, source))
    
    # Create base source nodes dataframe
    source_nodes = pd.DataFrame({
        'TYPE': 'source',
        'NAME': source_ids
    })
    
    # Initialize property columns
    property_columns = ['source_primary', 'source_secondary', 'source_link', 
                       'source_date', 'pubmed_id', 'country_of_origin']
    for col in property_columns:
        source_nodes[col] = None
    
    # Add properties for sources that have es_id
    if not properties_df.empty:
        # Merge with properties
        source_nodes = source_nodes.merge(
            properties_df,
            left_on='NAME',
            right_on='external_source_id',
            how='left'
        )
        
        # Update property columns from merged data
        for col in property_columns:
            mask = source_nodes['external_source_id'].notna()
            source_nodes.loc[mask, col] = source_nodes.loc[mask, col + '_y']
        
        # Clean up merged columns
        source_nodes = source_nodes.drop(columns=[col + '_y' for col in property_columns if col + '_y' in source_nodes.columns])
        source_nodes = source_nodes.drop(columns=[col + '_x' for col in property_columns if col + '_x' in source_nodes.columns])
        if 'external_source_id' in source_nodes.columns:
            source_nodes = source_nodes.drop(columns=['external_source_id'])
    
    # Add NODE_ID - keep es_ prefix for external sources
    source_nodes = source_nodes.reset_index(drop=True)
    source_nodes['NODE_ID'] = source_nodes.apply(
        lambda x: x['NAME'] if str(x['NAME']).startswith('es_') else 's_' + str(source_nodes.index[source_nodes['NAME'] == x['NAME']][0]),
        axis=1
    )
    
    return source_nodes

def process_nodes(nodes_df: pd.DataFrame, source_nodes: pd.DataFrame) -> pd.DataFrame:
    """
    Process and combine all nodes.
    
    Args:
        nodes_df (pd.DataFrame): Main nodes dataframe
        source_nodes (pd.DataFrame): Source nodes dataframe
        
    Returns:
        pd.DataFrame: Processed nodes dataframe
    """
    return pd.concat([nodes_df, source_nodes], ignore_index=True).drop_duplicates()

def create_relationships(df: pd.DataFrame, nodes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create relationships dataframe by joining nodes information.
    
    Args:
        df (pd.DataFrame): Original dataframe
        nodes_df (pd.DataFrame): Processed nodes dataframe
        
    Returns:
        pd.DataFrame: Relationships dataframe
    """
    # Join with x nodes
    df = df.merge(nodes_df, 
                 left_on=['x_type', 'x_name'],
                 right_on=['TYPE', 'NAME'],
                 how='left')
    df = df.rename(columns={'NODE_ID': 'START_ID'})

    # Join with y nodes
    df = df.merge(nodes_df,
                 left_on=['y_type', 'y_name'], 
                 right_on=['TYPE', 'NAME'],
                 how='left',
                 suffixes=('_x', '_y'))
    df = df.rename(columns={'NODE_ID': 'END_ID'})
    
    return df

def create_relations_dataframe(df: pd.DataFrame, nodes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create final relations dataframe with all relationship types.
    
    Args:
        df (pd.DataFrame): Processed dataframe with node IDs
        nodes_df (pd.DataFrame): Nodes dataframe
        
    Returns:
        pd.DataFrame: Final relations dataframe
    """
    # Get source nodes with their properties
    source_nodes = nodes_df[nodes_df['TYPE'] == 'source']
    
    # Create main relations
    relations = df[['START_ID', 'END_ID', 'relation']].dropna().rename(columns={'relation': 'TYPE'})
    
    # Create source relations
    source_relations = []
    for _, row in df.iterrows():
        if pd.notna(row['x_source']):
            source_id = row['x_source']
            if not str(source_id).startswith('es_'):
                # Try to find matching source node by source_secondary or NAME
                matching_sources = source_nodes[
                    (source_nodes['source_secondary'].notna() & (source_nodes['source_secondary'] == source_id)) |
                    (source_nodes['NAME'] == source_id)
                ]
                if not matching_sources.empty:
                    source_id = matching_sources.iloc[0]['NODE_ID']
                else:
                    # If no match found, this source needs to be added to source_nodes
                    new_idx = len(source_nodes)
                    source_id = f's_{new_idx}'
                    new_source = pd.DataFrame({
                        'TYPE': ['source'],
                        'NAME': [str(source_id)],
                        'NODE_ID': [source_id],
                        'source_secondary': [str(row['x_source'])]
                    })
                    source_nodes = pd.concat([source_nodes, new_source], ignore_index=True)
            source_relations.append({
                'START_ID': row['START_ID'],
                'END_ID': source_id,
                'TYPE': 'SOURCE'
            })
        if pd.notna(row['y_source']):
            source_id = row['y_source']
            if not str(source_id).startswith('es_'):
                # Try to find matching source node by source_secondary or NAME
                matching_sources = source_nodes[
                    (source_nodes['source_secondary'].notna() & (source_nodes['source_secondary'] == source_id)) |
                    (source_nodes['NAME'] == source_id)
                ]
                if not matching_sources.empty:
                    source_id = matching_sources.iloc[0]['NODE_ID']
                else:
                    # If no match found, this source needs to be added to source_nodes
                    new_idx = len(source_nodes)
                    source_id = f's_{new_idx}'
                    new_source = pd.DataFrame({
                        'TYPE': ['source'],
                        'NAME': [str(source_id)],
                        'NODE_ID': [source_id],
                        'source_secondary': [str(row['y_source'])]
                    })
                    source_nodes = pd.concat([source_nodes, new_source], ignore_index=True)
            source_relations.append({
                'START_ID': row['END_ID'],
                'END_ID': source_id,
                'TYPE': 'SOURCE'
            })
    
    # Update nodes_df with any new sources that were added
    nodes_df = process_nodes(nodes_df[nodes_df['TYPE'] != 'source'], source_nodes)
    
    # Combine all relations
    return pd.concat([
        relations,
        pd.DataFrame(source_relations)
    ], ignore_index=True)

def main():
    """Main function to process data and create Neo4j compatible CSV files."""
    start_time = time.time()
    
    # Select environment
    env = select_environment()
    output_dir = ensure_output_dir(env)
    
    # Load data
    print(f"Loading data files from {env} environment...")
    df = load_data_files(
        f'{env}/input/1_kg.csv',
        f'{env}/input/2_other_resources_triple.csv'
    )
    properties_df = load_properties(f'{env}/input/3_other_resources_property.csv')
    
    # Create nodes
    print("Creating nodes...")
    nodes_df = create_nodes_dataframe(df)
    source_nodes = create_source_nodes(df, properties_df)
    nodes_df = process_nodes(nodes_df, source_nodes)
    
    # Create relationships
    print("Creating relationships...")
    df = create_relationships(df, nodes_df)
    relations_df = create_relations_dataframe(df, nodes_df)
    
    # Save to CSV in the appropriate output directory
    print(f"Saving to CSV files in {output_dir}...")
    nodes_df.to_csv(f'{output_dir}/nodes.csv', index=False)
    relations_df.to_csv(f'{output_dir}/relationships.csv', index=False)
    
    # Copy and rename the properties file
    print("Copying properties file to output directory...")
    shutil.copy(
        f'{env}/input/3_other_resources_property.csv',
        f'{output_dir}/other_resources_property.csv'
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"\nExecution completed in {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()
