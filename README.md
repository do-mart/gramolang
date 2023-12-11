# gramolang
High-level package for using large language models (or _grand modèle de language_, as
one would say in French)


## AI Organizations API Wrappers
The package provides a single interface for accessing each organizations' models
or functionalities. This additional layer of abstraction is implemented with AI
organizations' API wrappers. Each API wrapper (e.g. `OpenAIAPIWrapper`)
inherits from the parent class `APIWrapper`.


## Chats or conversations
The `Chat` class provides a convenient data structure for generating and storing
conversations, and then completing these conversations. This is an additional
layer of abstraction over the API wrappers.


## API keys
AI organizations' APIs requires a key that must be provided before using their
models or making most calls to their interfaces. A user can provide the key
value directly, retrieve the key from a file, or from an environment variable.
Since APIs from different organizations can be used interchangeably, a user can
provide multiple keys if he intends to use the APIs of multiple organizations.

### 1. Providing a key value directly
Past API keys as `APIWrapper: 'apikeyvalue'` pairs in a dictionary: 

    >>> from gramolang import OpenAIAPIWrapper
    >>> api_keys = {OpenAIAPIWrapper: 'apikeyvalue'}

### 2. Providing a key in a file
When using a file instead of the value directly, write the key in the form
`name=apikeyvalue` on a single file line. Use the name stored in the
corresponding `APIWrapper` class in the class property `API_KEY_NAME`:

    >>> from gramolang import OpenAIAPIWrapper 
    >>> OpenAIAPIWrapper.API_KEY_NAME
    'OPENAI_API_KEY'

A key file can contain keys for different APIs or these keys can be stored in
different files. Only the first line starting with the key name will be read by
each API wrapper. The package will look for the equal (`=`) sign as the name/value
separator and any other characters in the tuple `common.NAME_VALUE_SEPS`.

Pass API key files as `APIWrapper: path` pairs where path is a `pathlib.Path`
instance pointing to the file:

    >>> from pathlib import Path
    >>> from gramolang import OpenAIAPIWrapper 
    >>> api_key_files = {OpenAIAPIWrapper: Path('.keys/api-key-file')}

### 3. Providing a key in the environment
If no key is provided either directly or with a file, the package will look
into the process environment with `os.environ`. The name of the environment
variable is the same as the name used in the api key file and must equals to the
`API_KEY_NAME` of the corresponding `APIWrapper` class.

### Errors or exceptions
The package will raise an exception if no key value can be retrieved with one
of the three methods mentioned above. The three methods can be used together. If
a key is provided with more than one method, the `APIWrapper` will use the
first key retrieve in the order above. If a key is retrieved but it is invalid,
the underlying organization's API may not raise an exception until the first
call (e.g. when  trying to complete a conversation for the first time).
