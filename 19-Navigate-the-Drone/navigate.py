import json
import os
import sys

from typing import Dict, Callable, List
from PIL import Image


root_folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(root_folder, 'lib'))

from lib.utils import setup_logger
from machine_for_answers import MachineForAnswers

logger = setup_logger(logging_folder=os.path.join(root_folder, 'dane', 'logs'))
SOURCES = os.path.join(root_folder, 'dane', 'sources')
PROCESSED_DATA = os.path.join(root_folder, 'dane', 'processed_data')


TASK_NAME = "webhook"


class MalformedAnswer(Exception):
    pass


def determine_border_size(image_path: str):
    SYSTEM_PROMPT = ("<OBJECTIVE>\n"
                     "You are a robot working in a board game factory. You are going to analyze a board game, which was printed and has to be cut into pieces. "
                     "The board consist of evenly placed squares with white background separated by thick black line. Please tell me, how thick in pixels is the black separating line?"
                     "Return only the JSON without any markdown or comments. Do not precede answer with initial ``` or the word 'json'"
                     "</OBJECTIVE>\n"
                     "<OUTPUT_EXAMPLE>\n"
                     '{"border_thickness": "15"}'
                     "</OUTPUT_EXAMPLE>\n")
    machine = MachineForAnswers()
    return get_json_answer_from_llm(llm_wrapper_to_be_executed=machine.get_ai_answer_to_image, max_attempts=3, question="", system_prompt=SYSTEM_PROMPT, image_path=image_path)

def determine_pieces_count(image_path: str):
    SYSTEM_PROMPT = ("<OBJECTIVE>\n"
                     "You are a robot working in a board game factory. You are going to analyze a board game, which was printed and has to be cut into pieces. "
                     "The board consist of evenly placed squares with white background separated by thick black line. Please tell me, how many fields are on the board? How many columns? How many rows?"
                     "Return only the JSON without any markdown or comments. Do not precede answer with initial ``` or the word 'json'"
                     "</OBJECTIVE>\n"
                     "<OUTPUT_EXAMPLE>\n"
                     '{"pieces_count": "4", "cols_number": "2", "rows_number": "2"}'
                     "</OUTPUT_EXAMPLE>\n")
    machine = MachineForAnswers()
    return get_json_answer_from_llm(llm_wrapper_to_be_executed=machine.get_ai_answer_to_image, max_attempts=3, question="", system_prompt=SYSTEM_PROMPT, image_path=image_path)


def get_json_answer_from_llm(llm_wrapper_to_be_executed: Callable, max_attempts: int, **wrapper_args):
    wrapper_name = getattr(llm_wrapper_to_be_executed, '__name__', 'Unknown')
    attempt = 0
    max_attempts = max_attempts
    try:
        logger.info(f"Will call {wrapper_name} with following arguments: {wrapper_args}")
        answer = llm_wrapper_to_be_executed(**wrapper_args)
        answer_as_json = json.loads(s=answer)
        return answer_as_json
    except json.decoder.JSONDecodeError:
        if attempt <= max_attempts:
            logger.warning(f"Malformed LLM answer: {answer_as_json}")
            attempt += 1
            logger.info(f"Re-trying. Attempt {attempt} of {max_attempts}")

        else:
            raise MalformedAnswer(f"Malformed LLM answer: {answer_as_json}. Reached max retries!")


def cut_board_to_pieces(image_path: str, border_size: int, cols_number: int, rows_number: int):
    pieces = []
    name, ext = os.path.splitext(os.path.basename(image_path))
    img = Image.open(image_path)
    board_width, board_height = img.size
    tile_width = (board_width - (border_size*(cols_number+1))) / cols_number
    tile_height = (board_height - (border_size*(rows_number+1))) / rows_number
    logger.info(f"Tile width is {tile_width}")
    logger.info(f"Tile height is {tile_height}")
    for row in range(rows_number):
        for column in range(cols_number):
            start_x = ((tile_width+border_size)*column)+border_size
            start_y = ((tile_height+border_size)*row)+border_size
            box = (start_x, start_y, start_x+tile_width, start_y+tile_height)
            out = os.path.join(PROCESSED_DATA, f'{name}_row_{row}_col_{column}{ext}')
            pieces.append(out)
            img.crop(box).save(out)
    return pieces


