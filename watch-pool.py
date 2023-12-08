"""Watch directory and pool file for autocomplete"""

from logging import getLogger, basicConfig, INFO, DEBUG
from pathlib import Path

from gramolang import NAME_VERSION as GRAMOLANG_NAME_VERSION, OpenAIAPIWrapper
from gramolang.auto import watch_pool_files


# API keys
api_key_files = {
    OpenAIAPIWrapper: Path(__file__).parent / '.keys' / 'openai-api-key-uqam'}

# Settings
POOL_DIR = Path(__file__).parent / Path(__file__).stem

STATUS_DELAY = 60 * 60      # Delay in seconds for printing pool status

MODEL = 'gpt-3.5-turbo'     # Default model
MAX_FILES = None            # Maximum number of concurrent files (None for default)
MAX_CONVERSATIONS = None    # Max. concurrent conversations for each file (None for default)
TIMEOUT = 2 * 60            # Max. time in seconds for one chat completion
RETRIES = 4                 # Number of times to retries if rate limit is reached

LOG_LEVEL = INFO            # Logging level (must be imported from logging)

# Logging
getLogger('gramolang').setLevel(LOG_LEVEL)
if LOG_LEVEL is DEBUG:
    basicConfig(
        # format='%(asctime)s [%(name)s] %(message)s',
        format='%(asctime)s [%(module)s][%(name)s] %(message)s')
else:
    basicConfig(format='%(message)s', datefmt='%X')

# Start pool
print(GRAMOLANG_NAME_VERSION)
watch_pool_files(
    root_dir=POOL_DIR, api_key_files=api_key_files, model=MODEL,
    timeout=TIMEOUT, retries=RETRIES,
    max_conversations=MAX_CONVERSATIONS, max_files=MAX_FILES,
    status_delay=STATUS_DELAY)
