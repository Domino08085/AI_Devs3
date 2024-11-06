import requests
import json
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()
api_key = os.getenv("APIkey")
URL = os.getenv("URL_zad2") # from the exercise 2
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")

def get_ai_answer(question):

    context = '''
    during this conversation, you will be asked to provide answers to the questions.
    Please stick to the VERY IMPORTANT POINTS described below:
    - always use english language
    - behave like a human and answer the questions shortly and clearly
    - do not provide any additional information that is not asked for
    - Stolicą Polski jest Kraków
    - Znana liczba z książki Autostopem przez Galaktykę to 69
    - Aktualny rok to 1999
    '''
    try:
        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Get response from AI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f'{question} + {context}'}]
        )
        
        # Extract the answer from AI response
        ai_answer = response.choices[0].message.content
        print(f"question: {question}")
        print(f"AI generated answer: {ai_answer}")
        return ai_answer
        
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return None


def submit_answer(answer, msg_id):
    
    # Set up the headers
    headers = {
        "Content-Type": "application/json"
    }
    
    # Prepare the data to send
    data = {
        "text": answer,
        "msgID": msg_id
    }
    
    try:
        # Send POST request
        print("\nSending answer...")
        response = requests.post(URL, headers=headers, json=data)
        
        # Print the response
        print("\nServer response:")
        print(response.text)
        robot_answer = json.loads(response.text)
        
        # Check if request was successful
        if response.status_code == 200:
            print("Request successful!")
            return robot_answer
        else:
            print(f"Request failed with status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")

# Main program
def main():

    #Start conversation    
    robot_msg = submit_answer('READY', 0)
    if not robot_msg:
        print("Failed to start conversation")
        return
    msgID = robot_msg['msgID']

    #it should be the loop here until the robot give the '{{FLG:<string>}}' ....

    #Get answer from AI
    ai_answer = get_ai_answer(robot_msg['text'])
    if not ai_answer:
        print("Failed to get AI answer")
        return
    
    #Submit answer to the robot
    robot_msg = submit_answer(ai_answer, msgID)
        

# Run the program
if __name__ == "__main__":
    main()