# AI Query Vim Plugin

## Description

This Vim plugin allows you to modify the current file using AI. It sends the content of the buffer, along with your query, to an external AI tool and displays a side-by-side diff of the current buffer and the AI's output.

## Usage

To use the plugin, execute the following command in Vim:

```vim
:Ai YOUR QUERY
```

Where `YOUR QUERY` represents the instructions you want the AI to apply to the current file. For example:

```vim
:Ai Convert this code to Python 3
```

## Installation

Copy the `pack/lainindo/start/ai` directory into your `~/.vim/pack/lainindo/start/` directory.  If the destination directory doesn't exist, create it.

## Configuration

Set the environment variable `GOOGLE_API_KEY` to your API key.

You can configure the following variables in your `.vimrc` file:

*   `g:ai_query_command`: The command to run the external AI tool. Defaults to `python3 <plugin_root>/python/gemini.py`, where `<plugin_root>` is the root directory of the plugin.
*   `g:ai_query_agent_instructions`: Instructions provided to the AI agent to guide its modifications. Defaults to general software development instructions.

Example configuration:

```vim
" Set the command for a custom AI tool
let g:ai_query_command = 'python3 /path/to/your/ai_tool.py'

" Override default instructions
let g:ai_query_agent_instructions = 'You are an expert web developer. Respond to user queries with code only. Do not include any additional text in your response.'
```

## Dependencies

*   **Python:** The plugin relies on an external Python script to interact with the AI. This script requires the following Python library to be installed: `google.genai`.

You can install it using the following command:

```
pip3 install google.genai
```

## Custom AI Tool Example (Python)

Here's a basic example of a custom Python script that you can use to implement your own AI tool, that you can use instead of the default one.  **Note:** This is a placeholder; you'll need to adapt it to interface with a real AI service.

```python
#!/usr/bin/env python3

import argparse
import subprocess
import os

def main():
    parser = argparse.ArgumentParser(description="Query an AI model with a file content.")
    parser.add_argument("-m", "--message", required=True, help="The query message to send to the AI.")
    parser.add_argument("-i", "--input_file", required=True, help="The input file to send to the AI.")
    parser.add_argument("-I", "--instructions", required=True, help="The agent instructions")

    args = parser.parse_args()

    try:
        with open(args.input_file, "r") as f:
            file_content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input_file}")
        exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}")
        exit(1)


    # *** Replace this with your actual AI interaction logic ***
    # This is just a placeholder
    print(f"AI Instructions: {args.instructions}")
    print(f"AI Query: {args.message}")
    print(f"File content: {file_content}")

    # Example: Simple string manipulation as a placeholder
    modified_content = file_content.upper()

    print(modified_content) # Output to stdout


if __name__ == "__main__":
    main()
```

## Troubleshooting

*   **`Error: CLI tool not found or not executable`**: Verify that the path to your AI tool is correct in `g:ai_query_command` and that the tool is executable.
*   **No output from AI**: Check the AI tool for errors and ensure it is printing the modified code to standard output.
*   **Error executing CLI tool**: Examine the output from the AI tool for error messages. Ensure that any API keys or authentication credentials are set up correctly.
