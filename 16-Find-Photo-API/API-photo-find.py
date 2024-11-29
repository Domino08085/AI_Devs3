import json
from dotenv import load_dotenv
import os
import requests
import re
from urllib.parse import urlparse
from openai import OpenAI
import base64

load_dotenv()
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")


def execute_query(api_key, query):
        payload = {
            "task": "photos",
            "apikey": api_key,
            "answer": query
        }
        
        response = requests.post(os.getenv("URL_query"), json=payload)
        response.encoding = 'utf-8'  # Ensure proper encoding
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        return response.json()

def get_urls(response):
    # Extract message content from response
    message = response.get('message', '')

    urls = []
    
    # Find all URLs ending in .PNG using regex
    image_names = re.findall(r'(IMG_.*?\.PNG)', message)
    for image_name in image_names:
        url = f"https://centrala.ag3nts.org/dane/barbara/{image_name}"
        urls.append(url)

    return urls

def download_photos(urls):
    
    downloaded_files = []
    
    for url in urls:
        try:
            # Get filename from URL
            filename = os.path.basename(urlparse(url).path)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(script_dir, filename)
            
            # Download image
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Save image
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            downloaded_files.append(filename)
            print(f"Successfully downloaded: {filename}")
            
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")
            
    return downloaded_files

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
            model="gpt-4o-mini",
            #model="gpt-4o",
            messages=messages
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

def ask_model_for_corrections(image_path, image_name):
    #LLM model for image corrections in progress....
    print(f"Processing image: {image_name}")
    #print(f"Image path: {image_path}")
    proceed = input("\nGive me the command (STORE/DROP/REPAIR/BRIGHTEN/DARKEN): ")
    return proceed

def main():

    load_dotenv()
    api_key = os.getenv("APIkey")
    URL_POST = os.getenv("URL_post")

    script_dir = os.path.dirname(os.path.abspath(__file__))

    initial_response = execute_query(api_key, "START")
    links = get_urls(initial_response)
    #links = json.loads(links_json_text)
    #print(json.dumps(links, indent=2, ensure_ascii=False))
    # links = [link.replace('.PNG', '-small.PNG') for link in links] #for smaller size of the photos
    print(links)
    filenames = download_photos(links)
    final_photos = []
    while len(filenames) > 0:
        print("There are still photos to process: " + str(filenames))
        image_name = filenames.pop()
        command = ask_model_for_corrections(os.path.join(script_dir, image_name), image_name).strip()
        if command == 'STORE':
            print("Photo OK: " + image_name)
            final_photos.append(image_name)
            continue
        elif command == 'DROP':
            print("Dropping photo: " + image_name)
            continue
        elif command in ['REPAIR', 'BRIGHTEN', 'DARKEN']:
            result = execute_query(api_key, f"{command} {image_name}")
            link = get_urls(result)
            print(link)
            filenames.extend(download_photos(link))
    print("End of photos preparation")

    print("Stored photos:" + str(final_photos))

    final_photo_paths = [os.path.join(script_dir, image_name) for image_name in final_photos]

    context = "You are a photographer and you need to describe the poeple on the photos. Focus on the details of their look, clothing and accessories."
    question = "Describe the photo. ANSWER IN POLISH LANGUAGE!"

    for final_photo in final_photo_paths:
        description = get_ai_answer_to_image(question, context, final_photo)
        print(description)

        send_results("photos", api_key, description, URL_POST)
        input("Press Enter to continue...")

if __name__ == "__main__":
    main()