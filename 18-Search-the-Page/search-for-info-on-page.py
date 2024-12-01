import requests
from bs4 import BeautifulSoup
import openai
from typing import List, Dict, Tuple
from urllib.parse import urljoin
from dotenv import load_dotenv
import os

class WebpageSearcher:
    def __init__(self, api_key: str):
        self.visited_urls = set()
        openai.api_key = api_key
        
    def fetch_webpage(self, url: str) -> str:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return ""

    def extract_content(self, html: str) -> Tuple[str, List[str]]:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract text
        text = ' '.join([p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span'])])
        
        # Extract links with their text
        links = []
        link_texts = []
        for a in soup.find_all('a', href=True):
            href = urljoin(self.current_url, a.get('href'))
            link_text = a.get_text().strip()
            if link_text:  # Only add non-empty link texts
                links.append(href)
                link_texts.append(f"{link_text} ({href})")
        
        # Clean up the text
        text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        
        # Add link texts to main text
        if link_texts:
            text = text + " " + " ".join(link_texts)
        return text, links #text, links
    
    def ask_confirmation(self, message: str) -> bool:
        while True:
            response = input(f"\n{message} (y/n/q to quit): ").lower()
            if response == 'q':
                print("[INFO] Search terminated by user")
                exit()
            if response in ['y', 'n']:
                return response == 'y'

    def search_for_answer(self, question: str, url: str, max_depth: int = 2) -> Dict:

        if not self.ask_confirmation(f"[CONFIRM] Check URL: {url}?"):
            return {"found": False, "answer": None, "url": None}

        print(f"\n[INFO] Checking URL: {url}")
        print(f"[INFO] Current search depth: {max_depth}")

        self.current_url = url
        # if max_depth < 0:
        #     print("[STOP] Maximum depth reached")
        #     return {"found": False, "answer": None, "url": None}

        if url in self.visited_urls:
            print("[SKIP] URL already visited")
            return {"found": False, "answer": None, "url": None}

        self.visited_urls.add(url)
        html = self.fetch_webpage(url)
        if not html:
            print("[ERROR] Failed to fetch webpage")
            return {"found": False, "answer": None, "url": None}

        content, links = self.extract_content(html)

        print("[INFO] Analyzing content...")
        print({content[:4000]})
        prompt = f"""
        Question: {question}
        Content: {content[:4000]}
        Task: Please think through this step-by-step:
        1. First, analyze if the content is relevant to the question
        2. Then, search for specific information that could answer the question
        3. Finally, provide your conclusion
        
        Format your response as:
        THINKING: Your step-by-step analysis
        ANSWER: The final answer or "Not found"
        """

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Search the webpage for the information that will help you answer the question. DO NOT TAKE THE COMMENTS INTO ACCOUNT!"},
                {"role": "user", "content": prompt}
            ]
        )

        full_response = response.choices[0].message.content# Split and display thinking process

        thinking_part = ""
        answer_part = ""
        
        if "THINKING:" in full_response and "ANSWER:" in full_response:
            parts = full_response.split("ANSWER:")
            thinking_part = parts[0].replace("THINKING:", "").strip()
            answer_part = parts[1].strip()
            
            print("\n[THINKING PROCESS]")
            print(thinking_part)
            print("\n[FINAL ANSWER]")
            print(answer_part)
        else:
            answer_part = full_response

        if "not found" not in answer_part.lower():
            return {"found": True, "answer": answer_part, "url": url}

        print("[INFO] Checking linked pages...")
        for link in links:
            if link not in self.visited_urls:
                result = self.search_for_answer(question, link, max_depth - 1)
                if result["found"]:
                    return result

        return {"found": False, "answer": None, "url": None}

# Usage example
if __name__ == "__main__":

    #I need to improve search method to avoid loops and search only the links that could have the answer or can guide LLM to it....

    load_dotenv()
    api_key = os.getenv("APIkey")
    URL_POST = os.getenv("URL_post")
    OPENAI_API_KEY = os.getenv("OpenAI_APIkey") 
    URL_SEARCH = os.getenv("URL_zad18")

    # question_1 = "Podaj adres mailowy do firmy SoftoAI"
    # print(f"\nSearching for answer to: {question_1}")
    # searcher_1 = WebpageSearcher(OPENAI_API_KEY)
    # result_1 = searcher_1.search_for_answer(
    #     question_1,
    #     f"{URL_SEARCH}"
    # )
    # if result_1["found"]:
    #     print(f"Answer found at {result_1['url']}:")
    #     print(result_1["answer"])
    # else:
    #     print(f"Answer not found. Checked URLs: {len(searcher_1.visited_urls)}")
    #     print("Visited URLs:", "\n".join(searcher_1.visited_urls))

    # question_2 = "Jaki jest adres interfejsu webowego do sterowania robotami zrealizowanego dla klienta jakim jest firma BanAN?"
    # print(f"\nSearching for answer to: {question_2}")
    # searcher_2 = WebpageSearcher(OPENAI_API_KEY)
    # result_2 = searcher_2.search_for_answer(
    #     question_2,
    #     f"{URL_SEARCH}"
    # )
    # if result_2["found"]:
    #     print(f"Answer found at {result_2['url']}:")
    #     print(result_2["answer"])
    # else:
    #     print(f"Answer not found. Checked URLs: {len(searcher_2.visited_urls)}")
    #     print("Visited URLs:", "\n".join(searcher_2.visited_urls))

    question_3 = "Jakie dwa certyfikaty jakości ISO otrzymała firma SoftoAI?"
    print(f"\nSearching for answer to: {question_3}")
    searcher_3 = WebpageSearcher(OPENAI_API_KEY)
    result_3 = searcher_3.search_for_answer(
        question_3,
        f"{URL_SEARCH}"
    )
    if result_3["found"]:
        print(f"Answer found at {result_3['url']}:")
        print(result_3["answer"])
    else:
        print(f"Answer not found. Checked URLs: {len(searcher_3.visited_urls)}")
        print("Visited URLs:", "\n".join(searcher_3.visited_urls))