from dotenv import load_dotenv
from openai import OpenAI
import requests
import os
import base64
import re
from bs4 import BeautifulSoup
from os.path  import basename
from urllib.parse import urljoin
from markdownify import MarkdownConverter
from markdownify import markdownify as md_convert
import glob

load_dotenv()
api_key = os.getenv("APIkey")
URL_POST = os.getenv("URL_post")
URL = os.getenv("URL_zad10")
ARTICLE = os.getenv("article")
OPENAI_API_KEY = os.getenv("OpenAI_APIkey")

class ImageBlockConverter(MarkdownConverter):
    """
    Create a custom MarkdownConverter that adds descriptions to images and audio files.
    """
    def convert_img(self, el, text, convert_as_inline):
        return super().convert_img(el, text, convert_as_inline) + '\nIMAGE_DESCRIPTION'
    
    def convert_audio(self, el, text, convert_as_inline):
        return super().convert_img(el, text, convert_as_inline) + '\nAUDIO_DESCRIPTION'
    
def md(soup, **options):
    return MarkdownConverter(**options).convert_soup(soup)

def md_custom(soup, **options):
    return ImageBlockConverter(**options).convert_soup(soup)

def parse_webpage(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

def download_files(soup, base_url):
    # Process images
    for image in soup.select("img[src]"):
        src = image["src"]
        # Construct the full URL for relative paths
        lnk = src if src.startswith("http") else urljoin(base_url, src)
        # Extract the filename from the URL
        filename = os.path.basename(lnk)
        try:
            # Download and save the image
            with open(filename, "wb") as f:
                f.write(requests.get(lnk).content)
            print(f"Downloaded {filename}")
        except Exception as e:
            print(f"Failed to download {filename}: {e}")

    # Process audio files
    for audio in soup.find_all('audio'):
        source = audio.find('source')
        if source:
            src = source.get('src')
            if src:
                # Construct the full URL for relative paths
                lnk = src if src.startswith("http") else urljoin(base_url, src)
                # Extract the filename from the URL
                filename = os.path.basename(lnk)
                try:
                    # Download and save the audio file
                    with open(filename, "wb") as f:
                        f.write(requests.get(lnk).content)
                    print(f"Downloaded {filename}")
                except Exception as e:
                    print(f"Failed to download {filename}: {e}")
        else:
            print(f"No source found in audio tag: {audio}")

def scan_folder_for_file(filename, folder_path=None):
    
    if folder_path is None:
        folder_path = os.getcwd()

    if filename:
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            return file_path

def clean_filename(text):
    # Replace spaces with underscores and remove special characters
    clean = re.sub(r'[^a-zA-Z0-9\s_-]', '', text)
    clean = clean.replace(' ', '_').lower()
    return clean

def update_attributes(soup, files_folder_path=None):
    
    # Process all images
    for figure in soup.find_all('figure'):
        # Get the figcaption of the image
        figcaption = figure.find('figcaption')
        figcaption_text = figcaption.get_text() if figcaption else "No caption"

        # Find the img tag inside the figure
        img = figure.find('img')
        if img and 'src' in img.attrs:
            # Get the original filename and extension
            original_path = img['src']
            directory = os.path.dirname(original_path)
            filename, ext = os.path.splitext(original_path)
            file = os.path.basename(original_path)
            
            # Get description from alt text or use 'image'
            if 'alt' in img.attrs:
                description = img['alt']
            else:
                description = get_ai_answer_to_image(
                    f'Opisz przedstawiony obrazek. Co jest na obrazku? Co to za miejsce? Jakie to miasto? Tu jest opis obrazka od autora: {figcaption_text}', 
                    'You are a helpful assistant that is an expert in describing images. Focus on the content of the image. It should be one line text', 
                    image_path=scan_folder_for_file(file, files_folder_path), 
                    image_type=ext)
                
            # Update attributes
            img['alt'] = description
    
    # Process all images not inside figure tags
    for img in soup.find_all('img'):
        if img.parent.name != 'figure' and 'src' in img.attrs:
            # Get the original filename and extension
            original_path = img['src']
            directory = os.path.dirname(original_path)
            filename, ext = os.path.splitext(original_path)
            file = os.path.basename(original_path)
            
            # Get description from alt text or use 'image'
            if 'alt' in img.attrs:
                description = img['alt']
            else:
                description = get_ai_answer_to_image(
                    'Opisz przedstawiony obrazek.',
                    'You are a helpful assistant that is an expert in describing images',
                    image_path=scan_folder_for_file(filename, files_folder_path),
                    image_type=os.path.splitext(original_path)[1]
                )
                
            # Update attributes
            img['alt'] = description
    
    # Process all audio elements
    for audio in soup.find_all('audio'):
        source = audio.find('source')
        if source and 'src' in source.attrs:
            # Get the original filename and extension
            original_path = source['src']
            directory = os.path.dirname(original_path)
            filename, ext = os.path.splitext(original_path)
            file = os.path.basename(original_path)
            
            # Get transcription from track or use default
            track = audio.find('track')
            if track and track.get('src'):
                description = track['src']
            else:
                transcription = speech_to_text(scan_folder_for_file(file, files_folder_path))
                description = f'Transcription of "{original_path}" audio file: "{transcription}"'
            
            # Update attributes
            audio.string = description
    
    return str(soup)
    
def speech_to_text(file_path):
    try:

        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Transcribe the audio file using Whisper API
        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        # Extract the transcription from the response
        transcription = response.text
        return transcription
        
    except Exception as e:
        print(f"Error translating MP3 to text: {e}")
        return None

def save_markdown_file(content, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
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
            model="gpt-4o-mini",
            #model="gpt-4o",
            messages=messages
        )
        
        # Extract the answer from AI response
        ai_answer = response.choices[0].message.content
        return ai_answer
        
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return None
    
# Main program
def main():
    soup = parse_webpage(ARTICLE)
    #download_files(soup, ARTICLE)
    #print(soup)
    soup_updated = update_attributes(soup)
    #print(soup_updated)
    markdown_content = md_convert(soup_updated)
    save_markdown_file(markdown_content, 'article.md')

# Run the program
if __name__ == "__main__":
    main()