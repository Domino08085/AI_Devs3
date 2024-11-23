from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import MarkdownTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient, models
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("APIkey")
URL_POST = os.getenv("URL_post")
URL = os.getenv("URL_zad10")
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")

class DocumentQA:
    def __init__(self, openai_api_key, model_name="gpt-4o-mini"):

        # Initialize OpenAI API key
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialize the LLM with specified model
        self.llm = ChatOpenAI(
            temperature=0.6,  # Set to 0 for more consistent answers
            model=model_name,
            max_tokens=15000  # Maximum length of the response
        )
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings()
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(":memory:")  # Using in-memory storage
        self.collection_name = "document_qa"
        
        # Create collection with proper configuration
        self.qdrant_client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=1536,  # OpenAI embeddings dimension
                distance=models.Distance.COSINE
            )
        )
        
        # Initialize vector store
        self.vector_store = None

    def load_and_process_document(self, markdown_path):
        """
        Load and process the markdown document
        """
        # Read the markdown file
        with open(markdown_path, 'r', encoding='utf-8') as file:
            markdown_content = file.read()
        
        # Split the text into chunks
        text_splitter = MarkdownTextSplitter(
            chunk_size=10000,
            chunk_overlap=2000
        )
        texts = text_splitter.split_text(markdown_content)
        
        # Create vector store
        self.vector_store = Qdrant(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embeddings=self.embeddings
        )
        
        # Add texts to the vector store
        self.vector_store.add_texts(texts)
        
        return len(texts)

    def setup_qa_chain(self):
        """
        Set up the QA chain
        """
        if not self.vector_store:
            raise ValueError("Please load a document first!")
        
        # Create retrieval QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 10}  # Number of relevant chunks to retrieve
            ),
            return_source_documents=True
        )

    def ask_question(self, question):
        """
        Ask a question and get an answer
        """
        if not hasattr(self, 'qa_chain'):
            self.setup_qa_chain()
        
        # Get the answer
        result = self.qa_chain({"query": question})
        
        return {
            "answer": result["result"],
            "source_documents": result["source_documents"]
        }

def main():

    # Initialize the system
    # Choose your model
    model_name = "gpt-4o-mini"
    
    qa_system = DocumentQA(OPENAI_API_KEY, model_name)
    print(f"Using OpenAI model: {model_name}")
    
    # Load and process the document
    markdown_path = "article.md"  # Replace with your document path
    num_chunks = qa_system.load_and_process_document(markdown_path)
    print(f"Document processed into {num_chunks} chunks")

    answers = []
    counter = 1
    
    # Example usage
    while True:
        question = input("\nEnter your question (or 'quit' to exit): ")
        if question.lower() == 'quit':
            break
            
        try:
            result = qa_system.ask_question(question)
            print("\nAnswer:", result["answer"])
            answer = f'{counter}={result["answer"]}'
            answers.append(answer)
            counter += 1
            print("\nBased on the following source documents:")
            for i, doc in enumerate(result["source_documents"], 1):
                print(f"\n{i}. {doc.page_content[:200]}...")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    print(f'Answers:\n')
    for answer in answers:
        print(answer)

if __name__ == "__main__":
    main()