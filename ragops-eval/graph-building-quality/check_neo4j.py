from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()
driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD')))
s = driver.session()
print('Labels:', [r[0] for r in s.run('CALL db.labels()')])
print('Rels:', [r[0] for r in s.run('CALL db.relationshipTypes()')])
s.close()
driver.close()