def describe_picture(image_path: str):
    SYSTEM_PROMPT = ("<OBJECTIVE>\n"
                     "You are a blind person assistant. You are getting a simple black and white image, you are going to describe for this person."
                     "Your task is to describe the image using only one word in Polish language. Your answer has to be JSON file. See OUTPUT_EXAMPLE section for details. "
                     "Return only the JSON without any markdown or comments. Do not precede answer with initial ``` or the word 'json'"
                     "</OBJECTIVE>\n"
                     "<OUTPUT_EXAMPLE>\n"
                     "[EXAMPLE A]\n"
                     '{"description": "skały"}\n'
                     '[END OF EXAMPLE]'
                     "[EXAMPLE B]\n"
                     '{"description": "łąka"}\n'
                     '[END OF EXAMPLE]'
                     "</OUTPUT_EXAMPLE>\n"
                     )
    machine = MachineForAnswers()
    logger.info(f"Trying to get description for {image_path}")
    return get_json_answer_from_llm(llm_wrapper_to_be_executed=machine.get_ai_answer_to_image, max_attempts=3, question="Please describe this picture.", system_prompt=SYSTEM_PROMPT, image_path=image_path)


def get_map_description(image_path: str):
    result = []
    border_size = int(determine_border_size(image_path=image_path)["border_thickness"])
    board_details = determine_pieces_count(image_path=image_path)
    cols_number = int(board_details['cols_number'])
    rows_number = int(board_details['rows_number'])
    pieces = cut_board_to_pieces(image_path=image_path, border_size=border_size, cols_number=cols_number, rows_number=rows_number)
    for row in range(rows_number):
        row_content = []
        result.append(row_content)
        for column in range(cols_number):
            appropriate_piece = pieces.pop(0)
            description = describe_picture(image_path=appropriate_piece)
            description = description["description"]
            row_content.append(description)

    logger.info("Got following map description:")
    for row in result:
        logger.info(f"    {row}")
    return result


def extract_only_relevant_part_from_route_description(route_description: str):
    SYSTEM_PROPMT = ("<OBJECTIVE>\n"
                    "You are playing a board game with a kid. "
                    "Kid, which is the user, tells you where does he want to move on a board with four rows and four columns."
                    "Kid may be hesitating, thinking aloud and changing his mind."
                    "Your job is to determine what movements the child would really like to perform."
                    "In the THINKING section explain your way of thinking."
                    "Output format is described in EXAMPLE section."
                    "</OBJECTIVE>\n"
                    "<RULES>\n"
                    "Always return a JSON file with a list of commands."
                    "<RULES>\n"
                    "<THINKING>"
                    "</THINKING>" 
                    "<EXAMPLE>\n"
                    "[EXAMPLE A]\n"
                    "User says: 'I want to move one field right, and then all the way down'\n"
                    'Your response: {"movement": "I want to move one field right, and then all the way down"], '
                    '"thinking": "User said he wants to move one field right, and then all the way down. User did not change his mind."}\n'
                    '[END OF EXAMPLE A]\n'
                    "[EXAMPLE B]\n"
                    "User says: 'I want to move all the way down. Wait! Scratch that! Move one field right, and then all the way down.'\n"
                    'Your response: {"movement": "Move one field right, and then all the way down.", '
                    '"thinking": "User started from upper right field. First user wanted to go down, but changed his mind. \n'
                    'First movement user is sure about is moving one field right. Then user wants to go all the way down."}\n'
                    '[END OF EXAMPLE B]\n'
                    "</EXAMPLE>")
    machine = MachineForAnswers()
    answer = get_json_answer_from_llm(llm_wrapper_to_be_executed=machine.get_ai_answer, max_attempts=3, question=route_description, system_prompt=SYSTEM_PROPMT)
    logger.info(f"This is the relevant part of directions: {answer}")
    return answer["movement"]

