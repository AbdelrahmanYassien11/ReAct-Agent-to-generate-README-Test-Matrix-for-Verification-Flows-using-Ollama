"""
tools.py - LINEAR 4-step pipeline with dual-model architecture
ALL tools use CONTENT MODEL for content generation
Tools receive file paths explicitly from routing model
Step 1: Parse entire spec -> write parsed_spec.json
Step 2: Read file from step 1 -> write test_requirements.json
Step 3: Read file from step 2 -> write test_scenarios.json
Step 4: Read file from step 3 -> write TEST_MATRIX.md
"""

import json
import re
from typing import Dict, Any


def extract_code_block(text):
    # Regular expression to match content between ``` or ```json and ```
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)

    if match:
        return match.group(
            1
        ).strip()  # Return the content without the backticks and any surrounding whitespace
    else:
        # Raise an error if no match is found
        print("No code block found between triple backticks.")
