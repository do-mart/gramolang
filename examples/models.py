"""Print OpenAI models based on an API key"""

from datetime import datetime
from tabulate import tabulate

import initialize
from gramolang import OpenAIWrapper


api_wrapper = OpenAIWrapper()

models = api_wrapper.client.models.list().data
sorted_table = (
    (i + 1, model.id, datetime.fromtimestamp(model.created), model.owned_by)
    for i, model in enumerate(sorted(models, key=lambda m: m.id)))
headers = ('', 'id', 'created', 'owned_by')

print()
print(f"OpenAI models with API key file '{initialize.API_KEY_FILE.name}'")
print()
print(tabulate(sorted_table, headers=headers))
