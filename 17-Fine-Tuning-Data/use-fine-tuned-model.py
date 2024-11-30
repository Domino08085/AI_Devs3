import json
import openai
from dotenv import load_dotenv
import os
import requests
from openai import OpenAI

load_dotenv()
api_key = os.getenv("APIkey")
URL_POST = os.getenv("URL_post")
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")
   
def get_ai_answer(dataset_content):

    try:
        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Get response from AI
        response = client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:personal:ai-devs3-task-17-research:AZMdnVBN", # Mine fine-tuned model
            #model="gpt-4o",
            messages=[
                {"role": "system", "content": "Classify the dataset if it is correct or incorrect"},
                {"role": "user", "content": dataset_content}
            ]
        )
        
        # Extract the answer from AI response
        ai_answer = response.choices[0].message.content
        return ai_answer
        
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return None
    
def prepare_dataset(data_string):
    """Convert the raw string data into structured format."""
    dataset = []
    # Split the input string into lines
    lines = data_string.strip().split('\n')
    
    for line in lines:
        # Split ID and values
        id_part, values = line.split('=')
        # Convert values to list of integers
        numbers = [int(x) for x in values.split(',')]
        
        # Create formatted entry
        entry = {
            "id": id_part,
            "values": numbers
        }
        dataset.append(entry)
    return dataset

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
        response.encoding = 'utf-8'  # Ensure proper encoding
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))

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
    data = """01=12,100,3,39
    02=-41,75,67,-25
    03=78,38,65,2
    04=5,64,67,30
    05=33,-21,16,-72
    06=99,17,69,61
    07=17,-42,-65,-43
    08=57,-83,-54,-43
    09=67,-55,-6,-32
    10=-20,-23,-2,44"""

    # Process data
    dataset = prepare_dataset(data)

    print("Dataset:")
    print(dataset)

    results = []

    # Process each entry
    for entry in dataset:
        values_string = ",".join(map(str, entry['values']))
        result = get_ai_answer(values_string)
        print(f"ID: {entry['id']}, Result: {result}")
        if result == 'correct':
            results.append(entry['id'].strip())
    
    print("Results:")
    print(results)

    send_results("research", api_key, results, URL_POST)

if __name__ == "__main__":
    main()