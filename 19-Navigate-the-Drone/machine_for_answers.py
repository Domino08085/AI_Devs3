# machine_for_answers.py
import os
import openai
from dotenv import load_dotenv
from typing import Dict, Optional
import json
import logging
import base64

load_dotenv()

class MachineForAnswers:
    def __init__(self):
        """Initialize with OpenAI API key from env or parameter"""
        self.api_key = os.getenv('OpenAI_APIkey')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        openai.api_key = self.api_key
        self.logger = logging.getLogger(__name__)

    def get_ai_answer(self, question, system_prompt):

        try:

            # Get response from AI
            response = openai.chat.completions.create(
                #model="gpt-4o-mini",
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f'{question}'}
                ]
            )
            
            # Extract the answer from AI response
            ai_answer = response.choices[0].message.content
            return ai_answer
            
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return None
        
    def get_ai_answer_to_image(self, question, system_prompt, image_path=None, image_type="png"):
        try:

            # Encode the image if provided
            image_data = None
            if image_path:
                with open(image_path, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Prepare the messages
            messages = [
                {"role": "system", "content": system_prompt},
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
            response = openai.chat.completions.create(
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