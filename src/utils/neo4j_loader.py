from neo4j import GraphDatabase
import pandas as pd
import streamlit as st

class Neo4jLoader:
    def __init__(self, uri, username, password):
        """Initialize Neo4j connection
        
        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        
    def close(self):
        """Close the Neo4j connection"""
        self.driver.close()
        
    def fetch_nodes(self):
        """Fetch all nodes from Neo4j
        
        Returns:
            pd.DataFrame: DataFrame containing nodes with their properties
        """
        with self.driver.session() as session:
            query = """
            MATCH (n)
            RETURN 
                n.nodeID as node_id,
                CASE 
                    WHEN any(x IN labels(n) WHERE x IN ['Source', 'source']) THEN 'source'
                    ELSE labels(n)[0]
                END as type,
                n.name as name,
                n.source_primary as source_primary,
                n.source_secondary as source_secondary,
                n.source_link as source_link,
                n.source_date as source_date,
                n.pubmed_id as pubmed_id,
                n.country_of_origin as country_of_origin
            """
            result = session.run(query)
            records = [record for record in result]
            
            if not records:
                return pd.DataFrame(columns=['node_id', 'type', 'name', 'source_type'])
                
            df = pd.DataFrame([dict(record) for record in records])
            return df
            
    def fetch_relationships(self):
        """Fetch all relationships from Neo4j
        
        Returns:
            pd.DataFrame: DataFrame containing relationships
        """
        with self.driver.session() as session:
            query = """
            MATCH (a)-[r]->(b)
            RETURN 
                a.nodeID as subject,
                type(r) as predicate,
                b.nodeID as object
            """
            result = session.run(query)
            records = [record for record in result]
            
            if not records:
                return pd.DataFrame(columns=['subject', 'predicate', 'object'])
                
            df = pd.DataFrame([dict(record) for record in records])
            return df

@st.cache_resource
def get_neo4j_loader():
    """Get Neo4j loader instance
    
    Returns:
        Neo4jLoader: Neo4j loader instance
    """
    # Get connection settings from session state
    uri = st.session_state.get('neo4j_uri', 'neo4j://localhost:7687')
    username = st.session_state.get('neo4j_user', 'neo4j')
    password = st.session_state.get('neo4j_password', 'alex12345')
    
    return Neo4jLoader(uri, username, password)

@st.cache_data
def load_data_from_neo4j():
    """Load graph data from Neo4j
    
    Returns:
        tuple: (nodes_df, relationships_df) Neo4j format node and relationship DataFrames
    """
    try:
        loader = get_neo4j_loader()
        
        # Fetch data
        nodes_df = loader.fetch_nodes()
        relationships_df = loader.fetch_relationships()
        
        # Validate data format
        if nodes_df.empty or relationships_df.empty:
            st.error("No data found in Neo4j database")
            return None, None
            
        required_node_columns = {'node_id', 'type', 'name', 'source_primary', 'source_secondary'}
        missing_node_columns = required_node_columns - set(nodes_df.columns)
        if missing_node_columns:
            st.error(f"Missing required node columns: {', '.join(missing_node_columns)}")
            return None, None
            
        required_rel_columns = {'subject', 'predicate', 'object'}
        missing_rel_columns = required_rel_columns - set(relationships_df.columns)
        if missing_rel_columns:
            st.error(f"Missing required relationship columns: {', '.join(missing_rel_columns)}")
            return None, None
            
        return nodes_df, relationships_df
        
    except Exception as e:
        st.error(f"Error loading data from Neo4j: {str(e)}")
        return None, None 