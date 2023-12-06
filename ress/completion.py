from pathlib import Path
#from openai import OpenAI
import openai
from gramolang.common import set_openai_api_key


# Set OpenAI API Key
API_KEY_FILE = Path.home()/'.mz/openai-api-key-uqam'
set_openai_api_key(API_KEY_FILE)

stream = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Say this is a test"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
