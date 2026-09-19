import os
import re

def fix():
    with open("services/validation.py", "r", encoding="utf-8") as f:
        text = f.read()
    
    text = text.replace('"{user_str}"', "'{user_str}'")
    text = text.replace('"{extracted_str}"', "'{extracted_str}'")
    
    with open("services/validation.py", "w", encoding="utf-8") as f:
        f.write(text)

fix()
