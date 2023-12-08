"""
Wrapper of AI Organizations' API

Layer of abstraction over each organization's API to provide the same interface
for all models.

"""

from typing import Any, Sequence
from logging import getLogger
from pathlib import Path

from openai import OpenAI

from .common import Message, get_file_environ_variable, retry


# Logging
module_logger = getLogger(__name__)


class APIWrapper:
    """Base inheritable class for API wrapper classes"""

    API_KEY_NAME: str = ''
    MODELS: set[str] = set()

    def __init__(
            self,
            api_key: str | None = None, api_key_file: Path | None = None):

        self.logger = module_logger.getChild(self.__class__.__name__)
        self.logger.debug(f"Initializing {self}")

        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = get_file_environ_variable(
                self.API_KEY_NAME, api_key_file)


# TODO: integrate a model function directly in the API?
# TODO: Test the MODELS constant against the available models at runtime
#       (The same list should be re-used)

class OpenAIAPIWrapper(APIWrapper):
    """Open AI's API wrapper"""

    # API key name
    API_KEY_NAME: str = 'OPENAI_API_KEY'

    # Implemented/supported models
    MODELS: set[str] = {'gpt-3.5-turbo', 'gpt-4', 'gpt-4-1106-preview'}

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
            rate_exceptions: Sequence[Exception] | tuple = tuple(),
            timeout_exceptions: Sequence[Exception] | tuple = tuple(),
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
            rate_exceptions=rate_exceptions,
            timeout_exceptions=timeout_exceptions,
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
for apiwrapper in (OpenAIAPIWrapper, AnthropicAPIWrapper):
    for model in apiwrapper.MODELS:
        if model in MODEL_TO_APIWRAPPER:
            raise KeyError(f"Model '{model}' already exists.")
        else:
            MODEL_TO_APIWRAPPER[model] = apiwrapper
