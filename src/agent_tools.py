import re
import subprocess
import wikipediaapi
from color import Color
import os
import shutil
import glob

# Wikipedia lookup tool
def wiki(query, sentences=3):
    wiki_wiki = wikipediaapi.Wikipedia(language='en', user_agent='frea-tools/1.0')
    page = wiki_wiki.page(query)
    if not page.exists():
        return f"No Wikipedia page found for '{query}'."
    summary = page.summary or ''
    sentences_list = re.split(r'(?<=[\.!?]) +', summary)
    selected = sentences_list[:sentences]
    return ' '.join(selected)

# Calculator tool
def calc(expression):
    try:
        expr = expression.replace('^', '**')
        result = eval(expr, {'__builtins__': None}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Calculation error: {e}"

# Vim editor tool
def vim(file_path):
    try:
        subprocess.run(['vim', file_path])
        return f"Opened vim for {file_path}"
    except Exception as e:
        return f"Error opening vim: {e}"

# File operation tools
def ls(path='.'):  # List directory contents
    try:
        for name in os.listdir(path):
            full = os.path.join(path, name)
            if os.path.isdir(full):
                print(f"{Color.LIGHTBLUE}{name}/ {Color.ENDC}")
            else:
                print(f"{Color.LIGHTGREEN}{name}{Color.ENDC}")
        return ''
    except Exception as e:
        return f"ls error: {e}"

def cat(file_path):  # Show full file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"cat error: {e}"

def head(file_path, lines=10):  # Show first N lines
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = []
            for i, line in enumerate(f, 1):
                if i > lines:
                    break
                content.append(line.rstrip())
            return '\n'.join(content)
    except Exception as e:
        return f"head error: {e}"

def tail(file_path, lines=10):  # Show last N lines
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
            return '\n'.join([line.rstrip() for line in content[-lines:]])
    except Exception as e:
        return f"tail error: {e}"

def grep(pattern, path='.'):  # Search regex in files
    try:
        result = []
        for root, dirs, files in os.walk(path):
            for fname in files:
                file_path = os.path.join(root, fname)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, 1):
                        if re.search(pattern, line):
                            result.append(f"{Color.LIGHTBLUE}{file_path}:{i}:{Color.ENDC} {line.rstrip()}")
        return '\n'.join(result)
    except Exception as e:
        return f"grep error: {e}"

def write_file(file_path, content):  # Overwrite file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Written to {file_path}"
    except Exception as e:
        return f"write_file error: {e}"

def append_file(file_path, content):  # Append to file
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"Appended to {file_path}"
    except Exception as e:
        return f"append_file error: {e}"

def delete_file(file_path):  # Delete a file
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return f"Deleted {file_path}"
        else:
            return f"File not found: {file_path}"
    except Exception as e:
        return f"delete_file error: {e}"

def move(src, dst):  # Move or rename file
    try:
        shutil.move(src, dst)
        return f"Moved {src} -> {dst}"
    except Exception as e:
        return f"move error: {e}"

def copy(src, dst):  # Copy file
    try:
        shutil.copy2(src, dst)
        return f"Copied {src} -> {dst}"
    except Exception as e:
        return f"copy error: {e}"
