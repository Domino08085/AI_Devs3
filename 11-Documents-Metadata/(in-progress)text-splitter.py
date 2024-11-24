import os
import json
from TextService import TextService

splitter = TextService()

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    
    docs = splitter.split(text, 1000)
    json_file_path = os.path.join(os.path.dirname(file_path), f"{os.path.basename(file_path).replace('.md', '')}.json")
    
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(docs, json_file, indent=2)
    
    chunk_sizes = [doc['metadata']['tokens'] for doc in docs]
    avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes)
    min_chunk_size = min(chunk_sizes)
    max_chunk_size = max(chunk_sizes)
    median_chunk_size = sorted(chunk_sizes)[len(chunk_sizes) // 2]
    
    return {
        'file': os.path.basename(file_path),
        'avgChunkSize': f"{avg_chunk_size:.2f}",
        'medianChunkSize': median_chunk_size,
        'minChunkSize': min_chunk_size,
        'maxChunkSize': max_chunk_size,
        'totalChunks': len(chunk_sizes)
    }

def main():
    # Get all markdown files in the current directory
    directory_path = os.path.dirname(__file__)
    files = [f for f in os.listdir(directory_path) if f.endswith('.md')]
    reports = []

    for file in files:
        file_path = os.path.join(directory_path, file)
        report = process_file(file_path)
        reports.append(report)

    # Print or save the reports as needed
    print(reports)

if __name__ == "__main__":
    main()