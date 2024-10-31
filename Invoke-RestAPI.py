import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()  # loads variables from .env file
api_key = os.getenv("API_KEY")

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

GetURI = "https://poligon.aidevs.pl/dane.txt"

headers = {
        "Authorization" : "Bearer token"
    }

APIkey = "Bearer"

Body = {
    "task": "1234",
    "apikey": APIkey,
    "answer": [0,1,2,3,4]
}

# 0 (zero) code response means success. Every code below 0 is an error.
#response = invoke_rest_api(RequestURI, "GET", headers, Body, "application/json")

#response = invoke_rest_api(RequestURI, "GET", headers, "application/json")

response = requests.get(GetURI, headers=headers, verify=False) # verify=False to Disable SSL verification !ONLY for tests!

# Check the response
if response.status_code == 200:
    print("API call successful")
    response_text = response.text
    response_table = response_text.splitlines()
    #response_json = response.json()
    print(response_table)
else:
    print(f"API call failed with status code {response.status_code}")
    print(response.text)

RequestURI = "https://poligon.aidevs.pl/verify"

Body = {
    "task": "POLIGON",
    "apikey": APIkey,
    "answer": response_table
}

#Przekazac w odpowiedni sposob APIkey ---> ..........

response = requests.post(RequestURI, headers=headers, json=Body, verify=False) # verify=False to Disable SSL verification !ONLY for tests!

if response.status_code == 200:
    print("API call successful")
    response_text = response.text
    #response_table = response_text.splitlines()
    #response_json = response.json()
    print(response_text)
else:
    print(f"API call failed with status code {response.status_code}")
    print(response.text)
