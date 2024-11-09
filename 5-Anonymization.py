from langchain_ollama import OllamaLLM
from openai import OpenAI
import requests
from dotenv import load_dotenv
import os

load_dotenv()

URL = os.getenv("URL_zad5") # from the exercise 5
URL_POST = os.getenv("URL_post") # from the exercise 5
api_key = os.getenv("APIkey")
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")

def get_text_from_website():

    try:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Make initial GET request to get the question
        print("Getting text from website...")
        response = requests.get(URL, headers=headers)
        
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to get question. Status code: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error getting question from website: {e}")
        return None
    
def anonymize_text(text, context):
    llm = OllamaLLM(model="gemma2:2b")

    response = llm.invoke(f'Anonymize the text: "{text}" \n Remember about the rules: {context}')

    return response

def anonymize_text_openai(text, context):

    try:
        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Get response from AI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": f'Anonymize the text: "{text}" \n Remember about the rules: {context}'}
            ]
        )
        
        # Extract the answer from AI response
        ai_answer = response.choices[0].message.content
        return ai_answer
        
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return None

def submit_text(text, URL, api_key):
    
    # Set up the headers
    headers = {
        "Content-Type": "application/json"
    }

    Body = {
    "task": "CENZURA",
    "apikey": api_key,
    "answer": text
    }

    response = requests.post(URL, headers=headers, json=Body)

    if response.status_code == 200:
        print("API call successful")
        response_text = response.text
        print(response_text)
    else:
        print(f"API call failed with status code {response.status_code}")
        print(response.text)

# Main program
def main():

    context = '''
    - Every word that needs to be redacted should be replaced with the word "CENZURA"
    - Treat street names and numbers as one word! 
    <EXAMPLE> 
    before anonymization: "ul. Akacjowa 7"
    after anonymization: "ul. CENZURA"
    </EXAMPLE>
    - Treat name and surname as one word
    - Answer should containt only the text that was anonymized
    - Do not provide any additional information that is not asked for
    - The anonymized text and punctuation MUST be exactly the same as in the original text
    - Do not redact words like: "ul.", "ulicy"
    <EXAMPLE>
    Tożsamość podejrzanego: CENZURA. Mieszka we CENZURA na ul. CENZURA. Wiek: CENZURA lat.
    </EXAMPLE>
    '''

    # Step 1: Get text from website
    text = get_text_from_website()

    print(f'Text from website: {text}')

    # Step 2: Anonymize the text
    anonymized_text = anonymize_text(text, context)
    #anonymized_text = anonymize_text_openai(text, context)

    print(f'Anonymized text: {anonymized_text}')

    # Step 3: Submit the anonymized text
    submit_text(anonymized_text, URL_POST, api_key)

if __name__ == "__main__":
    main()

