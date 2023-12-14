"""
Wrapper of AI Organizations' API

Layer of abstraction over each organization's API to provide the same interface
for all models.

TODO: Change the mechanics for passing keys? Use Enum? API_KEY_NAME?
      All the above?

"""
import logging
from typing import Any, Sequence
from logging import getLogger
from pathlib import Path
from os import environ

from openai import OpenAI, RateLimitError, APITimeoutError

from .common import Message, get_file_variable, retry


# Logging
module_logger = getLogger(__name__)


class APIWrapper:
    """Base inheritable class for API wrapper classes"""

    API_KEY_NAME: str = ''
    API_KEY_NAMES: tuple[str] = ()
    MODELS: set[str] = set()

    def __init__(
            self,
            api_key: str | None = None, api_key_file: Path | None = None):
        self.logger = module_logger.getChild(self.__class__.__name__)
        self.logger.debug(f"Initializing {self}")

        # API Key
        self.api_key_name: str | None = None
        self.api_key: str | None = None
        self.set_api_key(api_key=api_key, api_key_file=api_key_file)

    def set_api_key(
            self,
            api_key: str | None = None, api_key_file: Path | None = None):

        if api_key is not None:
            self.logger.debug(f"Setting API key directly from value")
            self.api_key = api_key
        else:
            if api_key_file is not None:
                for name in self.API_KEY_NAMES + (None,):
                    api_key = get_file_variable(
                        path=api_key_file, name=name, default=None)
                    if api_key:
                        self.logger.debug(
                            f"Setting API key from file with name {name}")
                        self.api_key_name = name
                        self.api_key = api_key
                        break
                if self.api_key is None: raise KeyError(
                    f"Cannot find API key: "
                    f"No variable {' or '.join(self.API_KEY_NAMES)} "
                    f"in file '{api_key_file}'")
            else:
                for name in self.API_KEY_NAMES:
                    self.logger.debug(
                        "Environment variables:\n" +
                        '\n'.join((f"{k}: {v}" for k, v in environ.items())))
                    if name in environ:
                        self.logger.debug(
                            f"Setting API key from environment variable {name}")
                        self.api_key_name = name
                        self.api_key = environ[name]
                        break
                if self.api_key is None: raise Exception(
                    f"Missing API key: no value or key file provided, and "
                    f"no environment variable {' or '.join(self.API_KEY_NAMES)}.")

# TODO: integrate a model function directly in the API?
# TODO: Test the MODELS constant against the available models at runtime?
#       (The same list should be re-used)


class OpenAIWrapper(APIWrapper):
    """Open AI's API wrapper"""

    # API key
    API_KEY_NAME: str = 'OPENAI_API_KEY'
    API_KEY_NAMES: tuple[str] = ('OpenAIWrapper', API_KEY_NAME)

    # Implemented/supported models
    MODELS: set[str] = {'gpt-3.5-turbo', 'gpt-4', 'gpt-4-1106-preview'}

    # Exceptions for chat complete
    RATE_EXCEPTIONS: tuple[Exception] = (RateLimitError,)
    TIMEOUT_EXCEPTIONS: tuple[Exception] = (APITimeoutError,)

    def __init__(
            self,
            api_key: str | None = None, api_key_file: Path | None = None):
        super().__init__(api_key=api_key, api_key_file=api_key_file)
        self.client = OpenAI(api_key=self.api_key)

    def complete_chat(
            self, model: str, messages: list[Message],
            max_tokens: int | None = None, temperature: float | None = None, top_p: float | None = None,
            choices: int | None = None,
            timeout: float | None = None, retries: int = 0,
            base_delay: float = 1, jitter: bool = True, spread_factor: float = 0.5,
            backoff: bool = True, backoff_base: float = 2,
            call_id: str | int | None = None) -> (dict, Any):
        """Chat completion """

        self.logger.debug(f"Complete chat with {self}")

        # TODO: Test all variables, again!

        # Reformat messages in OpenAI format
        messages = [{'role': m.role.value, 'content': m.content} for m in messages]

        # Create request
        request = {'model': model, 'messages': messages}
        if max_tokens is not None: request['max_tokens'] = max_tokens
        if temperature is not None: request['temperature'] = temperature
        if top_p is not None: request['top_p'] = top_p
        if choices is not None: request['n'] = choices

        # Additional log message
        log_message = f"model '{request['model']}'"
        if timeout is not None: log_message += f" {timeout}s timeout"

        # Options
        options = {'max_retries': 0}
        if timeout is not None: options['timeout'] = timeout

        # Create function call with decorator
        @retry(
            retries=retries,
            rate_exceptions=self.RATE_EXCEPTIONS,
            timeout_exceptions=self.TIMEOUT_EXCEPTIONS,
            base_delay=base_delay, jitter=jitter, spread_factor=spread_factor,
            backoff=backoff, backoff_base=backoff_base,
            call_id=call_id, log_messages=(log_message,))
        def retry_create_chat_completion():
            return self.client.with_options(**options).chat.completions.create(**request)

        # Return request and response:
        return request, retry_create_chat_completion()


class AnthropicAPIWrapper(APIWrapper):
    """Anthropic's API wrapper"""

    API_KEY_NAME: str = 'OPENAI_API_KEY'
    API_KEY_NAMES: tuple[str] = ('AnthropicWrapper', API_KEY_NAME)
    MODELS = {'claude', 'claude2'}

    def __init__(
            self,
            api_key: str | None = None, api_key_file: Path | None = None):
        super().__init__(api_key=api_key, api_key_file=api_key_file)
        self.client = OpenAI(api_key=self.api_key)

    def complete_chat(self): pass


# Models
# ------

MODEL_TO_APIWRAPPER: dict[str: APIWrapper] = {}
for api_wrapper in (OpenAIWrapper, AnthropicAPIWrapper):
    for model in api_wrapper.MODELS:
        if model in MODEL_TO_APIWRAPPER:
            raise KeyError(f"Model '{model}' already exists.")
        else:
            MODEL_TO_APIWRAPPER[model] = api_wrapper
