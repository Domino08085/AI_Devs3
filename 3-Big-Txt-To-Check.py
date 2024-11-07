import requests
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from typing import List, Dict
import re

load_dotenv()

URL = os.getenv("URL_zad3") # from the exercise 3
URL_TXT_FILE = os.getenv("URL_text") # from the exercise 3
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")
MY_API_KEY = os.getenv("APIkey")


def download_json_file(URL_TXT_FILE: str) -> dict:
    """
    Download JSON content from a text file at the given URL
    """
    try:
        response = requests.get(URL_TXT_FILE)
        response.raise_for_status()  # Raise an exception for bad status codes
        return json.loads(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None

def is_math_problem(question: str) -> bool:
    """
    Check if the question is a math problem
    """
    math_pattern = r'^\s*\d+\s*[\+\-\*\/]\s*\d+\s*$'
    return bool(re.match(math_pattern, question))

def validate_math_answer(question: str, given_answer: int) -> tuple:
    """
    Validate a math problem and return if it's correct and the correct answer
    """
    try:
        # Parse the question
        parts = question.split()
        num1 = int(parts[0])
        operator = parts[1]
        num2 = int(parts[2])
        
        # Calculate correct answer
        if operator == '+':
            correct_answer = num1 + num2
        elif operator == '-':
            correct_answer = num1 - num2
        elif operator == '*':
            correct_answer = num1 * num2
        elif operator == '/' and num2 != 0:
            correct_answer = num1 / num2
        else:
            raise ValueError(f"Unsupported operator or invalid division: {operator}")
        
        return correct_answer == given_answer, correct_answer
    except Exception as e:
        print(f"Error validating math problem: {e}")
        return False, None

def process_test_block_with_llm(test_block: Dict, api_key: str) -> Dict:
    """
    Process a test block using LLM
    Modify this function to work with your specific LLM API
    """
    try:
        # Format the test block for LLM
        prompt = f"Please answer the following question accurately:\n"
        prompt += f"Question: {test_block['q']}\n"

        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a knowledgeable assistant. Please provide accurate answers to questions. Return only the answer without explanation."},
                {"role": "user", "content": prompt}
            ]
        )
    
        response = response.choices[0].message.content

        return {"q": test_block['q'], "a": response}
    
    except Exception as e:
        print(f"Error processing test block with LLM: {e}")
        return test_block

def process_data(data: Dict, api_key: str) -> Dict:
    """
    Process the entire dataset, handling both math problems and test blocks
    """
    processed_data = data.copy()
    test_data = data.get('test-data', [])
    processed_test_data = []
    
    print(f"Processing {len(test_data)} items...")
    
    for item in test_data:
        processed_item = item.copy()
        
        # Check if it's a math problem
        if is_math_problem(item['question']):
            is_correct, correct_answer = validate_math_answer(item['question'], item['answer'])
            
            if not is_correct:
                print(f"Math error found in: {item['question']}")
                processed_item['original_answer'] = item['answer']
                processed_item['answer'] = correct_answer
                processed_item['corrected'] = True
        
        # Check if there's a test block
        if 'test' in item:
            print(f"Processing test block for item: {item['question']}")
            processed_item['test'] = process_test_block_with_llm(item['test'], api_key)
        
        processed_test_data.append(processed_item)
    
    processed_data['test-data'] = processed_test_data
    return processed_data

def save_results(data: Dict, output_file: str):
    """
    Save processed results to a file
    """
    #adding my api key to the processed file
    if 'apikey' in data:
        data['apikey'] = MY_API_KEY
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def send_results(data: Dict, URL: str, api_key):

    # Set up the headers
    headers = {
        "Content-Type": "application/json"
    }

    Body = {
    "task": "JSON",
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

def summarize_changes(original_data: Dict, processed_data: Dict):
    """
    Print a summary of changes made
    """
    original_test_data = original_data.get('test-data', [])
    processed_test_data = processed_data.get('test-data', [])
    
    math_corrections = 0
    test_blocks_processed = 0
    
    for orig, proc in zip(original_test_data, processed_test_data):
        if 'corrected' in proc:
            math_corrections += 1
        if 'test' in proc and proc['test']['a'] != '???':
            test_blocks_processed += 1
    
    print("\nProcessing Summary:")
    print(f"Total items processed: {len(original_test_data)}")
    print(f"Math problems corrected: {math_corrections}")
    print(f"Test blocks processed: {test_blocks_processed}")

def main():
    # Configuration
    output_file = "processed_data.json"
    
    # Download and parse JSON
    print("Downloading JSON file...")
    original_data = download_json_file(URL_TXT_FILE)
    if not original_data:
        return
    
    # Process the data
    print("Processing data...")
    processed_data = process_data(original_data, OPENAI_API_KEY)
    
    # Save results
    save_results(processed_data, output_file)
    
    # Print summary
    summarize_changes(original_data, processed_data)
    
    print(f"\nProcessing complete. Results saved to {output_file}")

    print(f"\nSending results to server...")
    send_results(processed_data, URL, MY_API_KEY)

if __name__ == "__main__":
    main()