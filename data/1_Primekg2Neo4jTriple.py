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
        pd.DataFrame: Combined nodes dataframe with TYPE, NAME, NODE_ID columns
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
    nodes_df = nodes_df.reset_index()
    nodes_df['NODE_ID'] = 'n_' + (nodes_df.index + 1).astype(str)  # Start from n_1
    nodes_df = nodes_df[['TYPE', 'NAME', 'NODE_ID']]  # Reorder columns
    
    return nodes_df

def create_source_nodes(df: pd.DataFrame, properties_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create source nodes dataframe with properties.
    
    Args:
        df (pd.DataFrame): Input dataframe
        properties_df (pd.DataFrame): Properties dataframe
        
    Returns:
        pd.DataFrame: Source nodes dataframe with TYPE, NAME, NODE_ID and additional properties
    """
    # Get unique external source IDs
    external_sources = pd.concat([
        df['x_external_source_id'].dropna(),
        df['y_external_source_id'].dropna()
    ]).unique()
    
    # Get unique knowledge graph sources
    kg_sources = pd.concat([
        df['x_source'].dropna(),
        df['y_source'].dropna()
    ]).unique()
    
    # Create source nodes dataframe for external sources with properties
    external_source_nodes = pd.DataFrame({
        'TYPE': 'source',
        'NAME': external_sources,
        'NODE_ID': ['es_' + str(id).replace('es_', '') for id in external_sources]  # Remove any existing es_ prefix
    })
    
    # Add properties from properties_df for external sources
    properties_df['external_source_id'] = 'es_' + properties_df['external_source_id'].astype(str)
    external_source_nodes = external_source_nodes.merge(
        properties_df,
        left_on='NODE_ID',
        right_on='external_source_id',
        how='left'
    ).drop('external_source_id', axis=1)
    
    # Create source nodes dataframe for knowledge graph sources with properties
    kg_source_nodes_list = []
    for i, source in enumerate(kg_sources, 1):
        # Create a dictionary with all properties
        source_dict = {
            'TYPE': 'source',
            'NAME': source,
            'NODE_ID': f's_{i}',
            'source_primary': 'PrimeKG',
            'source_secondary': source,
            'title': '',  # Empty string instead of None
            'source_link': '',  # Empty string instead of None
            'source_date': '',  # Empty string instead of None
            'pubmed_id': '',  # Empty string instead of None
            'country_of_origin': ''  # Empty string instead of None
        }
        kg_source_nodes_list.append(source_dict)
    
    kg_source_nodes = pd.DataFrame(kg_source_nodes_list)
    
    # Combine all source nodes and ensure column order
    source_nodes = pd.concat([external_source_nodes, kg_source_nodes], ignore_index=True)
    
    # Ensure TYPE, NAME, NODE_ID are first columns, followed by properties in a specific order
    property_cols = ['source_primary', 'source_secondary', 'title', 'source_link', 'source_date', 'pubmed_id', 'country_of_origin']
    source_nodes = source_nodes[['TYPE', 'NAME', 'NODE_ID'] + property_cols]
    
    # Replace NaN and None values with empty strings
    source_nodes = source_nodes.fillna('')
    
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

def create_relations_dataframe(df: pd.DataFrame, nodes_df: pd.DataFrame, properties_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create final relations dataframe with all relationship types.
    
    Args:
        df (pd.DataFrame): Processed dataframe with node IDs
        nodes_df (pd.DataFrame): Nodes dataframe
        properties_df (pd.DataFrame): Properties dataframe with source information
        
    Returns:
        pd.DataFrame: Final relations dataframe with START_ID, END_ID, TYPE columns
    """
    # Get source nodes mapping for knowledge graph sources
    kg_source_mapping = nodes_df[nodes_df['TYPE'] == 'source'].set_index('NAME')['NODE_ID'].to_dict()
    
    # Create main relations
    relations = df[['START_ID', 'END_ID', 'relation']].dropna().rename(columns={'relation': 'TYPE'})
    
    # Create source relations
    source_relations = []
    for _, row in df.iterrows():
        # Handle external source IDs
        if pd.notna(row['x_external_source_id']):
            source_id = 'es_' + str(row['x_external_source_id'])
            source_relations.append({
                'START_ID': row['START_ID'],
                'END_ID': source_id,
                'TYPE': 'SOURCE'
            })
        if pd.notna(row['y_external_source_id']):
            source_id = 'es_' + str(row['y_external_source_id'])
            source_relations.append({
                'START_ID': row['END_ID'],
                'END_ID': source_id,
                'TYPE': 'SOURCE'
            })
            
        # Handle x_source and y_source using the mapping
        if pd.notna(row['x_source']) and row['x_source'] in kg_source_mapping:
            source_relations.append({
                'START_ID': row['START_ID'],
                'END_ID': kg_source_mapping[row['x_source']],
                'TYPE': 'SOURCE'
            })
        if pd.notna(row['y_source']) and row['y_source'] in kg_source_mapping:
            source_relations.append({
                'START_ID': row['END_ID'],
                'END_ID': kg_source_mapping[row['y_source']],
                'TYPE': 'SOURCE'
            })
    
    # Combine all relations and ensure column order
    relations_df = pd.concat([
        relations,
        pd.DataFrame(source_relations)
    ], ignore_index=True)
    relations_df = relations_df[['START_ID', 'END_ID', 'TYPE']]
    
    return relations_df

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
    relations_df = create_relations_dataframe(df, nodes_df, properties_df)
    
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
