import re
from typing import Dict, List, Union

class TextService:
    def adjust_chunk_end(self, text: str, start: int, end: int, limit: int, min_chunk_tokens: int) -> int:
        # Attempt to reduce chunk size until it fits within token limit
        while end > start:
            reduced_end = self.find_previous_newline(text, start, end)
            if reduced_end == end:  # No newline found
                reduced_end = self.find_new_chunk_end(text, start, end)
            
            chunk_text = text[start:reduced_end]
            tokens = self.count_tokens(chunk_text)
            if tokens <= limit and tokens >= min_chunk_tokens:
                print(f"Reducing chunk to previous newline at position {reduced_end}")
                return reduced_end
            
            end = reduced_end
        
        # Return original end if adjustments aren't suitable
        return end

    def find_previous_newline(self, text: str, start: int, end: int) -> int:
        # Find the position of the previous newline character
        newline_pos = text.rfind('\n', start, end)
        if newline_pos == -1:
            return end
        return newline_pos

    def count_tokens(self, text: str) -> int:
        # Count the number of tokens in the text
        return len(text.split())
        
        # Return original end if adjustments aren't suitable
        return end
    
    def split(self, text: str, limit: int) -> List[Dict[str, Union[str, Dict[str, Union[int, Dict[str, List[str]], List[str]]]]]]:
        print(f"Starting split process with limit: {limit} tokens")
        chunks = []
        position = 0
        total_length = len(text)
        current_headers = {}

        while position < total_length:
            print(f"Processing chunk starting at position: {position}")
            chunk_text = text[position:position + limit]
            chunk_end = position + limit
            tokens = self.count_tokens(chunk_text)
            print(f"Chunk tokens: {tokens}")

            headers_in_chunk = self.extract_headers(chunk_text)
            self.update_current_headers(current_headers, headers_in_chunk)

            extracted = self.extract_urls_and_images(chunk_text)
            content = extracted["content"]
            urls = extracted["urls"]
            images = extracted["images"]

            chunks.append({
                "text": content,
                "metadata": {
                    "tokens": tokens,
                    "headers": {**current_headers},
                    "urls": urls,
                    "images": images,
                },
            })

            print(f"Chunk processed. New position: {chunk_end}")
            position = chunk_end

        print(f"Split process completed. Total chunks: {len(chunks)}")
        return chunks

    def find_new_chunk_end(self, text: str, start: int, end: int) -> int:
        # Reduce end position to try to fit within token limit
        new_end = end - ((end - start) // 10)  # Reduce by 10% each iteration
        if new_end <= start:
            new_end = start + 1  # Ensure at least one character is included
        return new_end

    def extract_headers(self, text: str) -> Dict[str, List[str]]:
        headers: Dict[str, List[str]] = {}
        header_regex = r'(^|\n)(#{1,6})\s+(.*)'
        
        for match in re.finditer(header_regex, text):
            level = len(match.group(2))
            content = match.group(3).strip()
            key = f'h{level}'
            
            if key not in headers:
                headers[key] = []
            headers[key].append(content)
            
        return headers

    def update_current_headers(self, current: Dict[str, List[str]], 
                            extracted: Dict[str, List[str]]) -> None:
        for level in range(1, 7):
            key = f'h{level}'
            if key in extracted:
                current[key] = extracted[key]
                self.clear_lower_headers(current, level)

    def clear_lower_headers(self, headers: Dict[str, List[str]], level: int) -> None:
        for l in range(level + 1, 7):
            headers.pop(f'h{l}', None)

    def extract_urls_and_images(text: str) -> Dict[str, Union[str, List[str]]]:
        urls: List[str] = []
        images: List[str] = []
        url_index = 0
        image_index = 0

        def replace_images(match):
            nonlocal image_index
            alt_text, url = match.group(1), match.group(2)
            images.append(url)
            result = f"![{alt_text}]({{$img{image_index}}})"
            image_index += 1
            return result

        def replace_urls(match):
            nonlocal url_index
            link_text, url = match.group(1), match.group(2)
            urls.append(url)
            result = f"[{link_text}]({{$url{url_index}}})"
            url_index += 1
            return result

        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_images, text)
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_urls, content)

        return {
            "content": content,
            "urls": urls,
            "images": images
        }
