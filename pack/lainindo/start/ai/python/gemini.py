#!/usr/bin/env python3

import os
import mimetypes
import argparse
import datetime
import logging
from typing import List

from google import genai
from google.genai import types


GOOGLE_API_KEY_ENV= "GOOGLE_API_KEY"
DEFAULT_INSTRUCTIONS = "You are a helpful assistant"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"


def parse_args():
    p = argparse.ArgumentParser(description="Interact with the Gemini API.")
    p.add_argument('-m', '--message', help='Message(s) to Gemini', action='append', type=str, required=True)
    p.add_argument('-i', '--input', help='Input file(s) to read messages from', action='append', type=str)
    p.add_argument('-M', '--model', help='Gemini model to use', type=str, default=DEFAULT_GEMINI_MODEL)
    p.add_argument('-I', '--instructions', help='Custom instructions for the agent.', type=str, default=DEFAULT_INSTRUCTIONS)
    p.add_argument('-d', '--debug', help='Enable debug logging', action='store_true')
    return p.parse_args()


def now_utc() -> datetime.datetime:
    """Returns the current datetime in UTC."""
    return datetime.datetime.now(datetime.timezone.utc)


def today_str() -> str:
    """Returns the current date as a string in YYYY-MM-DD format with timezone."""
    return now_utc().strftime('%Y-%m-%d %Z')


def current_time_str() -> str:
    """Returns the current time as a string in HH:MM:SS format with timezone."""
    return now_utc().strftime('%H:%M:%S %Z')


def get_setup_message(agent_instructions: str) -> str:
    """Constructs the setup message for the Gemini model."""
    return f"{agent_instructions}. Today is {today_str()}. Current time is {current_time_str()}."


def maybe_remove_prefix(s: str, prefix: str) -> str:
    """Removes the prefix from the string if it exists."""
    return s[len(prefix):] if s.startswith(prefix) else s


def get_response_messages(
    messages: List[str],
    file_paths: List[str] | None = None,
    role_name: str | None = None,
    agent_instructions : str = DEFAULT_INSTRUCTIONS,
    model_name: str = DEFAULT_GEMINI_MODEL,
) -> List[str] | None:
    """
    Retrieves responses from the Gemini API.

    Args:
        messages: A list of strings representing the conversation history and the current question.
                  The last element is assumed to be the current question.
        file_paths: A list of file paths to be uploaded to the Gemini API.
        role_name: An optional role name to be used for identifying messages from a specific role.
                   If provided, messages starting with '{role_name}:' will be treated as model responses.
        agent_instructions: Instructions for the agent, defaults to DEFAULT_INSTRUCTIONS.
        model_name: The name of the Gemini model to use, defaults to DEFAULT_GEMINI_MODEL.

    Returns:
        A list containing the response text from the Gemini API, or None if an error occurred.
    """
    api_key = os.getenv(GOOGLE_API_KEY_ENV) 
    client = genai.Client(api_key=api_key)

    history = messages[:-1]
    question = messages[-1]

    contents = [
        types.Content(
          role="model" if role_name and message.startswith(f'{role_name}:') else "user",
          parts=[types.Part.from_text(
            text=maybe_remove_prefix(message, f'{role_name}:') if role_name else message
          )],
        ) for message in history
    ]

    contents.append(
      types.UserContent(  # UserContent automatically sets role "user"
        parts=[types.Part.from_text(text=question)]
      )
    )

    if file_paths:
        for fpath in file_paths:
            try:
                contents.append(client.files.upload(file=fpath))
            except Exception as e:
                logging.error(f"Failed to upload file {fpath}: {e}")
                return None

    config = types.GenerateContentConfig(
        system_instruction=get_setup_message(agent_instructions),
        response_mime_type= 'text/plain',
        #max_output_tokens= 8192,
    )

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )

        return [response.text]

    except Exception as e:
        logging.exception("Error during Gemini API call: %s", e)  # Use logging.exception to include traceback

    return None


def read_file_contents(path: str) -> str | None:
    """Reads the content of a file and returns it as a string."""
    try:
        with open(path, "r") as file:
            return file.read()
    except FileNotFoundError:
        logging.warning("File not found: %s", path)
    except Exception as e:
        logging.error("Error reading file %s: %s", path, e, exc_info=True)
    return None


def process_input_files(input_files: List[str]) -> tuple[List[str], List[str]]:
    """
    Processes the input files, separating them into files to be uploaded
    and files whose content should be included as text.
    """
    upload_files = []
    text_content = []

    for fpath in input_files:
        mime_type, _ = mimetypes.guess_type(os.path.basename(fpath))
        if mime_type is not None:
            upload_files.append(fpath)
        else:
            # Treat other files as text.
            content = read_file_contents(fpath)
            if content:
                text_content.append(f"```\n{content}\n```")
            else:
                logging.warning(f"Could not read content from {fpath}, skipping.")

    return text_content, upload_files


def main():
    args = parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.WARNING,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    inputs = [m for m in args.message]
    files_to_upload = []

    if args.input:
        text_content, files_to_upload = process_input_files(args.input)
        inputs.extend(text_content)

    output_strings = get_response_messages(
        inputs,
        file_paths=files_to_upload,
        role_name=None,
        model_name=args.model,
        agent_instructions=args.instructions
    )

    if output_strings:
        print(''.join(output_strings))
    else:
        logging.error("No response received from Gemini API.")


if __name__ == "__main__":
    main()
