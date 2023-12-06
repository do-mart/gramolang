"""
Chat Agents Classes Definitions

TODO: Implement optional loging in the agent class?
TODO: Finish testing getting and setting all attribs and complete docstrings
TODO: Also, uniformize the SYMBOLS match sequences (e.g. ESCAPE_CHAT, TOP_P, etc.)
"""

from typing import Any, TextIO
from threading import Lock

import openai

from .common import TEMPERATURE_NAMES, TOP_P_NAMES, retry
from .command import BaseCommand, CommandInterface


# Commands
# --------

class UserCommand(BaseCommand):
    """Append or get user message (i.e. message with user role)."""
    NAMES = ('user', )

    def __init__(self, *args, name=NAMES[0], **kwargs) -> None:
        super().__init__(*args, name=name, **kwargs)


class SystemCommand(BaseCommand):
    """Append or get system message (i.e. message with system role)."""
    NAMES = ('system', 'sys', 'system_role', 'sys_role')

    def __init__(self, *args, name=NAMES[0], **kwargs) -> None:
        super().__init__(*args, name=name, **kwargs)


class CompleteCommand(BaseCommand):
    """Complete chat/conversation and append response as assistant message."""
    NAMES = ('assistant', 'complete')

    def __init__(self, *args, name=NAMES[0], **kwargs) -> None:
        super().__init__(*args, name=name, **kwargs)


class ModelCommand(BaseCommand):
    """Set/get model for chat completion."""
    NAMES = ('model',)

    def __init__(self, *args, name=NAMES[0], **kwargs) -> None:
        super().__init__(*args, name=name, **kwargs)


class MaxTokensCommand(BaseCommand):
    """Set/get maximum number of tokens to generate for chat completion."""
    NAMES = ('max_tokens',)

    def __init__(self, *args, name=NAMES[0], **kwargs) -> None:
        super().__init__(*args, name=name, **kwargs)


class TemperatureCommand(BaseCommand):
    """Set/get sampling temperature for chat completion."""
    NAMES = TEMPERATURE_NAMES

    def __init__(self, *args, name=NAMES[0], **kwargs) -> None:
        super().__init__(*args, name=name, **kwargs)


class TopPCommand(BaseCommand):
    """Set/get top probability mass of tokens to consider."""
    NAMES = TOP_P_NAMES

    def __init__(self, *args, name=NAMES[0], **kwargs) -> None:
        super().__init__(*args, name=name, **kwargs)


class TimeoutCommand(BaseCommand):
    """Set/get Time in seconds before chat completion times out."""
    NAMES = ('timeout',)

    def __init__(self, *args, name=NAMES[0], **kwargs) -> None:
        super().__init__(*args, name=name, **kwargs)


class RetriesCommand(BaseCommand):
    """Set/get additional retries attempts on error."""
    NAMES = ('retries',)

    def __init__(self, *args, name=NAMES[0], **kwargs) -> None:
        super().__init__(*args, name=name, **kwargs)


class ClearCommand(BaseCommand):
    """Clear messages history."""
    NAMES = ('clear',)

    def __init__(self, *args, name=NAMES[0], **kwargs) -> None:
        super().__init__(*args, name=name, **kwargs)


class ResetCommand(BaseCommand):
    """Reset all agent parameters and clear messages history."""
    NAMES = ('reset',)

    def __init__(self, *args, name=NAMES[0], **kwargs) -> None:
        super().__init__(*args, name=name, **kwargs)


# Agents class definitions
# ------------------------

