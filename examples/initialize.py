"""Common initialization for the example modules"""

from pathlib import Path
from sys import path
from shlex import split
from os import environ


# Settings
API_KEY_NAMES = {'OpenAIWrapper'}
API_KEY_FILE = Path(__file__).parent / '.keys'


# Add gramolang package to sys. path
package_dir = Path(__file__).parent.parent
if package_dir not in path: path.insert(1, str(package_dir))

# Load API keys in environment
if not API_KEY_FILE.is_file():
    raise FileNotFoundError(f"API key file doesn't exist: {API_KEY_FILE}")

found_key = {name: False for name in API_KEY_NAMES}
with open(API_KEY_FILE, 'r') as api_key_file:
    for line in api_key_file:
        tokens = split(line, comments=True)
        if not tokens: continue
        elif tokens[0] in API_KEY_NAMES:
            environ[tokens[0]] = tokens[-1]
            found_key[tokens[0]] = True

for name, found in found_key.items():
    if not found:
        raise Exception(f"API key '{name}' not in file: {API_KEY_FILE}")
