# Frea - Freak Robotic Entity with Amusement

## Overview

Frea is an interactive terminal-based chat application powered by Google's generative AI, designed to provide seamless user interactions with advanced natural language processing capabilities. This application offers a variety of features, including multi-line input, special commands, and a customizable loading animation.

## Features

- **Interactive Chat Interface**: Engage in dynamic conversations with a generative AI model.
- **Customization**: Configure API keys, loading styles, and instruction files via `config.ini`.
- **Special Commands**: Use commands like `exit`, `clear`, `reset`, `print`, `reconfigure`, and `help`.
- **Multi-Line Input**: Easily handle multi-line user inputs.
- **Loading Animations**: Enjoy visually appealing loading animations while waiting for responses.
- **Safety Settings**: Ensure content safety with predefined thresholds for harmful content categories.
- **Conversation Log**: Save conversation logs to a file.

## Setup

### Prerequisites

- Python 3.8 or later
- Required Python packages listed in `requirements.txt`

### Installation

1. **Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configuration**:
    - On the first run, the application will prompt for the API key, loading style, and instruction file path.
    - These settings will be saved in a `config.ini` file for future use.

## Usage

### Running the Application

To start the Frea application, run:

```bash
python frea.py
```

### Special Commands

- **exit**: Exit the application.
- **clear**: Clear the terminal screen.
- **reset**: Reset the chat session.
- **print**: Save the conversation log to a file.
- **reconfigure**: Reconfigure the settings.
- **help**: Display help information.

### Example Interaction

Upon running the application, you will see a prompt to enter your message:

```plaintext
╭─ User
╰─> Hello, how are you?
```

The application will respond after processing your input, showing a loading animation in the meantime.

### Multi-Line Input

To enter multi-line messages, end each line with a backslash (`\`):

```plaintext
╭─ User
╰─> This is a multi-line \
input example.
```

### Running Subprocess Commands

You can run system commands by prefixing them with `run `:

```plaintext
╭─ User
╰─> run ls -la
```

## Configuration

### Initial Configuration

On the first run, the application will guide you through creating a `config.ini` file:

```plaintext
╭─ Frea
╰─> No Configuration found. Creating configuration file.
Enter the API key: your_api_key_here
Enter the loading style (e.g., L1): L1
Enter the path to the instruction file: /path/to/instruction_file.txt
Configuration saved successfully!
```

### Reconfiguration

To update the configuration at any time, use the `reconfigure` command within the application.

## Developer Notes

### Code Structure

- **Color**: Contains ANSI escape codes for terminal colors.
- **GeminiChatConfig**: Handles configuration, API initialization, and command processing.
- **GeminiChat**: Main class to run the chat application.

### Functions

- **cursor_hide()**: Hides the terminal cursor.
- **cursor_show()**: Shows the terminal cursor.
- **remove_emojis(text)**: Removes emojis from text.
- **run_subprocess(command)**: Executes a system command.
- **generate_chat()**: Main loop to handle user input and generate AI responses.

### Safety Settings

The application includes predefined safety settings to block harmful content categories:

- Harassment
- Hate Speech
- Sexually Explicit
- Dangerous Content

These settings can be adjusted in the `gemini_safety_settings` method.

## demo

[![asciicast](https://asciinema.org/a/WBjtnAb4HIPa2w3oMiIJsfeB1.svg)](https://asciinema.org/a/WBjtnAb4HIPa2w3oMiIJsfeB1)

> note:
> you can incorporate frea to your bash terminal by doing [this step](alias.md).

---

By following this README, you should be able to set up, configure, and run the Frea application seamlessly. Enjoy interacting with your AI chat assistant!
