import pandas as pd
import os
import shutil
from typing import Dict, List, Tuple

def select_environment() -> str:
    """Select environment (dev/prod)."""
    while True:
        env = input("Select environment (dev/prod) [default: dev]: ").lower().strip()
        if env == '':
            return 'dev'
        if env in ['dev', 'prod']:
            return env
        print("Invalid environment. Please enter 'dev' or 'prod'")

def ensure_output_dir(env: str) -> str:
    """Create output directory if it doesn't exist."""
    output_dir = f"{env}/output"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def load_data(env: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load input data files.
    
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (combined_df, properties_df)
    """
    # Load main data files
    primekg_df = pd.read_csv(f'{env}/input/1_kg.csv')
    other_resources_df = pd.read_csv(f'{env}/input/2_other_resources_triple.csv')
    properties_df = pd.read_csv(f'{env}/input/3_other_resources_property.csv')
    
    # Combine data
    combined_df = pd.concat([primekg_df, other_resources_df], ignore_index=True)
    
    return combined_df, properties_df

def create_source_mapping(properties_df: pd.DataFrame) -> Dict[str, str]:
    """
    Create mapping of source names to their external source IDs.
    """
    mapping = {}
    
    for _, row in properties_df.iterrows():
        source_id = row['external_source_id']
        
        # Map all possible names from properties
        for field in ['source_primary', 'source_secondary', 'title']:
            if pd.notna(row[field]):
                name = str(row[field]).strip()
                mapping[name] = source_id
                mapping[name.lower()] = source_id
        
        # Map the ID itself
        mapping[source_id] = source_id
    
    return mapping

def create_nodes(df: pd.DataFrame, properties_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create nodes dataframe with proper handling of source IDs.
    """
    # Extract all non-source nodes first
    x_nodes = df[['x_type', 'x_name']].rename(columns={'x_type': 'TYPE', 'x_name': 'NAME'})
    y_nodes = df[['y_type', 'y_name']].rename(columns={'y_type': 'TYPE', 'y_name': 'NAME'})
    
    # Combine and remove duplicates
    nodes_df = pd.concat([x_nodes, y_nodes], ignore_index=True)
    nodes_df = nodes_df[nodes_df['TYPE'] != 'source'].drop_duplicates()
    
    # Add node IDs
    nodes_df['NODE_ID'] = 'n_' + nodes_df.index.astype(str)
    
    # Add empty property columns
    property_cols = ['source_primary', 'source_secondary', 'title', 
                    'source_link', 'source_date', 'pubmed_id', 'country_of_origin']
    for col in property_cols:
        nodes_df[col] = ''
    
    # Create comprehensive source mapping
    source_mapping = {}  # Maps any source identifier to its external source ID
    source_properties = {}  # Maps external source IDs to their properties
    
    # First, process properties file to build mappings
    for _, row in properties_df.iterrows():
        source_id = row['external_source_id']
        # Store properties
        source_properties[source_id] = row.to_dict()
        
        # Map all possible identifiers to this source ID
        source_mapping[source_id] = source_id  # Map ID to itself
        
        # Map all variations of source names
        for field in ['source_primary', 'source_secondary', 'title']:
            if pd.notna(row[field]):
                name = str(row[field]).strip()
                source_mapping[name] = source_id
                source_mapping[name.lower()] = source_id
                # Also map without spaces and special characters
                cleaned_name = ''.join(c.lower() for c in name if c.isalnum())
                source_mapping[cleaned_name] = source_id
    
    # Get all unique sources
    all_sources = pd.concat([
        df['x_external_source_id'].dropna(),
        df['y_external_source_id'].dropna(),
        df['x_source'].dropna(),
        df['y_source'].dropna()
    ]).unique()
    
    # Process sources and create nodes
    source_nodes = []
    kg_source_counter = 0
    processed_sources = set()  # Track which sources we've already processed
    
    # First pass: Process all external sources
    for source in all_sources:
        source_str = str(source).strip()
        source_lower = source_str.lower()
        cleaned_source = ''.join(c.lower() for c in source_str if c.isalnum())
        
        # Skip if we've already processed this source
        if source_str in processed_sources or source_lower in processed_sources:
            continue
        
        # Check if this is an external source
        external_id = None
        if source_str.startswith('es_'):
            external_id = source_str
        else:
            # Try all possible variations of the name
            external_id = (source_mapping.get(source_str) or 
                         source_mapping.get(source_lower) or 
                         source_mapping.get(cleaned_source))
        
        if external_id:
            # Use external source properties
            props = source_properties[external_id]
            source_nodes.append({
                'TYPE': 'source',
                'NAME': props['source_secondary'],  # Use canonical name from properties
                'NODE_ID': external_id,
                'source_primary': props['source_primary'],
                'source_secondary': props['source_secondary'],
                'title': props['title'],
                'source_link': props['source_link'],
                'source_date': props['source_date'],
                'pubmed_id': props['pubmed_id'],
                'country_of_origin': props['country_of_origin']
            })
            # Add all variations of this source name to processed set
            processed_sources.add(props['source_secondary'])
            processed_sources.add(props['source_secondary'].lower())
            if pd.notna(props['title']):
                processed_sources.add(props['title'])
                processed_sources.add(props['title'].lower())
            processed_sources.add(source_str)
            processed_sources.add(source_lower)
            processed_sources.add(cleaned_source)
    
    # Second pass: Process remaining sources as PrimeKG sources
    for source in all_sources:
        source_str = str(source).strip()
        source_lower = source_str.lower()
        cleaned_source = ''.join(c.lower() for c in source_str if c.isalnum())
        
        # Skip if we've already processed this source
        if (source_str in processed_sources or 
            source_lower in processed_sources or 
            cleaned_source in processed_sources):
            continue
        
        # Create PrimeKG source node
        source_nodes.append({
            'TYPE': 'source',
            'NAME': source_str,
            'NODE_ID': f's_{kg_source_counter}',
            'source_primary': 'PrimeKG',
            'source_secondary': source_str,
            'title': '',
            'source_link': '',
            'source_date': '',
            'pubmed_id': '',
            'country_of_origin': ''
        })
        processed_sources.add(source_str)
        processed_sources.add(source_lower)
        processed_sources.add(cleaned_source)
        kg_source_counter += 1
    
    # Combine all nodes
    source_df = pd.DataFrame(source_nodes)
    final_nodes_df = pd.concat([nodes_df, source_df], ignore_index=True)
    
    # Ensure proper column order
    columns = ['TYPE', 'NAME', 'NODE_ID'] + property_cols
    final_nodes_df = final_nodes_df[columns]
    
    return final_nodes_df

def create_relationships(df: pd.DataFrame, nodes_df: pd.DataFrame, properties_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create relationships dataframe with proper source handling.
    """
    # Create main relationships
    df = df.merge(
        nodes_df[['TYPE', 'NAME', 'NODE_ID']],
        left_on=['x_type', 'x_name'],
        right_on=['TYPE', 'NAME'],
        how='left'
    ).rename(columns={'NODE_ID': 'START_ID'})
    
    df = df.merge(
        nodes_df[['TYPE', 'NAME', 'NODE_ID']],
        left_on=['y_type', 'y_name'],
        right_on=['TYPE', 'NAME'],
        how='left',
        suffixes=('_x', '_y')
    ).rename(columns={'NODE_ID': 'END_ID'})
    
    # Get source mappings
    source_mapping = create_source_mapping(properties_df)
    node_mapping = nodes_df[nodes_df['TYPE'] == 'source'].set_index('NAME')['NODE_ID'].to_dict()
    
    # Create relationships list
    relationships = []
    
    # Add main relationships
    main_rels = df[['START_ID', 'END_ID', 'relation']].dropna()
    main_rels = main_rels.rename(columns={'relation': 'TYPE'})
    relationships.append(main_rels)
    
    # Create source relationships
    source_rels = []
    
    for _, row in df.iterrows():
        # Handle external source IDs
        if pd.notna(row['x_external_source_id']):
            source_rels.append({
                'START_ID': row['START_ID'],
                'END_ID': row['x_external_source_id'],
                'TYPE': 'SOURCE'
            })
        
        if pd.notna(row['y_external_source_id']):
            source_rels.append({
                'START_ID': row['END_ID'],
                'END_ID': row['y_external_source_id'],
                'TYPE': 'SOURCE'
            })
        
        # Handle regular sources
        for source_type, node_id in [('x_source', 'START_ID'), ('y_source', 'END_ID')]:
            if pd.notna(row[source_type]):
                source_str = str(row[source_type]).strip()
                source_lower = source_str.lower()
                
                # Try to find the correct source ID
                source_id = (source_mapping.get(source_str) or 
                           source_mapping.get(source_lower) or 
                           node_mapping.get(source_str))
                
                if source_id:
                    source_rels.append({
                        'START_ID': row[node_id],
                        'END_ID': source_id,
                        'TYPE': 'SOURCE'
                    })
    
    # Add source relationships
    if source_rels:
        relationships.append(pd.DataFrame(source_rels))
    
    # Combine all relationships
    final_rels_df = pd.concat(relationships, ignore_index=True)
    
    # Remove duplicates and ensure proper column order
    final_rels_df = final_rels_df[['START_ID', 'END_ID', 'TYPE']].drop_duplicates()
    
    return final_rels_df

def main():
    """Main function to convert data to Neo4j format."""
    print("Starting conversion process...")
    
    # Select environment
    env = select_environment()
    output_dir = ensure_output_dir(env)
    
    # Load data
    print(f"Loading data from {env} environment...")
    df, properties_df = load_data(env)
    
    # Create nodes
    print("Creating nodes...")
    nodes_df = create_nodes(df, properties_df)
    
    # Create relationships
    print("Creating relationships...")
    relationships_df = create_relationships(df, nodes_df, properties_df)
    
    # Save results
    print(f"Saving results to {output_dir}...")
    nodes_df.to_csv(f'{output_dir}/nodes.csv', index=False)
    relationships_df.to_csv(f'{output_dir}/relationships.csv', index=False)
    
    # Copy properties file
    shutil.copy(
        f'{env}/input/3_other_resources_property.csv',
        f'{output_dir}/other_resources_property.csv'
    )
    
    print("Conversion completed successfully!")

if __name__ == "__main__":
    main() 