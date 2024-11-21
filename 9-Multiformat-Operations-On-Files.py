from dotenv import load_dotenv
from openai import OpenAI
import requests
import json
import os
import base64
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
    
def speech_to_text(file_path):
    try:

        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Transcribe the audio file using Whisper API
        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        # Extract the transcription from the response
        transcription = response.text
        return transcription
        
    except Exception as e:
        print(f"Error translating MP3 to text: {e}")
        return None

def get_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def get_ai_answer_to_image(question, context, image_path=None, image_type="png"):
    try:
        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Encode the image if provided
        image_data = None
        if image_path:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

        # Prepare the messages
        messages = [
            {"role": "system", "content": context},
            {"role": "user", "content": [
                {
                "type": "text",
                "text": question,
                },
                {
                "type": "image_url",
                "image_url": {
                    "url":  f"data:image/{image_type};base64,{image_data}"
                },
                },
            ]
            }
        ]

        # Get response from AI
        response = client.chat.completions.create(
            #model="gpt-4o-mini",
            model="gpt-4o",
            messages=messages
        )
        
        # Extract the answer from AI response
        ai_answer = response.choices[0].message.content
        return ai_answer
        
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return None
    
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

    context = '''
    You are looking for the information about the people and hardware in the text.
    If you think that the text has information about the people, please write "people".
    If you think that the text has information about the hardware, please write "hardware".
    If you see that the text is mentioning robots and pineapple pizza it should be classified as "Other".
    AI module update or communication system update should be classified as "Other".
    If the text is not clear or it is describing something else than people or hardware, please write "Other".
    '''

    people_files_list = []
    hardware_files_list = []

    # Scan the folder for text files, images and audio files
    folder_path = '../../zadanie 8/pliki_z_fabryki'
    audio_extensions = ["mp3", "wav", "flac"]
    txt_extensions = ["txt", "docx", "pdf"]
    image_extensions = ["png", "jpg", "jpeg"]
    audio_files = scan_folder(folder_path, audio_extensions)
    txt_files = scan_folder(folder_path, txt_extensions)
    image_files = scan_folder(folder_path, image_extensions)

    for file in audio_files:
        print(f"audio files: {file}")
    
    for file in txt_files:
        print(f"txt files: {file}")

    for file in image_files:
        print(f"image files: {file}")

    print(f'\nProcessing the files...\n')

    # Process the text files
    for file_path in txt_files:
        text = get_text_from_file(file_path)
        ai_answer = get_ai_answer(text, context)
        print(f'AI answer to file {os.path.basename(file_path)}: {ai_answer}')
        if ai_answer.lower() == 'people':
            people_files_list.append(os.path.basename(file_path))
        if ai_answer.lower() == 'hardware':
            hardware_files_list.append(os.path.basename(file_path))

    # Process the audio files
    for file_path in audio_files:
        text = speech_to_text(file_path)
        ai_answer = get_ai_answer(text, context)
        print(f'AI answer to file {os.path.basename(file_path)}: {ai_answer}')
        if ai_answer.lower() == 'people':
            people_files_list.append(os.path.basename(file_path))
        if ai_answer.lower() == 'hardware':
            hardware_files_list.append(os.path.basename(file_path))

    # # Process the image files
    for file_path in image_files:
        ai_answer = get_ai_answer_to_image('Is this image has information about the people or hardware?', context, file_path)
        print(f'AI answer to file {os.path.basename(file_path)}: {ai_answer}')
        if ai_answer.lower() == 'people':
            people_files_list.append(os.path.basename(file_path))
        if ai_answer.lower() == 'hardware':
            hardware_files_list.append(os.path.basename(file_path))

    # Send the results
    files_list = {
        "people": people_files_list,
        "hardware": hardware_files_list
    }
    task_type = 'kategorie'
    send_results(task_type, api_key, files_list, URL_POST)

# Run the program
if __name__ == "__main__":
    main()