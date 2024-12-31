import pandas as pd

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load data from CSV file with specified data types.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: Loaded dataframe
    """
    return pd.read_csv(file_path, dtype={
        'relation': str, 'display_relation': str, 'x_index': str, 'x_id': str,
        'x_type': str, 'x_name': str, 'x_source': str, 'y_index': str,
        'y_id': str, 'y_type': str, 'y_name': str, 'y_source': str,
        'source_type': str, 'source_link': str, 'source_date': str
    })

def create_nodes_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create nodes dataframe from input dataframe's x and y columns.
    
    Args:
        df (pd.DataFrame): Input dataframe containing x and y node information
        
    Returns:
        pd.DataFrame: Combined nodes dataframe
    """
    # Create nodes dataframe from x and y columns
    x_nodes = df[['x_type', 'x_name']].rename(columns={
        'x_type': 'type', 
        'x_name': 'name'
    })
    
    y_nodes = df[['y_type', 'y_name']].rename(columns={
        'y_type': 'type',
        'y_name': 'name'
    })
    
    # Combine and process nodes
    nodes_df = pd.concat([x_nodes, y_nodes], ignore_index=True).drop_duplicates()
    nodes_df = nodes_df.reset_index(drop=True).reset_index()
    nodes_df['index'] = 'n_' + nodes_df['index'].astype(str)
    
    return nodes_df

def create_source_nodes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create source nodes dataframe from unique sources in the input dataframe.
    
    Args:
        df (pd.DataFrame): Input dataframe containing source information
        
    Returns:
        pd.DataFrame: Source nodes dataframe
    """
    source_nodes = pd.concat([
        pd.DataFrame({
            'type': 'source',
            'name': df['x_source'].dropna().unique()
        }),
        pd.DataFrame({
            'type': 'source', 
            'name': df['y_source'].dropna().unique()
        })
    ]).drop_duplicates()
    
    source_nodes = source_nodes.reset_index(drop=True).reset_index()
    source_nodes['index'] = 's_' + source_nodes['index'].astype(str)
    
    return source_nodes

def process_nodes(nodes_df: pd.DataFrame, source_nodes: pd.DataFrame) -> pd.DataFrame:
    """
    Process and combine all nodes, adding nodeID.
    
    Args:
        nodes_df (pd.DataFrame): Main nodes dataframe
        source_nodes (pd.DataFrame): Source nodes dataframe
        
    Returns:
        pd.DataFrame: Processed nodes dataframe
    """
    # Combine all nodes
    nodes_df = pd.concat([nodes_df, source_nodes], ignore_index=True).drop_duplicates()
    
    # Add nodeID
    nodes_df = (nodes_df
                .reset_index(drop=True)
                .reset_index()
                .rename(columns={'index': 'nodeID'}))
    
    return nodes_df

def create_relationships(df: pd.DataFrame, nodes_df: pd.DataFrame, source_nodes: pd.DataFrame) -> pd.DataFrame:
    """
    Create relationships dataframe by joining nodes information.
    
    Args:
        df (pd.DataFrame): Original dataframe
        nodes_df (pd.DataFrame): Processed nodes dataframe
        source_nodes (pd.DataFrame): Source nodes dataframe
        
    Returns:
        pd.DataFrame: Relationships dataframe
    """
    # Join with x nodes
    df = df.merge(nodes_df, 
                 left_on=['x_type', 'x_name'],
                 right_on=['type', 'name'],
                 how='left')
    df = df.rename(columns={'nodeID': ':START_ID'})

    # Join with y nodes
    df = df.merge(nodes_df,
                 left_on=['y_type', 'y_name'], 
                 right_on=['type', 'name'],
                 how='left',
                 suffixes=('_x', '_y'))
    df = df.rename(columns={'nodeID': ':END_ID'})

    # Join with source nodes for x_source
    df = df.merge(source_nodes,
                 left_on='x_source',
                 right_on='name',
                 how='left',
                 suffixes=('', '_source'))
    df = df.rename(columns={'index': 'source_id_x'})

    # Join with source nodes for y_source
    df = df.merge(source_nodes,
                 left_on='y_source', 
                 right_on='name',
                 how='left',
                 suffixes=('', '_source_y'))
    df = df.rename(columns={'index': 'source_id_y'})
    
    return df

def create_relations_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create final relations dataframe with all relationship types.
    
    Args:
        df (pd.DataFrame): Processed dataframe with node IDs
        
    Returns:
        pd.DataFrame: Final relations dataframe
    """
    return pd.concat([
        df[[':START_ID', ':END_ID', 'relation']].dropna().rename(columns={'relation': ':TYPE'}),
        df[[':START_ID', 'source_id_x']].dropna().rename(columns={'source_id_x': ':END_ID'}).assign(**{':TYPE': 'SOURCE'}),
        df[[':END_ID', 'source_id_y']].dropna().rename(columns={':END_ID':':START_ID', 'source_id_y': ':END_ID'}).assign(**{':TYPE': 'SOURCE'})
    ], axis=0)

def main():
    """Main function to process data and create Neo4j compatible CSV files."""
    # Load data
    df = load_data('Alzheimer_and_guideline.csv')
    
    # Create nodes
    nodes_df = create_nodes_dataframe(df)
    source_nodes = create_source_nodes(df)
    nodes_df = process_nodes(nodes_df, source_nodes)
    
    # Create relationships
    df = create_relationships(df, nodes_df, source_nodes)
    relations_df = create_relations_dataframe(df)
    
    # Save to CSV
    nodes_df.to_csv('nodes_test.csv', index=False)
    relations_df.to_csv('relations_test.csv', index=False)

if __name__ == "__main__":
    main()