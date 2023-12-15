"""Print OpenAI models based on API key"""

from logging import getLogger, DEBUG, INFO, basicConfig
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

from gramolang import OpenAIWrapper

api_key_file = Path(__file__).parent / '.keys' / 'openai-api-key-uqam'

# Logging
getLogger('gramolang.wraipi').setLevel(DEBUG)
basicConfig(format='%(asctime)s [%(module)s][%(name)s] %(message)s')

api_wrapper = OpenAIWrapper(api_key_file=api_key_file)

models = api_wrapper.client.models.list().data
headers = ('', 'id', 'created', 'owned_by')
sorted_table = (
    (i + 1, model.id, datetime.fromtimestamp(model.created), model.owned_by)
    for i, model in enumerate(sorted(models, key=lambda m: m.id)))

print()
print(f"OpenAI models with API key file '{api_key_file.name}'")
print()
print(tabulate(sorted_table, headers=headers))
