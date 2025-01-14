from neo4j import GraphDatabase
import time
from datetime import datetime
import os
import sys

# Add project root to Python path to import config
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)
from config import NEO4J_CONFIG

def print_execution_time(start_time, operation_name):
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"{operation_name} completed in {execution_time:.2f} seconds")

class Neo4jImporter:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def create_indexes(self):
        with self.driver.session() as session:
            try:
                # Drop any existing indexes first
                session.run("DROP INDEX source_nodeID IF EXISTS")
                session.run("DROP INDEX guideline_nodeID IF EXISTS")
                session.run("DROP INDEX concept_nodeID IF EXISTS")
                
                # Create fresh indexes with specific configurations for better performance
                session.run("CREATE INDEX source_nodeID FOR (n:source) ON (n.nodeID)")
                session.run("CREATE INDEX guideline_nodeID FOR (n:guideline) ON (n.nodeID)")
                session.run("CREATE INDEX concept_nodeID FOR (n:concept) ON (n.nodeID)")
            except Exception as e:
                print(f"Warning: Index operation failed - {str(e)}")

    def drop_indexes(self):
        with self.driver.session() as session:
            try:
                # Drop existing indexes if they exist
                session.run("DROP INDEX source_nodeID IF EXISTS")
                session.run("DROP INDEX guideline_nodeID IF EXISTS")
                session.run("DROP INDEX concept_nodeID IF EXISTS")
            except Exception as e:
                print(f"Warning: Index dropping failed - {str(e)}")

    def import_nodes(self, csv_file_path):
        with self.driver.session() as session:
            query = """
            CALL {
                LOAD CSV WITH HEADERS FROM 'file:///' + $file_path AS row
                CREATE (n)
                WITH n, row
                CALL apoc.create.addLabels(n, [row.TYPE]) YIELD node
                SET node.nodeID = row.NODE_ID,
                    node.name = row.NAME,
                    node.type = row.TYPE,
                    node.source_primary = CASE WHEN row.source_primary <> '' THEN row.source_primary ELSE null END,
                    node.source_secondary = CASE WHEN row.source_secondary <> '' THEN row.source_secondary ELSE null END,
                    node.title = CASE WHEN row.title <> '' THEN row.title ELSE null END,
                    node.source_link = CASE WHEN row.source_link <> '' THEN row.source_link ELSE null END,
                    node.source_date = CASE WHEN row.source_date <> '' THEN row.source_date ELSE null END,
                    node.pubmed_id = CASE WHEN row.pubmed_id <> '' THEN row.pubmed_id ELSE null END,
                    node.country_of_origin = CASE WHEN row.country_of_origin <> '' THEN row.country_of_origin ELSE null END
                RETURN count(*) as cnt
            } IN TRANSACTIONS OF 10000 ROWS
            RETURN sum(cnt)
            """
            session.run(query, file_path=csv_file_path)

    def import_relationships(self, csv_file_path):
        with self.driver.session() as session:
            query = """
            CALL {
                LOAD CSV WITH HEADERS FROM 'file:///' + $file_path AS row
                MATCH (source {nodeID: row.START_ID})
                MATCH (target {nodeID: row.END_ID})
                CALL apoc.create.relationship(source, row.TYPE, {}, target) YIELD rel
                RETURN count(*) as cnt
            } IN TRANSACTIONS OF 2000 ROWS
            RETURN sum(cnt) as total
            """
            session.run(query, file_path=csv_file_path)

    def import_external_source_properties(self, csv_file_path):
        with self.driver.session() as session:
            query = """
            CALL {
                LOAD CSV WITH HEADERS FROM 'file:///' + $file_path AS row
                MATCH (n {nodeID: row.external_source_id})
                SET n.name = row.title,
                    n.source_primary = row.source_primary,
                    n.source_secondary = row.source_secondary,
                    n.source_link = row.source_link,
                    n.source_date = row.source_date,
                    n.pubmed_id = CASE WHEN row.pubmed_id <> '' THEN row.pubmed_id ELSE null END,
                    n.country_of_origin = CASE WHEN row.country_of_origin <> '' THEN row.country_of_origin ELSE null END
                RETURN count(*) as cnt
            } IN TRANSACTIONS OF 5000 ROWS
            RETURN sum(cnt)
            """
            session.run(query, file_path=csv_file_path)

    def delete_all_data(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

# Usage example
start_total = time.time()
print(f"\nStarting import process at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

importer = Neo4jImporter(
    NEO4J_CONFIG["URI"],
    NEO4J_CONFIG["USER"],
    NEO4J_CONFIG["PASSWORD"]
)

try:
    # Delete all data and prepare database
    start_time = time.time()
    importer.delete_all_data()
    importer.drop_indexes()
    print_execution_time(start_time, "Deleting all data")

    # Create indexes before import
    start_time = time.time()
    importer.create_indexes()
    print_execution_time(start_time, "Creating indexes")

    # Import nodes
    start_time = time.time()
    importer.import_nodes("nodes.csv")
    print_execution_time(start_time, "Importing nodes")

    # Import relationships
    start_time = time.time()
    importer.import_relationships("relationships.csv")
    print_execution_time(start_time, "Importing relationships")

    # Import external source properties
    start_time = time.time()
    importer.import_external_source_properties("other_resources_property.csv")
    print_execution_time(start_time, "Importing external source properties")

    print_execution_time(start_total, "\nTotal execution time")
finally:
    importer.close()
