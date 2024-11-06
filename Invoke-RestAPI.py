import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("APIkey")

def invoke_rest_api(uri, method, headers, body=None, content_type=None):
    try:
        if body:
            if method.upper() == "GET":
                response = requests.get(uri, headers=headers, data=body)
            else:
                if content_type:
                    headers['Content-Type'] = content_type
                response = requests.request(method, uri, headers=headers, data=json.dumps(body))
        else:
            response = requests.request(method, uri, headers=headers)
        
        return response.json()
    except Exception as e:
        print(f"Warning: {e}")

GetURI = os.getenv("Invoke_GetURI")

headers = {
        "Authorization" : "Bearer token"
    }

# 0 (zero) code response means success. Every code below 0 is an error.
response = requests.get(GetURI, headers=headers)

# Check the response
if response.status_code == 200:
    print("API call successful")
    response_text = response.text
    response_table = response_text.splitlines()
    print(response_table)
else:
    print(f"API call failed with status code {response.status_code}")
    print(response.text)

RequestURI = os.getenv("Invoke_RequestURI")

Body = {
    "task": "POLIGON",
    "apikey": api_key,
    "answer": response_table
}

response = requests.post(RequestURI, headers=headers, json=Body)

if response.status_code == 200:
    print("API call successful")
    response_text = response.text
    print(response_text)
else:
    print(f"API call failed with status code {response.status_code}")
    print(response.text)
