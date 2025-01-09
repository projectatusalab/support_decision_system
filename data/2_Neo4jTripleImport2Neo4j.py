from neo4j import GraphDatabase
import time
from datetime import datetime

def print_execution_time(start_time, operation_name):
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"{operation_name} completed in {execution_time:.2f} seconds")

class Neo4jImporter:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def import_nodes(self, csv_file_path):
        with self.driver.session() as session:
            # Use built-in LOAD CSV instead of APOC
            query = """
            LOAD CSV WITH HEADERS FROM 'file:///' + $file_path AS row
            CALL apoc.create.node([row.TYPE], {
                nodeID: row.NODE_ID,
                name: CASE 
                    WHEN row.TYPE = 'source' AND row.NODE_ID STARTS WITH 'es_' THEN null 
                    ELSE row.NAME 
                END,
                source_primary: CASE 
                    WHEN row.TYPE = 'source' THEN row.source_primary 
                    ELSE null 
                END,
                source_secondary: CASE 
                    WHEN row.TYPE = 'source' THEN row.source_secondary 
                    ELSE null 
                END,
                title: CASE 
                    WHEN row.TYPE = 'source' AND row.title <> '' THEN row.title 
                    ELSE null 
                END,
                source_link: CASE 
                    WHEN row.TYPE = 'source' AND row.source_link <> '' THEN row.source_link 
                    ELSE null 
                END,
                source_date: CASE 
                    WHEN row.TYPE = 'source' AND row.source_date <> '' THEN row.source_date 
                    ELSE null 
                END,
                pubmed_id: CASE 
                    WHEN row.TYPE = 'source' AND row.pubmed_id <> '' THEN row.pubmed_id 
                    ELSE null 
                END,
                country_of_origin: CASE 
                    WHEN row.TYPE = 'source' AND row.country_of_origin <> '' THEN row.country_of_origin 
                    ELSE null 
                END
            }) YIELD node
            RETURN node
            """
            session.run(query, file_path=csv_file_path)

    def import_relationships(self, csv_file_path):
        with self.driver.session() as session:
            # Use built-in LOAD CSV to create relationships
            query = """
            LOAD CSV WITH HEADERS FROM 'file:///' + $file_path AS row
            MATCH (source {nodeID: row.`START_ID`})
            MATCH (target {nodeID: row.`END_ID`})
            CALL apoc.create.relationship(source, row.TYPE, {}, target) YIELD rel
            RETURN rel
            """
            session.run(query, file_path=csv_file_path)

    def import_external_source_properties(self, csv_file_path):
        with self.driver.session() as session:
            query = """
            LOAD CSV WITH HEADERS FROM 'file:///' + $file_path AS row
            MATCH (n {nodeID: row.external_source_id})
            SET n.name = row.title,
                n.source_primary = row.source_primary,
                n.source_secondary = row.source_secondary,
                n.source_link = row.source_link,
                n.source_date = row.source_date,
                n.pubmed_id = CASE WHEN row.pubmed_id <> '' THEN row.pubmed_id ELSE null END,
                n.country_of_origin = CASE WHEN row.country_of_origin <> '' THEN row.country_of_origin ELSE null END
            """
            session.run(query, file_path=csv_file_path)

    def delete_all_data(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

# Usage example
start_total = time.time()
print(f"\nStarting import process at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

importer = Neo4jImporter(
    "neo4j://localhost:7687",
    "neo4j",
    "alex12345"
)

try:
    # Delete all data
    start_time = time.time()
    importer.delete_all_data()
    print_execution_time(start_time, "Deleting all data")

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
