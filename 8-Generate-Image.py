from dotenv import load_dotenv
from openai import OpenAI
import requests
import json
import os

load_dotenv()
api_key = os.getenv("APIkey")
URL = os.getenv("URL_zad8") # from the task 8
URL_POST = os.getenv("URL_post")
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")

def get_data_from_website(URL):

    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        # Making GET request and ensuring that the JSON is encoded properly (with polish characters etc.)
        print("Getting data from website...")
        response = requests.get(URL, headers=headers)
        data = response.json()
        
        if response.status_code == 200:
            return data
        else:
            print(f"Failed to get data. Status code: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error getting data from website: {e}")
        return None
    
def generate_ai_image(image_description):

    try:
        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Generate the image
        response = client.images.generate(
            model="dall-e-3",
            prompt=image_description,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        # Extract the image URL from the response
        image_url = response.data[0].url
        return image_url
        
    except Exception as e:
        print(f"Error generating image with DALL-E: {e}")
        return None
    
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

    # Get data from website
    robot_description = get_data_from_website(URL)
    print(f'Data from website: {robot_description.get("description", "")}')
    robot_description = robot_description.get("description", "")
    
    # Rewrite the description to be a prompt for DALL-E
    context = "You are a helpful assistant. You are rewriting the sentences that will be used as a prompt for image generation in a model DALL-E."
    question = f'Translate the description of a robot and rewrite it as a prompt for DALL-E. \n Description: "{robot_description}"'
    description_image = get_ai_answer(question, context)

    print(f'Description image: {description_image}')

    # Generate image
    ai_image = generate_ai_image(description_image)

    print(f'AI image URL: {ai_image}')

    # Send the results
    task_type = 'robotid'
    send_results(task_type, api_key, ai_image, URL_POST)

# Run the program
if __name__ == "__main__":
    main()