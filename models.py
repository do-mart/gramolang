from pathlib import Path
from sys import path

import openai

from gramolang.common import set_openai_api_key


# API Key file
API_KEY_FILE = Path.home()/'.mz/openai-api-key-uqam'

# Set OpenAI API Key
set_openai_api_key(API_KEY_FILE)

response = openai.Model.list()
models = {}
for i, item in enumerate(response['data']):
    parts = item['id'].split('-')
    d = models
    for part in parts:
        if part not in d: d[part] = {}
        d = d[part]
    d[item['id']] = i
    print(f"{i}. id: {item['id']}")


def write_iter(title, iterable, depth=0):
    """Write a string with the content of an iterable object.

    If object has a __getitem__ attribute, the value in each key-value pair
    will also be written. The function can self-reenter to print embedded dict
    or sets."""

    pad = "\t"
    buf = f"{pad * depth}{title} ({len(iterable)} items):"
    for i, k in enumerate(iterable):
        if hasattr(iterable, "__getitem__"):
            # if isinstance(iterable, dict):
            v = iterable[k]
            if isinstance(v, dict) or isinstance(v, set):
                buf += "\n" + write_iter(f"{i}. {k}", v, depth + 1)
            else:
                buf += f"\n{pad * (depth + 1)}{i}. {k}: {v}"
        else:
            buf += f"\n{pad * (depth + 1)}{i}. {k}"
    return buf


print()
print(write_iter('models', models))


# def write_table(items, depth=0):
#     pad = "\t\t"
#     buf = pad * depth
#     for key in items:
#         buf += key
#         if len(items[key]) != 0: buf += write_table(items[key], depth + 1)
#         else: buf += '\n'
#     return buf
#
#
# print()
# print(write_table(models))
#
