from fastapi import Depends
import pymongo
from api.config import settings
from neo4j import GraphDatabase

class Neo4jDBConnection:
    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            try:
                cls._driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD))
                cls._driver.verify_connectivity()
                print("Neo4j connection successful")
            except Exception as e:
                print(f"Neo4j connection failed: {e}")
                raise
        return cls._driver

def get_session():
    return Neo4jDBConnection.get_driver().session(database=settings.NEO4J_DATABASE)
