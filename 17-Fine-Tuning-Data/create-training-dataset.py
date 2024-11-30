import json

def create_training_json(dataset_content, classification):
    training_data = {
        "messages": [
            {
                "role": "system",
                "content": "Classify the dataset if it is correct or incorrect"
            },
            {
                "role": "user",
                "content": dataset_content
            },
            {
                "role": "assistant",
                "content": classification
            }
        ]
    }
    return json.dumps(training_data, ensure_ascii=False)

def process_dataset_file(input_file, output_file, classification="correct"):
    with open(input_file, 'r', encoding='utf-8') as f_in:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                # Remove whitespace and newlines
                dataset_content = line.strip()
                if dataset_content:  # Skip empty lines
                    # You can modify the classification logic here
                    classification = classification  # Default classification
                    json_line = create_training_json(dataset_content, classification)
                    f_out.write(json_line + '\n')

# Example usage
input_file = "../../../zadanie 17/lab_data/correct.txt"
output_file = "../../../zadanie 17/lab_data/correct_json.jsonl"
process_dataset_file(input_file, output_file, "correct")
input_file = "../../../zadanie 17/lab_data/incorrect.txt"
output_file = "../../../zadanie 17/lab_data/incorrect_json.jsonl"
process_dataset_file(input_file, output_file, "incorrect")