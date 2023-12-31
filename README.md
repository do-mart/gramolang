# gramolang
High-level package for using large language models (or _grand modèle de language_, as
one would say in French).


## AI Organizations' API Wrapper
The package provides a single interface for accessing each organizations' models
or functionalities. This additional layer of abstraction is implemented with a
wrapper class for each AI organizations' API (e.g. `OpenAIWrapper`). API
wrappers inherit from the parent class `APIWrapper`.


## Chat or conversation
The `Chat` class provides a convenient data structure for generating and storing
conversations, and then completing these conversations. This is an additional
layer of abstraction over the API wrappers.


## API keys
AI organizations' APIs require a key that must be provided before using their
models or making most calls to their interfaces. A user can provide the key
value in an environment variable (preferred approach) or directly as an
argument. Note that multiple keys must be provided when in order to use the
APIs from different organizations.

### 1. Providing a key in the environment
The preferred approach is to provide the key as an environment variable with
`os.environ`. The name of the environment variable must be the name of the API
wrapper class or the organisation's API key name (if existing). Looked-up names
are stored in the API wrapper class tuple `API_KEY_NAMES`.

```python
# Example of providing an API key in the environment
import os
os.environ['OpenAIWrapper'] = 'apikeyvalue'
```

```python
# Using the organisation's API key name works as well
import os
os.environ['OPENAI_API_KEY'] = 'apikeyvalue'
```


### 2. Providing a key value directly
A key can be also be provided as an initialization argument to the wrapper
class (e.g. for testing or debugging purposes, or to override a default
environment key):

```python
from gramolang import OpenAIWrapper
api_wrapper = OpenAIWrapper(api_key='apikeyvalue')
```

Higher-level classes or functions allow providing multiple keys to use different
organizations API. In that case, pass the keys as `APIWrapper: 'apikeyvalue'`
pairs in a `dict`:

```python
from gramolang import OpenAIWrapper, Chat
api_keys = {OpenAIWrapper: 'apikeyvalue'}
chat = Chat(api_keys=api_keys)
```


### Errors or exceptions
The package will raise an exception if no key value can be retrieved with one
of the two methods mentioned above. If a key is provided directly and in the
environment, the direct value will be used. If a key is retrieved but its value
is invalid, an exception may not be raised until the first call to the
underlying API (e.g. when  trying to complete a conversation for the first
time).



## Examples
The `example` directory contains example scripts for specific package
functionalities:

- `models.py`: Simple script to retrieve OpenAI models based on an API key,
- `console`: Unix shell executable for the interactive console
- `complete`: Unix shell executable for autocompleting a file using the
  `auto.complete_file()` function.
- `watch-pool.py`: Script to watch directory and pool files for autocomplete 
  using the `auto.watch_pool_files()` function.

The script `initialize.py` provides common initialization features for the
other scripts: adding the `gramolang` package directory in `sys.path` and load
API keys in the environment based on values stored in a file.