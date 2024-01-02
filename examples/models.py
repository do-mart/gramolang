"""Print OpenAI models based on an API key"""

from tabulate import tabulate

import initialize
from gramolang import OpenAIWrapper


api_wrapper = OpenAIWrapper()

models = api_wrapper.all_models()
sorted_table = (
    (i + 1, mid, models[mid]['created'], models[mid]['owned_by'])
    for i, mid in enumerate(sorted(models)))
headers = ('', 'id', 'created', 'owned_by')

print()
print(f"OpenAI models with API key file '{initialize.API_KEY_FILE.name}'")
print()
print(tabulate(sorted_table, headers=headers))
