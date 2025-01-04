import pandas as pd
from typing import Dict, List
import time

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
    # Get unique source IDs from x_source and y_source
    source_ids = pd.concat([
        df['x_source'].dropna(),
        df['y_source'].dropna()
    ]).unique()
    
    # Create base source nodes dataframe
    source_nodes = pd.DataFrame({
        'TYPE': 'source',
        'NAME': source_ids
    })
    
    # Add NODE_ID
    source_nodes = source_nodes.reset_index(drop=True)
    source_nodes['NODE_ID'] = 's_' + source_nodes.index.astype(str)
    
    # Add properties for sources that have es_id
    es_sources = source_nodes[source_nodes['NAME'].str.startswith('es_', na=False)].copy()
    if not es_sources.empty:
        # Merge with properties
        es_sources = es_sources.merge(
            properties_df,
            left_on='NAME',
            right_on='external_source_id',
            how='left'
        )
        
        # Update original source_nodes with properties
        property_columns = ['source_primary', 'source_secondary', 'source_link', 
                          'source_date', 'pubmed_id', 'country_of_origin']
        for col in property_columns:
            source_nodes[col] = None
            source_nodes.loc[source_nodes['NAME'].str.startswith('es_', na=False), col] = es_sources[col]
    
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
    # Get source nodes
    source_nodes = nodes_df[nodes_df['TYPE'] == 'source']
    
    # Create main relations
    relations = df[['START_ID', 'END_ID', 'relation']].dropna().rename(columns={'relation': 'TYPE'})
    
    # Create source relations
    source_relations = []
    for _, row in df.iterrows():
        if pd.notna(row['x_source']):
            source_node = source_nodes[source_nodes['NAME'] == row['x_source']].iloc[0]
            source_relations.append({
                'START_ID': row['START_ID'],
                'END_ID': source_node['NODE_ID'],
                'TYPE': 'SOURCE'
            })
        if pd.notna(row['y_source']):
            source_node = source_nodes[source_nodes['NAME'] == row['y_source']].iloc[0]
            source_relations.append({
                'START_ID': row['END_ID'],
                'END_ID': source_node['NODE_ID'],
                'TYPE': 'SOURCE'
            })
    
    # Combine all relations
    return pd.concat([
        relations,
        pd.DataFrame(source_relations)
    ], ignore_index=True)

def main():
    """Main function to process data and create Neo4j compatible CSV files."""
    start_time = time.time()
    
    # Load data
    print("Loading data files...")
    df = load_data_files('1_primekg_Alzheimer.csv', '2_other_resources_triple.csv')
    properties_df = load_properties('3_other_resources_property.csv')
    
    # Create nodes
    print("Creating nodes...")
    nodes_df = create_nodes_dataframe(df)
    source_nodes = create_source_nodes(df, properties_df)
    nodes_df = process_nodes(nodes_df, source_nodes)
    
    # Create relationships
    print("Creating relationships...")
    df = create_relationships(df, nodes_df)
    relations_df = create_relations_dataframe(df, nodes_df)
    
    # Save to CSV
    print("Saving to CSV files...")
    nodes_df.to_csv('nodes.csv', index=False)
    relations_df.to_csv('relationships.csv', index=False)
    
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"\nExecution completed in {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()
