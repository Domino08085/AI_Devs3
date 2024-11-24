from typing import List, Dict
import openai
from dotenv import load_dotenv
import os
from VectorDatabaseSearch import SimpleDocumentSearch
import requests
import json

load_dotenv()
api_key = os.getenv("APIkey")
URL_POST = os.getenv("URL_post")

class DocumentBasedAnswering:
    def __init__(self):
        """Initialize with API keys and search engine"""
        load_dotenv()
        
        # Initialize document search
        self.search_engine = SimpleDocumentSearch(
            openai_key=os.getenv("OpenAI_APIkey"),
            qdrant_url=os.getenv("Qdrant_URL"),
            qdrant_key=os.getenv("Qdrant_APIkey")
        )
        
        # Setup OpenAI
        openai.api_key = os.getenv("OpenAI_APIkey")

    def save_files_to_db(self, folder_path: str):
        """Trigger save_files method from search engine"""
        self.search_engine.save_files(folder_path)

    def format_context(self, similar_docs: List[Dict]) -> str:
        """Format similar documents into context string"""
        context = "Relevant information from documents:\n\n"
        for doc in similar_docs:
            context += f"From file '{doc['file_name']}':\n{doc['content']}\n\n"
        return context

    def get_answer(self, question: str, additional_information: str, max_docs: int = 3) -> str:
        """Get answer based on similar documents"""
        try:
            # Find similar documents
            similar_docs = self.search_engine.find_similar(question, max_docs)
            
            if not similar_docs:
                return "No relevant documents found to answer the question."
            
            print(f"Found {len(similar_docs)} similar documents.")
            print("Similar documents:")
            for doc in similar_docs:
                print(f"File: {doc['file_name']}, Similarity: {doc['similarity']}")
            
            # Format context from similar documents
            context = self.format_context(similar_docs)
            
            # Create prompt for GPT
            prompt = f"""Based on the following context, please answer the question. 
            If the answer cannot be derived from the context, say so.
            {additional_information}
            
            Context:
            {context}
            
            Question: {question}"""
            
            # Get response from OpenAI
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided document context."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error getting answer: {e}"

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


if __name__ == "__main__":
    # Example usage
    answering = DocumentBasedAnswering()
    
    # Save files to database
    folder_path = "../../../zadanie 12/pliki_z_fabryki/weapons_tests/do-not-share"
    answering.save_files_to_db(folder_path)

    # Example question
    question = "W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?"
    answer = answering.get_answer(question, "As an answer provide only the date in the format YYYY-MM-DD.")
    
    print("\nQuestion:", question)
    print("\nAnswer:", answer)

    # Send the results
    task_type = 'wektory'
    send_results(task_type, api_key, answer, URL_POST)

