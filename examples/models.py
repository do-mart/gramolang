"""Print OpenAI models based on API key"""

from logging import getLogger, DEBUG, INFO, basicConfig
from datetime import datetime
from tabulate import tabulate

import initialize
from gramolang import OpenAIWrapper


# Logging
getLogger('gramolang.wraipi').setLevel(INFO)
basicConfig(format='%(asctime)s [%(module)s][%(name)s] %(message)s')

api_wrapper = OpenAIWrapper()

models = api_wrapper.client.models.list().data
headers = ('', 'id', 'created', 'owned_by')
sorted_table = (
    (i + 1, model.id, datetime.fromtimestamp(model.created), model.owned_by)
    for i, model in enumerate(sorted(models, key=lambda m: m.id)))

print()
print(f"OpenAI models with API key file '{_initialize.API_KEY_FILE.name}'")
print()
print(tabulate(sorted_table, headers=headers))
