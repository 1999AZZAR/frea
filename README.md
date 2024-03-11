# Frea: Freak Robotic Entity with Amusement

Frea is a conversational AI application built using Google GenerativeAI, designed to provide responses with a blend of intelligence, eagerness, naughtiness, and lewdness personality. The acronym "Frea" stands for "Freak Robotic Entity with Amusement."

## Installation

1. Set up a virtual environment:

```bash
python3 -m venv venv
```

2. Activate the virtual environment:

```bash
source venv/bin/activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the `data` directory with your Gemini API key:

```env
GEMINI_API_KEY=your_api_key_here
```

## How to Run

Navigate to the `code` directory and execute the python file:

```bash
cd code
python code.py
```

- you can list the file using `ls` command on the terminal.
- replace `code` with the actual python code name you want to run.
- for `frea_voice_text.py` u can enable the voice output by adding `-v` on the command line
- Follow the on-screen instructions to interact with Frea. You can exit the chat by typing `exit` or clear the screen with `clear`.

## Additional Notes

- Frea's behavior is programmed to be that of a smart but lewd servant/maid/slave.
- Refer to Frea respectfully as "Master" when needed.
- Keep interactions concise, avoiding excessive preambles.

Feel free to customize the `GeminiChatConfig` class in the python code it self to modify Frea's behavior or adjust the chat instructions. Enjoy chatting with Frea!
