import requests
import json
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()
api_key = os.getenv("APIkey")
URL = os.getenv("URL_zad6") # from the exercise 6
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")

def get_ai_answer(question, text, context):

    try:
        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Get response from AI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": f'{question}\n"{text}"'}
                #{"role": "user", "content": f'Below is the transcript. Please provide a step-by-step reasoning process to determine the University street name where professor Andrzej Maj was working. Then, provide the final answer?: \n "{text}"'}
            ]
        )
        
        # Extract the answer from AI response
        ai_answer = response.choices[0].message.content
        return ai_answer
        
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return None
    
def get_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def send_results(data, URL: str, api_key):

    # Set up the headers
    headers = {
        "Content-Type": "application/json"
    }

    Body = {
    "task": "mp3",
    "apikey": api_key,
    "answer": data
    }
    
    try:
        # Send POST request
        print("\nSending data...")
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


# Main program
def main():

    context = '''
    You need to deduce from the transcripts where the professor Andrzej Maj was working.
    We need the name of the street of the University where professor was working.
    Below are some tips:
    - Think in polish
    - We need the name of the University with a street name and the number of the building
    '''
    question = 'Below is the transcript. Please provide a step-by-step reasoning process to determine the University street name where professor Andrzej Maj was working. Then, provide the final answer?:'

    file_path_adam = '../../zadanie 6/adam.txt'
    file_path_agnieszka = '../../zadanie 6/agnieszka.txt'
    file_path_ardian = '../../zadanie 6/ardian.txt'
    file_path_michal = '../../zadanie 6/michal.txt'
    file_path_monika = '../../zadanie 6/monika.txt'
    file_path_rafal = '../../zadanie 6/rafal.txt'

    transcript_adam = get_text_from_file(file_path_adam)
    transcript_agnieszka = get_text_from_file(file_path_agnieszka)
    transcript_ardian = get_text_from_file(file_path_ardian)
    transcript_michal = get_text_from_file(file_path_michal)
    transcript_monika = get_text_from_file(file_path_monika)
    transcript_rafal = get_text_from_file(file_path_rafal)

    # Process the transcripts with Chain of Thought
    print("Processing Adam's transcript...")
    answer_adam = get_ai_answer(question, transcript_adam, context)
    print(f"AI's reasoning and answer for transcript:\n{answer_adam}\n")

    print("Processing Agnieszka's transcript...")
    answer_agnieszka = get_ai_answer(question, transcript_agnieszka, context)
    print(f"AI's reasoning and answer for transcript:\n{answer_agnieszka}\n")

    print("Processing Ardian's transcript...")
    answer_ardian = get_ai_answer(question, transcript_ardian, context)
    print(f"AI's reasoning and answer for transcript:\n{answer_ardian}\n")

    print("Processing Michal's transcript...")
    answer_michal = get_ai_answer(question, transcript_michal, context)
    print(f"AI's reasoning and answer for transcript:\n{answer_michal}\n")

    print("Processing Monika's transcript...")
    answer_monika = get_ai_answer(question, transcript_monika, context)
    print(f"AI's reasoning and answer for transcript:\n{answer_monika}\n")

    print("Processing Rafal's transcript...")
    answer_rafal = get_ai_answer(question, transcript_rafal, context)
    print(f"AI's reasoning and answer for transcript:\n{answer_rafal}\n")

    context_final = f'''
    Having all the conclusions from the transcripts, you need to deduce where the professor Andrzej Maj was working.
    We need the name of the street of the University where professor was working.
    Answer in polish.
    IMPORTANT!: As the answer we need only the University name and street name with a number of the building!
    Below are the conclusions from the transcripts:
    - Adam: "{answer_adam}"\n
    - Agnieszka: "{answer_agnieszka}"\n
    - Ardian: "{answer_ardian}"\n
    - Michal: "{answer_michal}"\n
    - Monika: "{answer_monika}"\n
    - Rafal: "{answer_rafal}"\n
    '''
    question_final = 'Provide the address of the University where professor Andrzej Maj was working having in mind the conclusions'

    answer_final = get_ai_answer(question_final, '', context_final)

    print(f"Answer for the final question:\n{answer_final}\n")

    #Submit answer
    send_results(answer_final, URL, api_key)
        

# Run the program
if __name__ == "__main__":
    main()