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
value directly, retrieve the key from a file, or from an environment variable.
Since APIs from different organizations can be used interchangeably, a user can
provide multiple keys if he intends to use the APIs of multiple organizations.

### 1. Providing key values directly
Past API keys as `APIWrapper: 'apikeyvalue'` pairs in a `dict`: 

    >>> from gramolang import OpenAIWrapper
    >>> api_keys = {OpenAIWrapper: 'apikeyvalue'}

### 2. Providing keys in a file
When using a file, write the key in the form `name=apikeyvalue` on a single
line. Use either the name of the API wrapper class (default) or the underlying
organisation's API name (both names are stored in the wrapper class tuple
`API_KEY_NAMES`), e.g.:

    # Example of the content of an API key file
    OpenAIWrapper=apikeyvalue

A key file can contain keys for different APIs or these keys can be stored in
different files. Only the first line starting with the key name will be read by
each API wrapper. The package will look for the equal (`=`) sign as the name/value
separator, other characters in the tuple `common.NAME_VALUE_SEPS` or the space
character.

Pass API key files as `APIWrapper: path` pairs in a `dict` where path is a `pathlib.Path`
instance pointing to the file:

    >>> from pathlib import Path
    >>> from gramolang import OpenAIWrapper 
    >>> api_key_files = {OpenAIWrapper: Path('.keys/api-key-file')}

### 3. Accessing keys from the environment
If no key is provided, either directly or with a file, the package will look
into the process environment with `os.environ`. The name of the environment
variable is the same as the name used in the api key file and must equals one
of the names in `API_KEY_NAMES`.

### Errors or exceptions
The package will raise an exception if no key value can be retrieved with one
of the three methods mentioned above. If the methods are used together, and if
a key is provided with more than one method, the `APIWrapper` will use the
first key retrieved in the order above. If a key is retrieved but its value is
invalid, an exception may not be raised until the first call to the underlying
API (e.g. when  trying to complete a conversation for the first time).