class ChatGPTAgent:

    # Models implemented in Class
    MODELS = ('gpt-4', 'gpt-4-1106-preview', 'gpt-3.5-turbo')

    # Default system message
    SYSTEM_MESSAGE = "You’re a kind helpful assistant"  # Default System Role

    # Exceptions for chat complete
    RATE_EXCEPTIONS = (
        openai.error.RateLimitError, openai.error.ServiceUnavailableError)
    TIMEOUT_EXCEPTIONS = (openai.error.Timeout,)

    # DEPRECATED
    # Management of rate limits for concurrent (threaded) completions
    # locks: dict[str: Lock] = {k: Lock() for k in MODELS}
    # back_levels: dict[str:int] = {k: 0 for k in MODELS}

    # Thread-safe chat completion id/counter (olds value of last call)
    _ccid_counter: int = -1
    _ccid_counter_lock = Lock()

    # Default values for reset attributes
    MODEL = MODELS[0]
    MAX_TOKENS: int | None = None
    TEMPERATURE: float | None = None
    TOP_P: float | None = None
    N: int | None = None
    TIMEOUT: int | None = None
    RETRIES: int = 0

    @classmethod
    def validate_model(cls, value) -> str:
        if value not in cls.MODELS:
            raise Exception(f"Open AI model is invalid or not implemented: {value}")
        return value

    @staticmethod
    def validate_temperature(value) -> float | None:
        if value is None: return None
        else:
            try:
                test = float(value)
                if 0 < test > 2: raise ValueError
            except ValueError:
                raise ValueError(
                    f"Invalid value {value}, temperature must be between 0 and 2")
            return test

    @staticmethod
    def validate_top_p(value) -> float | None:
        if value is None: return None
        else:
            try:
                test = float(value)
                if 0 < test > 1: raise ValueError
            except ValueError:
                raise ValueError(
                    f"Invalid value {value}, top probability (top_p) must be between 0 and 1")
            return test

    @staticmethod
    def validate_n(value) -> int | None:
        if value is None: return None
        else:
            try:
                test = int(value)
                if 0 < test > 255: raise ValueError
            except ValueError:
                raise ValueError(
                    f"Invalid value {value}, number of choices (n) must be between 0 and 255")
            return test

    @staticmethod
    def validate_timeout(value) -> int | None:
        if value is None: return None
        else:
            try:
                test = int(value)
                if not test > 0: raise ValueError
            except Exception:
                raise ValueError(
                    f"Invalid value {value}, timeout seconds must convert to an int > 0")
            return test

    @staticmethod
    def validate_retries(value: int) -> int:
        if value is None: return None
        else:
            try:
                test = int(value)
                if not test >= 0: raise ValueError
            except Exception:
                raise ValueError(
                    f"Invalid value {value}, retries must convert to an int >= 0")
            return test

    def __init__(self, model: str = MODEL) -> None:

        # Check API key and model
        if not openai.api_key:
            raise openai.error.AuthenticationError("No API key provided")

        # Reset attributes
        # ----------------

        self.model = model
        self._max_tokens: int | None = self.MAX_TOKENS
        self._temperature: float | None = self.TEMPERATURE
        self._top_p: float | None = self.TOP_P
        self._n: int | None = self.N

        # Timeout and retries
        self._timeout: int | None = self.TIMEOUT
        self._retries: int = self.RETRIES

        # Messages and completions
        self._messages: list[dict[str: Any]] = []
        self._completions: dict[int: dict] = {}
        self._last_system_message_index: int | None = None
        self._last_user_message_index: int | None = None
        self._last_assistant_message_index: int | None = None

    def clear(self, default_system_message: bool = False) -> None:
        """Clear messages history."""
        self._messages.clear()
        self._completions.clear()
        self._last_system_message_index: int | None = None
        self._last_user_message_index: int | None = None
        self._last_assistant_message_index: int | None = None
        if default_system_message: self.append_system_message()

    def reset(self, default_system_message: bool = False) -> None:
        """Reset all agent parameters and clear messages history."""

        self._model = self.MODEL
        self._max_tokens: int | None = None
        self._temperature: float | None = None
        self._top_p: float | None = None
        self._n: int | None = None

        # Timeout
        self._timeout: int | None = None
        self._retries: int = self.RETRIES

        # Messages and completions
        self._last_system_message_index: int | None = None
        self._last_user_message_index: int | None = None
        self._last_assistant_message_index: int | None = None

        # Clear to complete reset
        self.clear(default_system_message=default_system_message)

    def append_system_message(self, content: str = SYSTEM_MESSAGE) -> None:
        """Append message with system role to messages list."""
        self._messages.append({'role': 'system', 'content': content})
        self._last_system_message_index = len(self._messages) - 1

    def append_user_message(self, content: str) -> None:
        """Append message with user role to messages list."""
        self._messages.append({'role': 'user', 'content': content})
        self._last_user_message_index = len(self._messages) - 1

    def append_assistant_message(self, content: str) -> None:
        """Append message with assistant role to messages list."""
        self._messages.append({'role': 'assistant', 'content': content})
        self._last_assistant_message_index = len(self._messages) - 1

    def append_completion(self, request: dict, response) -> None:
        """Append assistant message from completion response."""
        for i, choice in enumerate(response.choices):
            self._completions[len(self._messages) + 1] = {
                'n': i, 'request': request, 'response': response}
            self.append_assistant_message(choice.message.content)

    @property
    def model(self) -> str:
        """Model to use for chat completion."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        self._model = self.validate_model(value)

    @property
    def max_tokens(self) -> int | None:
        """Maximum number of tokens to generate in the chat completion."""
        return self._max_tokens

    @property
    def temperature(self) -> float | None:
        """Sampling temperature to use between 0 and 2."""
        return self._temperature

    @temperature.setter
    def temperature(self, value: float | None) -> None:
        self._temperature = self.validate_temperature(value)

    @property
    def top_p(self) -> float | None:
        """Top probability mass of tokens to consider."""
        return self._top_p

    @top_p.setter
    def top_p(self, value: float | None) -> None:
        self._top_p = self.validate_top_p(value)

    @property
    def n(self) -> float | None:
        """How many chat completion choices to generate for one request."""
        return self._n

    @n.setter
    def n(self, value: int | None) -> None:
        self._n = self.validate_n(value)

    @property
    def timeout(self) -> int | None:
        """Time in seconds before chat completion times out."""
        return self._timeout

    @timeout.setter
    def timeout(self, value: int | None) -> None:
        self._timeout = self.validate_timeout(value)

    @property
    def retries(self) -> int:
        """Retries attempts on error (total attempts = 1 + retries)"""
        return self._retries

    @retries.setter
    def retries(self, value: int) -> None:
        self._retries = self.validate_retries(value)

    def complete(
            self, model: str | None = None, max_tokens: int | None = None,
            temperature: int | None = None, top_p: int | None = None, n: int | None = None,
            append_completion: bool = True,
            timeout: int | None = None, retries: int | None = None,
            call_id: str | int | None = None, log_file: TextIO | None = None):
        """Chat completion """

        # DEPRECATED
        # Thread-safe chat completion id (CCID)
        # Note: This will be incremented with each completion call, the class
        # attribute must be used for assignment of immutable type (python, wtf).
        # self._ccid_counter_lock.acquire()
        # self.__class__._ccid_counter += 1
        # ccid = self._ccid_counter
        # self._ccid_counter_lock.release()

        # Build request
        if model is None: model = self._model

        request = {'model': model, 'messages': list(self._messages)}

        if max_tokens is not None: request['max_tokens'] = max_tokens

        if temperature is not None:
            request['temperature'] = self.validate_temperature(temperature)
        elif self._temperature is not None:
            request['temperature'] = self._temperature

        if top_p is not None: request['top_p'] = self.validate_top_p(temperature)
        elif self._top_p is not None: request['top_p'] = self._top_p

        if n is not None: request['n'] = self.validate_n(n)
        elif self._n is not None: request['n'] = self._n

        if timeout is not None: timeout = self.validate_timeout(timeout)
        elif self._timeout is not None: timeout = self._timeout
        if timeout: request['request_timeout'] = timeout

        retries = self.validate_retries(retries)
        if retries is None and self._retries is not None: retries = self._retries

        # Response to chat completion
        # response = None

        # Complete with retries and exponential backoff (with custom decorator)
        @retry(
            retries=retries,
            rate_exceptions=self.RATE_EXCEPTIONS,
            timeout_exceptions=self.TIMEOUT_EXCEPTIONS,
            base_delay=1, jitter=True, spread_factor=0.75,
            backoff=True, backoff_base=4,
            call_id=call_id,
            log_messages=(f"model '{model}', {timeout}s timeout",))
        def retry_create_openai_chatcompletion():
            return openai.ChatCompletion.create(**request)
        response = retry_create_openai_chatcompletion()

        # DEPRECATED built-in retry and backoff
        # # Simple customized logger
        # def log(message: str, supp: str | None = None):
        #     # if log_file is None: return
        #     print(
        #         message,
        #         f"{mark(call_id)}[{i}/{retries}][LEV {backoff_level}]",
        #         f"model '{model}', {timeout}s timeout{', ' + supp if supp else ''}",
        #         file=log_file, flush=True)
        #
        # # Complete with retries and exponential backoff
        # BASE_DELAY = 1          # Base delay in seconds between retries
        # JITTER = True           # Jitter delay
        # SPREAD_FACTOR = 0.75    # Jitter spread as a factor of delay (max. 1)
        # BACKOFF = True          # Exponential backoff delay for retries
        # BACKOFF_BASE = 4        # Base for exponential backoff
        #
        # spread = BASE_DELAY * SPREAD_FACTOR
        # backoff_level = 0
        # for i in range(retries + 1):
        #     try:
        #         log('Request for chat completion')
        #         response = openai.ChatCompletion.create(**request)
        #         log('Successfully completed request')
        #         break
        #     except self.RATE_EXCEPTIONS + self.TIMEOUT_EXCEPTIONS as e:
        #         log('Rate or timeout error with request', write_exception(e))
        #         if i == retries: raise e
        #         delay = BASE_DELAY + ((spread * random()) - (spread / 2) if JITTER else 0)
        #         if isinstance(e, self.RATE_EXCEPTIONS):
        #             backoff_level += 1
        #             if BACKOFF: delay *= BACKOFF_BASE ** backoff_level
        #         log(f"Sleep({round(delay, 1)}) and retry")
        #         sleep(delay)
        #     except Exception as e:
        #         log(
        #             'Error (unhandled) with request',
        #             write_error(exception=e, re_raise=True, sep='\n'))
        #         raise e

        # DEPRECATED Previous implementation with common backoff level for each model
        # aid = hex(id(self))
        # for i in range(retries + 1):
        #     delay = DELAY + ((spread * random()) - (spread / 2) if JITTER else 0)
        #     if BACKOFF:
        #         self.locks[model].acquire()
        #         delay *= BASE ** self.back_levels[model]
        #         infos = f"[lev {self.back_levels[model]}] model '{model}', attempt {i}, delay = {round(delay, 1)}s"
        #         print(aid, 'READ', infos, flush=True)
        #         self.locks[model].release()
        #     sleep(delay)
        #     limit_rate = False
        #     try:
        #         response = openai.ChatCompletion.create(**request)
        #         print(aid, 'COMPLETED', infos, flush=True)
        #         break
        #     except self.RATE_EXCEPTIONS + self.TIMEOUT_EXCEPTIONS as e:
        #         print(aid, 'ERROR', f"{e.__class__.__name__}: {e}", infos)
        #         if i == retries: raise e
        #         if isinstance(e, self.RATE_EXCEPTIONS): limit_rate = True
        #     except Exception as e:
        #         raise e
        #     finally:
        #         self.locks[model].acquire()
        #         if limit_rate:
        #             self.back_levels[model] += 1
        #             print(aid, 'RAISE', f"[lev {self.back_levels[model]}]", flush=True)
        #         elif self.back_levels[model] > 0:
        #             self.back_levels[model] -= 1
        #             print(aid, 'LOWER', f"[lev {self.back_levels[model]}]", flush=True)
        #         self.locks[model].release()

        # Add assistant response
        if append_completion: self.append_completion(request, response)

        # Return response
        return request, response

    @property
    def messages(self) -> list: return self._messages

    @property
    def completions(self) -> list: return self._messages

    def last_system_message(self) -> str | None:
        if self._last_system_message_index is not None:
            return self._messages[self._last_system_message_index]['content']
        else:
            return None

    def last_user_message(self) -> str | None:
        if self._last_user_message_index is not None:
            return self._messages[self._last_user_message_index]['content']
        else:
            return None

    def last_assistant_message(self) -> str | None:
        if self._last_assistant_message_index is not None:
            return self._messages[self._last_assistant_message_index]['content']
        else:
            return None

    def last_completion(self) -> dict | None:
        if len(self._completions) > 0:
            return self._completions[list(self._completions.keys())[-1]]
        else:
            return None

    command_interface = CommandInterface({
        UserCommand: append_user_message,
        SystemCommand: append_system_message,
        CompleteCommand: complete,
        ModelCommand: model,
        MaxTokensCommand: max_tokens,
        TemperatureCommand: temperature,
        TopPCommand: top_p,
        TimeoutCommand: timeout,
        RetriesCommand: retries,
        ClearCommand: clear,
        ResetCommand: reset})

    def execute(self, command: type | BaseCommand | str, *args, **kwargs):
        self.command_interface.instance_execute(self, command, *args, **kwargs)

    def parse_execute(self, command: str):
        self.command_interface.instance_parse_execute(self, command)