def transform_route_description_into_directions(route_description: str):
    filtered_moves = extract_only_relevant_part_from_route_description(route_description=route_description)

    SYSTEM_PROPMT = ("<OBJECTIVE>\n"
                    "You are playing a board game with a kid. "
                    "Kid, which is the user, tells you where does he want to move on a board with four rows and four columns."
                    "Starting point is always the upper left corner of the board."
                    "Your task is to translate movement description into list of command words: UP, DOWN, LEFT, RIGHT."
                    "In the THINKING section explain your way of thinking."
                    "Output format is described in EXAMPLE section."
                    "</OBJECTIVE>\n"
                    "<RULES>\n"
                    "Always return a JSON file with a list of commands."
                    "<RULES>\n"
                    "<THINKING>"
                    "</THINKING>" 
                    "<EXAMPLE>\n"
                    "[EXAMPLE A]\n"
                    "User says: 'I moved one field right, and then all the way down'\n"
                    'Your response: {"movement": ["RIGHT", "DOWN", "DOWN", "DOWN"], '
                    '"thinking": "User started from upper right field. First movement is RIGHT. After this move user is in second column, first row.'
                    ' Now user wants to go all the way down. There are four rows, so possible movements are: DOWN, DOWN, DOWN."}\n'
                    '[END OF EXAMPLE A]\n'
                    "</EXAMPLE>")
    machine = MachineForAnswers()
    answer = get_json_answer_from_llm(llm_wrapper_to_be_executed=machine.get_ai_answer, max_attempts=3, question=route_description, system_prompt=SYSTEM_PROPMT)
    logger.info(f"Following directions were given: {answer}")
    return answer


def translate_map_description_into_json(map_description: List, output_location):
    result = {}
    for row_index, row_content in enumerate(map_description):
        for column_index, entry in enumerate(row_content):
            result[f"{row_index}_{column_index}"] = entry
    logger.info(f"Map was translated to a following dictionary:")
    logger.info(f"{result}")
    with open(output_location, 'w') as output_handle:
        output_handle.write(json.dumps(result))


def get_map_as_json():
    DESCRIPTION_FILE = os.path.join(PROCESSED_DATA, 'map.json')
    if not os.path.exists(DESCRIPTION_FILE):

        image_path = os.path.join(SOURCES, 'mapa_s04e04.png')
        if isinstance(image_path, list):
            image_path = os.path.join(*image_path)
            
        logger.debug(f"Using image path: {image_path}")
        
        # Verify path exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at: {image_path}")

        map_description = get_map_description(image_path=os.path.join(SOURCES, 'mapa_s04e04.png'))
        translate_map_description_into_json(map_description=map_description, output_location=DESCRIPTION_FILE)
    with open(DESCRIPTION_FILE, 'r') as map_handle:
        return json.loads(map_handle.read())


def get_field_description_basing_on_instructions(movement_instructions: List):
    map_description=get_map_as_json()
    row_number=0
    col_number=0
    for instruction in movement_instructions:
        if instruction == "UP":
            row_number = row_number-1
            logger.info(f"Instruction was UP. Now row number is {row_number} and column number is {col_number}")
        elif instruction == "DOWN":
            row_number = row_number+1
            logger.info(f"Instruction was DOWN. Now row number is {row_number} and column number is {col_number}")
        elif instruction == "RIGHT":
            col_number = col_number+1
            logger.info(f"Instruction was RIGHT. Now row number is {row_number} and column number is {col_number}")
        elif instruction == "LEFT":
            col_number = col_number-1
            logger.info(f"Instruction was LEFT. Now row number is {row_number} and column number is {col_number}")
        else:
            raise KeyError(f"Bad instruction: {instruction}")
    try:
        logger.info(f"Destination field is row {row_number}, column {col_number}")
        return map_description[f"{row_number}_{col_number}"]
    except KeyError as e:
        raise ValueError(f"There is no such field - row {row_number}, column: {col_number}")


def navigate(instructions: str) -> str:
    instructions_as_list = transform_route_description_into_directions(instructions)['movement']
    return get_field_description_basing_on_instructions(movement_instructions=instructions_as_list)
