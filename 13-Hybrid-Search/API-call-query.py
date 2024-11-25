import requests
import json
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")

class DBAPIClient:
    def __init__(self, api_key, base_url="YOUR_API_ENDPOINT"):
        self.api_key = api_key
        self.base_url = base_url

    def execute_query(self, query):
        payload = {
            "task": "database",
            "apikey": self.api_key,
            "query": query
        }
        
        response = requests.post(self.base_url, json=payload)
        return response.json()

    def get_tables(self):
        return self.execute_query("show tables")

    def get_table_structure(self, table_name):
        return self.execute_query(f"show create table {table_name}")
    
def get_ai_answer(question, context):

    try:
        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Get response from AI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            #model="gpt-4o",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": f'{question}'}
            ]
        )
        
        # Extract the answer from AI response
        ai_answer = response.choices[0].message.content
        return ai_answer
        
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return None
    
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
        answer = json.loads(response.text)
        
        # Check if request was successful
        if response.status_code == 200:
            print("Request successful!")
            return answer
        else:
            print(f"Request failed with status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")

def main():

    load_dotenv()
    api_key = os.getenv("APIkey")
    URL_POST = os.getenv("URL_post")
    URL_QUERY = os.getenv("URL_zad13")

    # Initialize client
    client = DBAPIClient(api_key, URL_QUERY)
    
    # Get table information
    tables = client.get_tables()
    print("Available tables:", tables)

    tables_structure = ''
    
    # Get structure for relevant tables
    connections_structure = client.get_table_structure("connections")
    print("\nEmployees table structure:")
    print(json.dumps(connections_structure, indent=2))
    print(connections_structure['reply'][0]['Create Table'])
    tables_structure += '"' + connections_structure['reply'][0]['Create Table'] + '"' + '\n\n'

    datacenters_structure = client.get_table_structure("datacenters")
    print("\nDatacenters table structure:")
    print(json.dumps(datacenters_structure, indent=2))
    tables_structure += '"' + datacenters_structure['reply'][0]['Create Table'] + '"' + '\n\n'

    correct_order_structure = client.get_table_structure("correct_order")
    print("\nEmployees table structure:")
    print(json.dumps(correct_order_structure, indent=2))
    tables_structure += '"' + correct_order_structure['reply'][0]['Create Table'] + '"' + '\n\n'

    users_structure = client.get_table_structure("users")
    print("\nEmployees table structure:")
    print(json.dumps(users_structure, indent=2))
    tables_structure += '"' + users_structure['reply'][0]['Create Table'] + '"' + '\n\n'

    print(tables_structure)
 

    context = f'''
    - You need to help the user create a SQL query.\n
    - Below is the structure of every table in the database.\n
    - !Return only the SQL query string without any additonal character!\n
    - Use the structures below to create the SQL query:\n
    {tables_structure}
    '''

    query = get_ai_answer("Get active datacenters IDs without duplicates where the users id are not active. Use JOIN if you need", context)

    #query = 'SELECT DISTINCT d.dc_id FROM datacenters d JOIN users e ON d.manager = e.id WHERE e.is_active = 0'

    print(query)
    
    result = client.execute_query(query)
    print("\nDatacenters managed by inactive users:")
    print(result['reply'])
    results_table = []
    
    for i in result['reply']:
        results_table.append(i['dc_id'])

    task = 'database'
    send_results(task, api_key, results_table, URL_POST)

if __name__ == "__main__":
    main()