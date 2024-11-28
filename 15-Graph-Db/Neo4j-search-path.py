from neo4j import GraphDatabase
import json
from dotenv import load_dotenv
import os
import requests

def get_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def get_json_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.loads(file.read())

# Data
users = get_json_from_file("../../../zadanie 15/users.txt")
connections = get_json_from_file("../../../zadanie 15/connections.txt")

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_user(self, user):
        with self.driver.session() as session:
            session.execute_write(self._create_user_node, user)

    @staticmethod
    def _create_user_node(tx, user):
        query = """
        CREATE (u:User {
            user_id: $user_id,
            username: $username,
            access_level: $access_level,
            is_active: $is_active,
            lastlog: $lastlog
        })
        """
        # Convert the user dict to ensure proper parameter mapping
        params = {
            'user_id': str(user['user_id']),  # This will be mapped to user_id in the query
            'username': str(user['username']),
            'access_level': str(user['access_level']),
            'is_active': str(user['is_active']),
            'lastlog': str(user['lastlog'])
        }
        tx.run(query, params)

    def create_connection(self, connection):
        with self.driver.session() as session:
            session.execute_write(self._create_connection_relationship, connection)

    @staticmethod
    def _create_connection_relationship(tx, connection):
        query = """
        MATCH (u1:User {user_id: $user1_id})
        MATCH (u2:User {user_id: $user2_id})
        CREATE (u1)-[:CONNECTED_TO]->(u2)
        """
        params = {
            'user1_id': str(connection['user1_id']),
            'user2_id': str(connection['user2_id'])
        }
        tx.run(query, params)

    def find_shortest_path(self, start_username, end_username):
        with self.driver.session() as session:
            return session.execute_read(self._find_shortest_path, start_username, end_username)
    
    @staticmethod
    def _find_shortest_path(tx, start_username, end_username):
        query = """
        MATCH (start:User {username: $start_username})
        MATCH (end:User {username: $end_username})
        MATCH path = shortestPath(
            (start)-[:CONNECTED_TO*..15]-(end)
        )
        WHERE ALL(x IN NODES(path) WHERE SINGLE(y IN NODES(path) WHERE y.user_id = x.user_id))
        UNWIND nodes(path) as node
        RETURN COLLECT(DISTINCT node.username) as path_usernames
        """
        params = {
            'start_username': start_username,
            'end_username': end_username
        }
        result = tx.run(query, params)
        record = result.single()
        return record['path_usernames'] if record else None

def send_results(task, api_key, data, URL: str, ):

    # Set up the headers
    headers = {
        "Content-Type": "application/json"
    }

    Body = {
    "task": task,
    "apikey": api_key,
    "answer": data
    }
    
    try:
        # Send POST request
        print("\nSending data...")
        #print(f"Body:\n {Body}")
        response = requests.post(URL, headers=headers, json=Body)
        
        # Print the response
        print("\nServer response:")
        print(response.text)
        
        # Check if request was successful
        if response.status_code == 200:
            print("Request successful!")
            return response.json()
        else:
            print(f"Request failed with status code: {response.status_code}")
            return response.json()
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")


def main():

    load_dotenv()
    api_key = os.getenv("APIkey")
    URL_POST = os.getenv("URL_post")

    # Connect to Neo4j
    conn = Neo4jConnection(
        uri="bolt://localhost:7687",
        user="neo4j",
        password=os.getenv("neo4j_password")
    )

    try:
        # Create user nodes
        for user in users:
            conn.create_user(user)

        # Create connections
        for connection in connections:
            conn.create_connection(connection)

        # Find shortest path
        path = conn.find_shortest_path("Rafał", "Barbara")
        if path:
            print("Path:", ", ".join(path))
        else:
            print("No path found")
        
        send_results("connections", api_key, ",".join(path), URL_POST)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()