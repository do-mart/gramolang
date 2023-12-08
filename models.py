from pathlib import Path
from datetime import datetime
from tabulate import tabulate

from gramolang import OpenAIAPIWrapper

api_key_file = 'openai-api-key-uqam'
api_wrapper = OpenAIAPIWrapper(
    api_key_file=Path.home()/'.mz'/api_key_file)

models = api_wrapper.client.models.list().data
headers = ('', 'id', 'created', 'owned_by')
sorted_table = (
    (i + 1, model.id, datetime.fromtimestamp(model.created), model.owned_by)
    for i, model in enumerate(sorted(models, key=lambda m: m.id)))

print()
print(f"OpenAI models with API key '{api_key_file}'")
print()
print(tabulate(sorted_table, headers=headers))
