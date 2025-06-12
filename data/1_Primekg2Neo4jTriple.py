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
    cochrane_df = pd.read_csv(f'{env}/input/2_cochranelibrary_triple.csv')
    
    # Load property files
    other_properties_df = pd.read_csv(f'{env}/input/3_other_resources_property.csv')
    cochrane_properties_df = pd.read_csv(f'{env}/input/3_cochranelibrary_property.csv')
    
    # Combine data
    combined_df = pd.concat([primekg_df, other_resources_df, cochrane_df], ignore_index=True)
    properties_df = pd.concat([other_properties_df, cochrane_properties_df], ignore_index=True)
    
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
    
    # Process source nodes from properties file
    source_nodes = []
    processed_sources = set()
    name_to_id_map = {}  # Map to track source names to their IDs
    
    # Process guideline and other sources from properties file first
    for _, row in properties_df.iterrows():
        source_id = row['external_source_id']
        if pd.isna(source_id):
            continue
        source_id = str(source_id)
        if source_id in processed_sources:
            continue
        
        # For Cochrane Library sources, use the original ID
        if row['source_primary'] == 'Cochrane Library':
            node_id = source_id
        else:
            # For other sources, keep using the es_ prefix
            node_id = source_id if source_id.startswith('es_') else f'es_{len(processed_sources) + 1}'
        
        source_name = row['source_secondary']
        name_to_id_map[str(source_name).lower()] = node_id
        
        source_nodes.append({
            'TYPE': 'source',
            'NAME': source_name,
            'NODE_ID': node_id,
            'source_primary': row['source_primary'],
            'source_secondary': source_name,
            'title': row['title'],
            'source_link': row['source_link'],
            'source_date': row['source_date'],
            'pubmed_id': str(row['pubmed_id']) if pd.notna(row['pubmed_id']) else '',
            'country_of_origin': str(row['country_of_origin']) if pd.notna(row['country_of_origin']) else ''
        })
        processed_sources.add(source_id)
    
    # Add PrimeKG source nodes
    primekg_sources = pd.concat([
        df[['x_source']].rename(columns={'x_source': 'source'}),
        df[['y_source']].rename(columns={'y_source': 'source'})
    ])['source'].unique()
    
    kg_source_counter = 0
    for source_str in primekg_sources:
        if pd.isna(source_str):
            continue
        source_str = str(source_str).strip()
        source_lower = source_str.lower()
        
        # Skip if we've already processed this source
        if source_lower in name_to_id_map or source_str in processed_sources:
            continue
            
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
        name_to_id_map[source_lower] = f's_{kg_source_counter}'
        processed_sources.add(source_str)
        kg_source_counter += 1
    
    # Create source nodes dataframe
    source_df = pd.DataFrame(source_nodes)
    
    # Combine all nodes
    final_nodes_df = pd.concat([nodes_df, source_df], ignore_index=True)
    
    # Ensure proper column order
    columns = ['TYPE', 'NAME', 'NODE_ID'] + property_cols
    final_nodes_df = final_nodes_df[columns]
    
    return final_nodes_df

def create_relationships(df: pd.DataFrame, nodes_df: pd.DataFrame, properties_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create relationships dataframe with proper source handling, and include is_effective as a property.
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
    
    # Add main relationships，包含 is_effective
    if 'relation_name' in df.columns:
        main_rels = df[['START_ID', 'END_ID', 'relation', 'relation_name']].dropna(subset=['START_ID', 'END_ID', 'relation'])
        main_rels = main_rels.rename(columns={'relation': 'TYPE', 'relation_name': 'is_effective'})
        # 將 is_effective 轉為 int，無法轉換時設為 None
        main_rels['is_effective'] = pd.to_numeric(main_rels['is_effective'], errors='coerce').astype('Int64')
    else:
        main_rels = df[['START_ID', 'END_ID', 'relation']].dropna(subset=['START_ID', 'END_ID', 'relation'])
        main_rels['is_effective'] = pd.NA
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
                'TYPE': 'SOURCE',
                'is_effective': pd.NA
            })
        
        if pd.notna(row['y_external_source_id']):
            source_rels.append({
                'START_ID': row['END_ID'],
                'END_ID': row['y_external_source_id'],
                'TYPE': 'SOURCE',
                'is_effective': pd.NA
            })
        
        # Handle regular sources and PrimeKG sources
        for source_type, node_id in [('x_source', 'START_ID'), ('y_source', 'END_ID')]:
            if pd.notna(row[source_type]):
                source_str = str(row[source_type]).strip()
                source_lower = source_str.lower()
                
                # Try to find the source node ID
                source_node = nodes_df[
                    (nodes_df['TYPE'] == 'source') & 
                    ((nodes_df['NAME'] == source_str) | 
                     (nodes_df['source_secondary'] == source_str))
                ]
                
                if not source_node.empty:
                    source_id = source_node.iloc[0]['NODE_ID']
                    source_rels.append({
                        'START_ID': row[node_id],
                        'END_ID': source_id,
                        'TYPE': 'SOURCE',
                        'is_effective': pd.NA
                    })
    
    # Add source relationships
    if source_rels:
        relationships.append(pd.DataFrame(source_rels))
    
    # Combine all relationships
    final_rels_df = pd.concat(relationships, ignore_index=True)
    # 確保 is_effective 欄位存在且型態為 Int64
    if 'is_effective' not in final_rels_df.columns:
        final_rels_df['is_effective'] = pd.NA
    final_rels_df['is_effective'] = final_rels_df['is_effective'].astype('Int64')
    # Remove duplicates and ensure proper column order
    final_rels_df = final_rels_df[['START_ID', 'END_ID', 'TYPE', 'is_effective']].drop_duplicates()
    
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
    
    # Combine and save property files
    print("Combining and saving property files...")
    combined_properties = pd.concat([
        pd.read_csv(f'{env}/input/3_other_resources_property.csv'),
        pd.read_csv(f'{env}/input/3_cochranelibrary_property.csv')
    ], ignore_index=True)
    combined_properties.to_csv(f'{output_dir}/other_resources_property.csv', index=False)
    
    print("Conversion completed successfully!")

if __name__ == "__main__":
    main() 