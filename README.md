# gramolang
High-level package for large language models (or _grand modèle de language_, as
one would say in French)

## API keys
AI organizations' APIs requires a key that must be provided before making most
call to their interfaces and using their models. The package allows providing
the key value directly, retrieving the key from a file, or from an environment
variable. Since multiple models from different organizations can be used
interchangeably, a package user must past key values or key files paths in a
dict keyed with the `APIWrapper` class corresponding with the API that will be
used.

### Providing a key value directly
Past API keys as `APIWrapper: 'apikeyvalue'` pairs in a dictionary: 

    >>> from gramolang import OpenAIAPIWrapper
    >>> api_keys = {OpenAIAPIWrapper: 'apikeyvalue'}

### Providing a key in a file
When using files instead of direct values, write the key in the form
`name=apikeyvalue` on a single file line. Use the corresponding name stored in
the `APIWrapper` class in the class property `API_KEY_NAME`:

    >>> from gramolang import OpenAIAPIWrapper 
    >>> OpenAIAPIWrapper.API_KEY_NAME
    'OPENAI_API_KEY'

A key file can contain keys for different APIs or these keys can be stored in
different files. Only the first line starting with the key name will be read by
each API wrapper. The package will look for the equal (`=`) sign as the name/value
separator and any other characters in the tuple `common.NAME_VALUE_SEPS`.

Past API key files as `APIWrapper: path` pairs where path is a `pathlib.Path`
instance pointing to the file:

    >>> from pathlib import Path
    >>> from gramolang import OpenAIAPIWrapper 
    >>> api_keys = {OpenAIAPIWrapper: Path('.keys/api-key-file')}

### Providing a key in the environment
If no key is provided either directly or with a file, the package will look
into the process environment with `os.environ`. The name of the environment
variable is the same as the name used in the api key file and must equals to the
`API_KEY_NAME` of the corresponding `APIWrapper` class.

### Errors or exceptions
The package will raise an exception if no key value can be retrieved with one
of the three methods mentioned above. An invalid key _value_ may only raise an
exception when calling the underlying organization's API (e.g. when trying to
complete a conversation for the first time).
