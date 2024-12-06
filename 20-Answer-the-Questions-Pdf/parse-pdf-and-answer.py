import os
from PyPDF2 import PdfReader
import openai
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
import fitz  # PyMuPDF
import io
from PIL import Image
import base64

# Load environment variables
load_dotenv()

# Initialize OpenAI API key
openai.api_key = os.getenv('OpenAI_APIkey')

# Initialize Qdrant client with API key and cluster URL
qdrant_api_key = os.getenv('Qdrant_APIkey')
qdrant_url = os.getenv('Qdrant_URL') 

# Create a Qdrant collection
collection_name = "pdf_text_collection"

try:
    qdrant_client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key
    )

    # Check if collection exists
    if not qdrant_client.collection_exists("pdf_text_collection"):
        # Create collection if it doesn't exist
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=1536,
                distance=models.Distance.COSINE
            )
        )
        print(f"Created new collection: {collection_name}")
    else:
        print(f"Using existing collection: {collection_name}")
                
except Exception as e:
    print(f"Error connecting to database: {e}")

def extract_text_from_pdf(pdf_path):
    """Extract text content from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return None

def get_openai_embedding(text):
    """Get embedding for text using OpenAI API."""
    
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

def store_text_in_vector_db(text):
    """Store text in a vector database."""
    # Split text into smaller chunks
    chunks = text.split('\n\n')
    vectors = []
    for i, chunk in enumerate(chunks):
        print(f"\nProcessing chunk {i+1} of {len(chunks)}")
        print(f"{chunk}\n")
        # Create an embedding for each chunk
        embedding = get_openai_embedding(chunk)
        if embedding:
            # Prepare the vector for Qdrant
            vectors.append(models.PointStruct(id=i, vector=embedding, payload={"text": chunk}))
    # Store the vectors in Qdrant
    qdrant_client.upsert(collection_name=collection_name, points=vectors)

def get_relevant_text(question, max_results=5):
    """Retrieve relevant text from the vector database."""
    # Create an embedding for the question
    question_embedding = get_openai_embedding(question)
    if question_embedding:
        # Query the vector database
        search_result = qdrant_client.search(
            collection_name=collection_name,
            query_vector=question_embedding,
            limit=max_results
        )

        # Retrieve the most relevant text chunks
        relevant_texts = [hit.payload['text'] for hit in search_result]
        
        for result in search_result:
            print(f"\nRelevant text:\n {result.payload['text']}")
            print(f"Similarity ---> {round(result.score, 2)}")

        return "\n".join(relevant_texts)
    
    return ""

def get_answer_from_openai(context, question):
    """Get answer from OpenAI API based on context and question."""
    try:
        # Create a prompt that includes both context and question
        prompt = f"""Context: {context}\n\nQuestion: {question}\n\nAnswer the question based on the context provided above."""
        
        # Make API call to OpenAI
        response = openai.chat.completions.create(
            #model="gpt-4o-mini",
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                {"role": "user", "content": prompt}
            ],
            #temperature=0.7,
            #max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error getting answer from OpenAI: {str(e)}")
        return None

# this method or LLM-answer-to-image one should be adjusted to extract only images that have text or possibly important information (skipping images of empty pages etc.)
def extract_and_save_images_from_pdf(pdf_path, output_folder):
    """Extract images from a PDF file and save them as PNG files."""
    pdf_document = fitz.open(pdf_path)
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            
            # Create output folder if it doesn't exist
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            # Save image as PNG
            image_filename = f"page_{page_number+1}_image_{img_index+1}.png"
            image_path = os.path.join(output_folder, image_filename)
            image.save(image_path, "PNG")
            print(f"Saved image: {image_path}")

def get_ai_answer_to_image(question, context, image_path=None, image_type="png"):
    try:

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


def main():
    # Get PDF path from user
    pdf_path = '../../../zadanie 20/notatnik-rafala.pdf'
    
    # Extract text from PDF
    print(f"\nExtracting text from PDF...")
    pdf_text = extract_text_from_pdf(pdf_path)

    # Extract images from PDF
    #output_folder = '../../../zadanie 20'
    #extract_and_save_images_from_pdf(pdf_path, output_folder)

    additional_text = get_ai_answer_to_image(
                    'Odczytaj tekst z obrazka. Tekst jest w języku polskim. Podaj tylko tekst, bez żadnych dodatkowych znaków.',
                    'You are a helpful assistant that is an expert in making OCR from images',
                    image_path='../../../zadanie 20/page_19_image_4.png',
                    image_type="png"
                )
    
    print(f"\nAdditional text: \n{additional_text}")

    pdf_text += f"\n\n{additional_text}"

    #print(f"PDF text: {pdf_text}")
    
    if pdf_text:
        print("\nPDF text extracted successfully!")

        #print(pdf_text)

        print("Storing text in vector database...")
        store_text_in_vector_db(pdf_text)
        
        # Interactive question-answering loop
        while True:
            question = input("\nEnter your question (or 'quit' to exit): ")
            
            if question.lower() == 'quit':
                break
            
            print("\nRetrieving relevant text...")
            relevant_text = get_relevant_text(question)
            
            print("\nGetting answer from OpenAI...")
            answer = get_answer_from_openai(relevant_text, question)
            
            if answer:
                print("\nAnswer:", answer)
            else:
                print("\nFailed to get an answer. Please try again.")

if __name__ == "__main__":
    main()
