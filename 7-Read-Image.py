import base64
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")

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
    
def get_ai_answer(question, context):

    try:
        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Get response from AI
        response = client.chat.completions.create(
            #model="gpt-4o-mini",
            model="gpt-4o",
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


# Main program
def main():

    context = '''
    You are a map expert.
    You need to deduce from the image what city is depicted on the map.
    Below are some tips:
    - This is the city located in Poland so you don't need to look for it in other countries
    - There are the street names, key locations like cementaries, buildings, bus stops and railways
    - Focus on the key locations like buildings or places with the street names around them
    '''
    question = 'Return the key elements from the image that could help deduce the city name'

    file_path_map_1 = '../../zadanie 7/mapa 1.png'
    file_path_map_2 = '../../zadanie 7/mapa 2.png'
    file_path_map_3 = '../../zadanie 7/mapa 3.png'
    file_path_map_4 = '../../zadanie 7/mapa 4.png'

    #file_path_map = '../../zadanie 7/mapa-optimized.jpg'

    # Process the images
    print("Processing image...")
    answer_map_1 = get_ai_answer_to_image(question, context, file_path_map_1)
    print(f"AI answer:\n{answer_map_1}\n")

    answer_map_2 = get_ai_answer_to_image(question, context, file_path_map_2)
    print(f"AI answer:\n{answer_map_2}\n")

    answer_map_3 = get_ai_answer_to_image(question, context, file_path_map_3)
    print(f"AI answer:\n{answer_map_3}\n")

    answer_map_4 = get_ai_answer_to_image(question, context, file_path_map_4)
    print(f"AI answer:\n{answer_map_4}\n")

    context_final = f'''
    Having all the conclusions from previous images scans you need to answer what city is depicted on the map parts.
    IMPORTANT! One part and only one is from completely different city, rest is from the same city so, you need to be careful!
    Focus mainly on the key location like "Cmentarz Ewangelicko Augsburski near the road 534 and streets Parkowa and Cmentarna"
    It's not Brodnica, Białystok, Kraków, Warsaw or Toruń!
    Below are the conclusions from the given map parts:
    - map part one: "{answer_map_1}"\n
    - map part two: "{answer_map_2}"\n
    - map part three: "{answer_map_3}"\n
    - map part four: "{answer_map_4}"\n
    '''
    question_final = 'What city is depicted on the map?'

    answer_final = get_ai_answer(question_final, context_final)

    print(f"Final answer:\n{answer_final}\n")

# Run the program
if __name__ == "__main__":
    main()