from neo4j import GraphDatabase

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
                name: row.NAME
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

    def delete_all_data(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

# Usage example
importer = Neo4jImporter(
    "neo4j://localhost:7687",
    "neo4j",
    "alex12345"
)

try:
    importer.delete_all_data()
    importer.import_nodes("nodes.csv")
    importer.import_relationships("relationships.csv")
finally:
    importer.close()
