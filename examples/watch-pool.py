"""Watch directory and pool file for autocomplete"""


from logging import getLogger, basicConfig, INFO, DEBUG
from pathlib import Path

import initialize
from gramolang.common import NAME_VERSION as GRAMOLANG_NAME_VERSION
from gramolang.auto import watch_pool_files


# Settings
MODEL = 'gpt-3.5-turbo'     # Default model
MAX_FILES = None            # Maximum number of concurrent files (None for default)
MAX_CHATS = None            # Max. concurrent conversations for each file (None for default)
TIMEOUT = 2 * 60            # Max. time in seconds for one chat completion
RETRIES = 4                 # Number of times to retries on timeout or rate limit
STATUS_DELAY = 60 * 60      # Delay in seconds for printing pool status
LOG_LEVEL = INFO            # Logging level (import from logging)

POOL_DIR = Path(__file__).parent / Path(__file__).stem  # Pool directory


# Logging
getLogger('gramolang').setLevel(LOG_LEVEL)
if LOG_LEVEL is DEBUG:
    basicConfig(format='%(asctime)s [%(module)s][%(name)s] %(message)s')
else:
    basicConfig(format='%(message)s', datefmt='%X')

# Start pool
print(GRAMOLANG_NAME_VERSION)
watch_pool_files(
    root_dir=POOL_DIR, model=MODEL,
    timeout=TIMEOUT, retries=RETRIES,
    max_files=MAX_FILES, max_chats=MAX_CHATS,
    status_delay=STATUS_DELAY)
