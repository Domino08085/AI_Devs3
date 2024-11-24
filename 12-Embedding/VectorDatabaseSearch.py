from pathlib import Path
import os
from typing import List, Dict
import openai
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("APIkey")
URL_POST = os.getenv("URL_post")
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")
QDRANT_API_KEY = os.getenv("Qdrant_APIkey")
QDRANT_URL = os.getenv("Qdrant_URL")

class SimpleDocumentSearch:
    def __init__(self, openai_key: str, qdrant_url: str, qdrant_key: str):
        """Start the search engine with API keys"""
        # Setup OpenAI
        openai.api_key = openai_key
        
        # Connect to Qdrant database
        try:
            self.db = QdrantClient(url=qdrant_url, api_key=qdrant_key)
            
            # Check if collection exists
            if not self.db.collection_exists("my_documents"):
                # Create collection if it doesn't exist
                self.db.create_collection(
                    collection_name="my_documents",
                    vectors_config=models.VectorParams(
                        size=1536,
                        distance=models.Distance.COSINE
                    )
                )
                print("Created new collection: my_documents")
            else:
                print("Using existing collection: my_documents")
                
        except Exception as e:
            print(f"Error connecting to database: {e}")
        
    def convert_text_to_vector(self, text: str) -> List[float]:
        """Convert text into numbers that AI can understand"""
        try:
            # Check if text is empty
            if not text.strip():
                raise ValueError("Empty text provided")
                
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            # Access the embedding using the correct response structure
            if hasattr(response, 'data') and len(response.data) > 0:
                vector = response.data[0].embedding
                
                # Verify vector dimension
                if len(vector) != 1536:
                    print(f"Warning: Expected 1536 dimensions, got {len(vector)}")
                    return None
                    
                return vector
            else:
                print("Error: Invalid response structure from OpenAI API")
                return None
            
        except AttributeError as e:
            print(f"Error accessing embedding data: {e}")
            return None
        except Exception as e:
            print(f"Error creating embedding: {e}")
            return None

    def save_files(self, folder_path: str):
        """Save all text files from a folder to the database"""
        import hashlib
        
        # Get all .txt files from the folder
        all_files = Path(folder_path).glob('*.txt')
        file_counter = 0
        skipped = 0
        
        for file_path in all_files:
            try:
                # Read the file
                with open(file_path, 'r', encoding='utf-8') as file:
                    text_content = file.read()
                
                # Create content hash
                content_hash = hashlib.md5(text_content.encode()).hexdigest()
                
                # Check if document exists by searching for hash
                existing_docs = self.db.scroll(
                    collection_name="my_documents",
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="content_hash",
                                match={"value": content_hash}
                            )
                        ]
                    )
                )[0]
                
                if existing_docs:
                    print(f"Skipping {file_path.name} - already exists")
                    skipped += 1
                    continue
                    
                # Convert text to vector
                text_vector = self.convert_text_to_vector(text_content)
                
                if text_vector:
                    file_counter += 1
                    self.db.upsert(
                        collection_name="my_documents",
                        points=[{
                            "id": file_counter,
                            "vector": text_vector,
                            "payload": {
                                "file_path": str(file_path),
                                "file_name": file_path.name,
                                "content": text_content,
                                "content_hash": content_hash
                            }
                        }]
                    )
                    print(f"Saved file {file_path.name} with ID: {file_counter}")
                    
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
        
        print(f"\nProcessing complete:")
        print(f"Files saved: {file_counter}")
        print(f"Files skipped: {skipped}")

    def find_similar(self, search_text: str, max_results: int = 3) -> List[Dict]:
        """Find similar documents to your search text"""
        try:
            # Convert search text to vector
            search_vector = self.convert_text_to_vector(search_text)
            
            # Search in database
            found_docs = self.db.search(
                collection_name="my_documents",
                query_vector=search_vector,
                limit=max_results
            )
            
            # Make results easy to read
            results = []
            for doc in found_docs:
                results.append({
                    "file_name": doc.payload["file_name"],
                    "content": doc.payload["content"],
                    "similarity": round(doc.score, 2)
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching: {e}")
            return []

# Example usage:
if __name__ == "__main__":

    from dotenv import load_dotenv
    load_dotenv()
    
    # Create search engine
    search = SimpleDocumentSearch(
        openai_key=os.getenv("OpenAI_APIkey"),
        qdrant_url=os.getenv("Qdrant_URL"),
        qdrant_key=os.getenv("Qdrant_APIkey")
    )
    
    # Save files
    #search.save_files("../../../zadanie 12/pliki_z_fabryki/weapons_tests/do-not-share")
    
    # Search for something
    results = search.find_similar("kradzież prototypu")
    
    # Show results
    for result in results:
        print(f"\nFile: {result['file_name']}")
        print(f"Similarity: {result['similarity']}")
        print("---")