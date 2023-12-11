# gramolang
High-level console and interface for large language models

## API keys
AI organizations API requires an API key that must be provided before using
their models. The package allows providing the key value directly, retrieving the
value from a file, or from an environment variable. Since multiple models from
different organizations can be used interchangeably, key values and key files
paths must past to package call in a dict keyed with the API wrapper class.

**Providing a key value directly**:

    >>> from gramolang.wraipi import OpenAIAPIWrapper
    >>> api_keys = {OpenAIAPIWrapper: 'apikeyvalue'}

When providing a file instead of the key value directly, the key must be writen
in the form `name=value` in the file on a single line. The name of the key is
stored in the API wrapper class in the class property `API_KEY_NAME`:

    >>> from gramolang.wraipi import OpenAIAPIWrapper 
    >>> OpenAIAPIWrapper.API_KEY_NAME
    'OPENAI_API_KEY'

**Providing a key in a file**: A key file can contain keys for different APIs or
these keys can be stored in different files. Only the first line starting with
the key name will be read by each API wrapper. The package will look for equal
(=) sign as the name/value separator or any other characters in the tuple
`common.NAME_ARGUMENTS_SEPS`, ignoring whitespaces and tabulations. The key
file paths must also be past in a dict keyed with the API wrapper class:

    >>> from pathlib import Path
    >>> from gramolang.wraipi import OpenAIAPIWrapper
    >>> path = Path('.keys/api-key-file') 
    >>> api_keys = {OpenAIAPIWrapper: path}

**Providing a key in the environment**: the name of the environment variable
must be equal to `API_KEY_NAME` in the API wrapper class corresponding to the
API of the models that will be used.

The package will raise an exception if the key isn't available. An invalid key
value will only raised an exception when calling the underlying organization's
API.
