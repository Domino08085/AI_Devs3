import requests
from openai import OpenAI
from dotenv import load_dotenv
import os
import re

load_dotenv()

URL = os.getenv("URL_zad1") # from the exercise 1
USERNAME = "tester" # from the exercise 1
PASSWORD = "574e112a" # from the exercise 1
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")


def extract_question(response_text):

    try:
        # Print the full response for debugging
        print("Full response from website:", response_text)
        
        # Try to find text between "Question:<br />" and "</p>"
        question_match = re.search(r'Question:<br />(.*?)</p>', response_text, re.DOTALL) #DOTALL used to match also a new line
        
        if question_match:
            question = question_match.group(1).strip() #capturing group 1 from () in the regex and strip() to remove leading and trailing whitespaces
            print(f"Extracted question: {question}")
            return question
        else:
            print("No question found in response")
            return None
            
    except Exception as e:
        print(f"Error extracting question: {e}")
        return None

def get_ai_answer(question):

    try:
        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Get response from AI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f'answer to the question: "{question}" providing only the year number as the answer'}]
        )
        
        # Extract the answer from AI response
        ai_answer = response.choices[0].message.content
        print(f"question: {question}")
        print(f"AI generated answer: {ai_answer}")
        return ai_answer
        
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return None

def get_question_from_website():

    try:
        # Set up the headers
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Make initial GET request to get the question
        print("Getting question from website...")
        response = requests.get(URL, headers=headers)
        
        if response.status_code == 200:
            return extract_question(response.text)
        else:
            print(f"Failed to get question. Status code: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error getting question from website: {e}")
        return None

def submit_login_and_answer(answer):
    
    # Set up the headers
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Prepare the data to send
    data = {
        "username": USERNAME,
        "password": PASSWORD,
        "answer": answer
    }
    
    try:
        # Send POST request
        print("\nSending answer to server...")
        response = requests.post(URL, headers=headers, data=data)
        
        # Print the response
        print("\nServer response:")
        print(response.text)
        
        # Check if request was successful
        if response.status_code == 200:
            print("Request successful!")
        else:
            print(f"Request failed with status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")

# Main program
def main():
    # Step 1: Get question from website
    question = get_question_from_website()
    if not question:
        print("Failed to get question from website")
        return
        
    # Step 2: Get answer from AI
    ai_answer = get_ai_answer(question)
    if not ai_answer:
        print("Failed to get AI answer")
        return
        
    # Step 3: Submit answer
    submit_login_and_answer(ai_answer)

# Run the program
if __name__ == "__main__":
    main()