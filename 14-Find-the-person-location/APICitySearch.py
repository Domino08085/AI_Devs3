import openai
import requests
import json
from typing import Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")

class CitySearchAssistant:
    def __init__(self, api_key, openai_api_key: str):
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        self.api_key = api_key
        
    def get_suggestion(self, context, user_input: str) -> str:
        messages = [
            {"role": "system", "content": f'You are an expert in looking for the relations between the places and people. You need to find the city where person named "Barbara Zawadzka" is located. As the answer you just need to provide the person or city name to check next. !Do not provide the names if you have them already in the provided information!'},
            {"role": "user", "content": f'{user_input}. Here you have additional information for next suggestions:\n "{context}"' }
        ]
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    def execute_search(self, query, base_url):
        payload = {
            "apikey": self.api_key,
            "query": query
        }
        
        response = requests.post(base_url, json=payload)
        return response.json()
    
def get_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    
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

def save_search_results(file_path, input, data, search_type):  
    # Append data to the file
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(f'\n{search_type.upper()} name: ' + '"' + input + '"' + ' is related to: ' + json.dumps(data['message'], indent=2) + '\n')


def main():

    load_dotenv()
    api_key = os.getenv("APIkey")
    URL_POST = os.getenv("URL_post")
    URL_PEOPLE = os.getenv("URL_zad14_people")
    URL_PLACES = os.getenv("URL_zad14_places")

    
    note = get_text_from_file('../../../zadanie 14/notatka.txt')

    assistant = CitySearchAssistant(api_key, OPENAI_API_KEY)
    
    while True:
        user_input = input("What are you looking for? (or 'q' to exit): ")
        if user_input.lower() == 'q':
            break
            
        # Get suggestion from ChatGPT
        #suggestion = assistant.get_suggestion(note, user_input)
        #print(f"\nChatGPT suggests: {suggestion}")
        
        proceed = input("\nWould you like to search for the place or person? (place/person): ")
        if proceed.lower() == 'place':
            user_query = input("Put a place name: ")
            # Search place in external API
            place_data = assistant.execute_search(user_query, URL_PLACES)
            if place_data:
                print("\nPlace information found:")
                print(json.dumps(place_data, indent=2))
                save_search_results('../../../zadanie 14/notatka.txt', user_query, place_data, "place")
            else:
                print("\nCould not find place information.")
        if proceed.lower() == 'person':
            user_query = input("Put a person name: ")
            # Search person in external API
            person_data = assistant.execute_search(user_query, URL_PEOPLE)
            if person_data:
                print("\nPerson information found:")
                print(json.dumps(person_data, indent=2))
                save_search_results('../../../zadanie 14/notatka.txt', user_query, person_data, "person")
            else:
                print("\nCould not find person information.")
        else:
            print("\nInvalid input. Please try again.")
            
        continue_search = input("\nPut the name of the city that will be send to the Central. (or 'q' to exit): ")
        if continue_search.lower() == 'q':
            break
        else:
            answer = send_results("loop", api_key, continue_search, URL_POST)
            save_search_results('../../../zadanie 14/notatka.txt', continue_search, answer, "place")

if __name__ == "__main__":
    main()