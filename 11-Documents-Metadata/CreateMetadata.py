from dotenv import load_dotenv
from openai import OpenAI
import requests
import json
import os
import glob

load_dotenv()
api_key = os.getenv("APIkey")
URL_POST = os.getenv("URL_post")
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")
    
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

def get_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    
    
def scan_folder(folder_path, extensions):
    """
    Scan the folder for files with specific extensions.
    :param folder_path: Path to the folder to scan.
    :param extensions: List of file extensions to look for.
    :return: List of file paths with the specified extensions.
    """
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(folder_path, f'*.{ext}')))
    return files

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
        print(f"Body:\n {Body}")
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

    keywords_dict = {}

    # Scan the folder for text files, images and audio files
    folder_path = '../../../zadanie 11/pliki_z_fabryki'
    facts_path = '../../../zadanie 11/pliki_z_fabryki/facts'
    txt_extensions = ["txt", "docx", "pdf", "md"]
    txt_files = scan_folder(folder_path, txt_extensions)
    facts = scan_folder(facts_path, txt_extensions)

    facts_context = ''

    for fact in facts:
        text = get_text_from_file(fact)
        if not (not text.strip() or text.strip().lower() == 'entry deleted'):
            ai_answer = get_ai_answer(text, 'You need to shorten the given text to the keywords. The answer should be a name of the given person and their jobs or skills <EXAMPLE> Barbara Zawadzka: specjialistka frontend, programista Javascript, programista Python </EXAMPLE>. Do not include any other information.')
            facts_context += ai_answer + "\n"
    
    print(facts_context)

    context = f'''
    - Summarize the text by the keywords.\n
    - Add the keywords information aboout the job and skills of the mentioned person.\n
    - Add the keywords information about the sectors from the name of the file.\n
    - Answer should only return comma-separated keywords!\n
    - Translating to polish keep the word in the nominative case.\n
    - Use the facts below :\n
    {facts_context}
    '''
    
    for file in txt_files:
        print(f"txt files: {file}")

    print(f'\nProcessing the files...\n')

    # Process the text files
    for file_path in txt_files:
        text = get_text_from_file(file_path)
        filename = os.path.basename(file_path)
        ai_answer = get_ai_answer(f'summarize the file {filename}: "{text}"', context)

        keywords = ai_answer

        
        keywords_dict[filename] = keywords

        print(f'Keywords for {filename}: {keywords}')

    # Send the results
    task_type = 'dokumenty'
    send_results(task_type, api_key, keywords_dict, URL_POST)

# Run the program
if __name__ == "__main__":
    main()