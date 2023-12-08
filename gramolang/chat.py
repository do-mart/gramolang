"""
Chat or conversation class

Terminology:
Role: role of a message (e.g. user, human, system, assistant)
Content: content of one message
Message: NamedTuple with message role and content
Assistant message: Message with assistant role
Completion: NamedTuple with choice, request and response instances

"""

from typing import Any, NamedTuple
from logging import getLogger
from pathlib import Path

from openai import RateLimitError, APITimeoutError

from .common import (
    TEMPERATURE_NAMES, TOP_P_NAMES, NONE_ARG,
    Role, Message)
from .wraipi import APIWrapper, MODEL_TO_APIWRAPPER
from .command import (
    BaseCommand, BaseEmptyCommand, BaseUnaryCommand, BaseUnaryRequiredCommand,
    Commands)


# Logging
module_logger = getLogger(__name__)


# Types
# -----

class Completion(NamedTuple):
    choice: int
    request: dict
    response: Any


# Commands
# --------

class UserCommand(BaseUnaryRequiredCommand):
    """Append user message (i.e. message with user role)."""
    NAMES = ('user', )

    def __init__(self, arg: str, name=NAMES[0]) -> None:
        super().__init__(str(arg), name=name)


class SystemCommand(BaseUnaryCommand):
    """Append system message (i.e. message with system role)."""
    NAMES = ('system', 'sys', 'system_role', 'sys_role')

    def __init__(self, arg: str | None = None, name=NAMES[0]) -> None:
        if arg is not None: super().__init__(str(arg), name=name)
        else: super().__init__(name=name)


class CompleteCommand(BaseCommand):
    """Complete chat/conversation and append response as assistant message."""
    NAMES = ('assistant', 'complete')

    def __init__(self, *args, name=NAMES[0], **kwargs) -> None:
        super().__init__(*args, name=name, **kwargs)


class MaxTokensCommand(BaseUnaryCommand):
    """Set/get maximum number of tokens to generate for chat completion."""
    NAMES = ('max_tokens', 'max_token')

    def __init__(
            self, arg: int | None | type(NONE_ARG) = NONE_ARG,
            name=NAMES[0]) -> None:
        if not (arg is None or arg is NONE_ARG): arg = int(arg)
        super().__init__(arg, name=name)


class TemperatureCommand(BaseUnaryCommand):
    """Set/get sampling temperature for chat completion."""
    NAMES = TEMPERATURE_NAMES

    def __init__(
            self, arg: float | None | type(NONE_ARG) = NONE_ARG,
            name=NAMES[0]) -> None:
        if not (arg is None or arg is NONE_ARG): arg = float(arg)
        super().__init__(arg, name=name)


class TopPCommand(BaseUnaryCommand):
    """Set/get top probability mass of tokens to consider."""
    NAMES = TOP_P_NAMES

    def __init__(
            self, arg: float | None | type(NONE_ARG) = NONE_ARG,
            name=NAMES[0]) -> None:
        if not (arg is None or arg is NONE_ARG): arg = float(arg)
        super().__init__(arg, name=name)


class ChoicesCommand(BaseUnaryCommand):
    """Set/get top probability mass of tokens to consider."""
    NAMES = ('choices',)

    def __init__(
            self, arg: int | None | type(NONE_ARG) = NONE_ARG,
            name=NAMES[0]) -> None:
        if not (arg is None or arg is NONE_ARG): arg = int(arg)
        super().__init__(arg, name=name)


class TimeoutCommand(BaseUnaryCommand):
    """Set/get time in seconds before chat completion times out."""
    NAMES = ('timeout',)

    def __init__(
            self, arg: int | None | type(NONE_ARG) = NONE_ARG,
            name=NAMES[0]) -> None:
        if not (arg is None or arg is NONE_ARG): arg = round(float(arg))
        super().__init__(arg, name=name)


class RetriesCommand(BaseUnaryCommand):
    """Set/get additional retries attempts on error."""
    NAMES = ('retries',)

    def __init__(
            self, arg: int | type(NONE_ARG) = NONE_ARG, name=NAMES[0]) -> None:
        if arg is not NONE_ARG: super().__init__(int(arg), name=name)
        else: super().__init__(name=name)


class ClearCommand(BaseEmptyCommand):
    """Clear messages history."""
    NAMES = ('clear',)

    def __init__(self, *, name=NAMES[0]) -> None:
        super().__init__(name=name)


class ResetCommand(BaseEmptyCommand):
    """Reset all agent parameters and clear messages history."""
    NAMES = ('reset',)

    def __init__(self, *, name=NAMES[0]) -> None:
        super().__init__(name=name)


class ModelCommand(BaseUnaryCommand):
    """Set/get model for chat completion."""
    NAMES = ('model',)

    def __init__(
            self, arg: str | None | type(NONE_ARG) = NONE_ARG,
            name=NAMES[0]) -> None:
        if not (arg is None or arg is NONE_ARG): arg = str(arg)
        super().__init__(arg, name=name)


# Agents class definitions
# ------------------------

class Chat:
    """Chat or conversation"""

    # Models implemented in Class
    MODELS = ('gpt-3.5-turbo', 'gpt-4', 'gpt-4-1106-preview')

    # Default system message
    SYSTEM_MESSAGE = "You’re a kind helpful assistant"  # Default System Role

    # Exceptions for chat complete
    RATE_EXCEPTIONS: tuple[Exception] = (RateLimitError,)
    TIMEOUT_EXCEPTIONS: tuple[Exception] = (APITimeoutError,)

    # Default values for reset attributes
    MAX_TOKENS: int | None = None       # 1, 2, 3, ..., ? (tokens) | None
    TEMPERATURE: float | None = None    # 0 <= Value <= 2 | None
    TOP_P: float | None = None          # 0 <= Value <= 1 | None
    CHOICES: int | None = None          # 1, 2, 3, ... | None
    TIMEOUT: int | None = None          # 0, 1, 2, ... (seconds) | None
    RETRIES: int = 0                    # -1 (infinite retries), 0, 1, 2, ...

    def __init__(
            self,
            api_keys: dict[type(APIWrapper): str] | None = None,
            api_key_files: dict[type(APIWrapper): Path] | None = None
            ) -> None:

        # Logging
        self.logger = module_logger.getChild(self.__class__.__name__)
        self.logger.debug(f"Initializing {self}")

        # APIs Keys and Wrappers
        self._api_keys: dict[type(APIWrapper): str] = (
            {} if api_keys is None else api_keys)
        self._api_keys_files: dict[type(APIWrapper): str] = (
            {} if api_key_files is None else api_key_files)
        self._api_wrappers: dict[type(APIWrapper): APIWrapper] = {}

        # Current APIWrapper and Model
        self._api_wrapper: APIWrapper | None = None
        self._model: str | None = None

        # Reset attributes
        # ----------------

        self.max_tokens: int | None = self.MAX_TOKENS
        self.temperature: float | None = self.TEMPERATURE
        self.top_p: float | None = self.TOP_P
        self.choices: int | None = self.CHOICES

        # Timeout and retries
        self.timeout: int | None = self.TIMEOUT
        self.retries: int = self.RETRIES

        # Messages and completions
        self.messages: list[Message] = []
        self.completions: list[Completion] = []
        self.last_system_message_index: int | None = None
        self.last_user_message_index: int | None = None
        self.last_assistant_message_index: int | None = None

    def clear(self, default_system_message: bool = False) -> None:
        """Clear messages history."""

        self.logger.debug(f"Clear {self}")

        self.messages.clear()
        self.completions.clear()
        self.last_system_message_index: int | None = None
        self.last_user_message_index: int | None = None
        self.last_assistant_message_index: int | None = None
        if default_system_message: self.append_system_message()

    def reset(self, default_system_message: bool = False) -> None:
        """Reset all agent parameters and clear messages history."""

        self.logger.debug(f"Reset {self}")

        self.max_tokens: int | None = self.MAX_TOKENS
        self.temperature: float | None = self.TEMPERATURE
        self.top_p: float | None = self.TOP_P
        self.choices: int | None = self.CHOICES

        # Timeout
        self.timeout: int | None = self.TIMEOUT
        self.retries: int = self.RETRIES

        # Messages and completions
        self.last_system_message_index: int | None = None
        self.last_user_message_index: int | None = None
        self.last_assistant_message_index: int | None = None

        # Clear to complete reset
        self.clear(default_system_message=default_system_message)

    def model(self, value: str | None | type(NONE_ARG) = NONE_ARG) -> str:
        """Set model and instantiate API wrapper (if necessary) or return model."""

        if value is None: self._model = None
        if value is None or value is NONE_ARG: return self._model
        if value not in self.MODELS:
            raise Exception(
                f"Model for chat completion is invalid or not implemented: {value}")

        # Instantiate/set API wrapper and model
        api_wrapper_class = MODEL_TO_APIWRAPPER[value]
        if api_wrapper_class not in self._api_wrappers:
            self._api_wrapper = api_wrapper_class(
                api_key=self._api_keys.get(api_wrapper_class, None),
                api_key_file=self._api_keys_files.get(api_wrapper_class, None))
            self._api_wrappers[api_wrapper_class] = self._api_wrapper
        self._model = value
        return self._model

    def append_system_message(self, content: str = SYSTEM_MESSAGE) -> None:
        """Append message with system role to messages list."""
        self.messages.append(Message(Role.SYSTEM, content))
        self.last_system_message_index = len(self.messages) - 1

    def append_user_message(self, content: str) -> None:
        """Append message with user role to messages list."""
        self.messages.append(Message(Role.USER, content))
        self.last_user_message_index = len(self.messages) - 1

    def append_assistant_message(self, content: str) -> None:
        """Append message with assistant role to messages list."""
        self.messages.append(Message(Role.ASSISTANT, content))
        self.last_assistant_message_index = len(self.messages) - 1

    def append_completion(self, request: dict, response) -> None:
        """Append assistant message from completion response."""
        for i, choice in enumerate(response.choices):
            self.completions.append(Completion(i, request, response))
            self.append_assistant_message(choice.message.content)

    def role_messages(self, role: Role) -> tuple[Message]:
        """Return tuple of messages for role"""
        return tuple(
            Message(m.role, m.content)
            for m in self.messages if m.role == role)

    def messages_counts(self):
        """"Calculate and return dictionary with counts for each message type"""
        counts = {role: 0 for role in Role}
        for m in self.messages: counts[m.role] += 1
        return counts

    # DEPRECATED
    # def last_user_message(self) -> str | None:
    #     if self._last_user_message_index is not None:
    #         return self.messages[self._last_user_message_index]['content']
    #     else:
    #         return None

    # DEPRECATED
    # def last_system_message(self) -> str | None:
    #     if self._last_system_message_index is not None:
    #         return self.messages[self._last_system_message_index]['content']
    #     else:
    #         return None

    def last_assistant_message(self) -> str | None:
        if self.last_assistant_message_index is not None:
            return self.messages[self.last_assistant_message_index].content
        else:
            return None

    def last_completion(self) -> Completion | None:
        if len(self.completions) > 0: return self.completions[-1]
        else: return None

    # DEPRECATED
    # @staticmethod
    # def validate_temperature(value) -> float | None:
    #     if value is None: return None
    #     else:
    #         try:
    #             test = float(value)
    #             if 0 < test > 2: raise ValueError
    #         except ValueError:
    #             raise ValueError(
    #                 f"Invalid value {value}, temperature must be between 0 and 2")
    #         return test

    # DEPRECATED
    # @staticmethod
    # def validate_top_p(value) -> float | None:
    #     if value is None: return None
    #     else:
    #         try:
    #             test = float(value)
    #             if 0 < test > 1: raise ValueError
    #         except ValueError:
    #             raise ValueError(
    #                 f"Invalid value {value}, top probability (top_p) must be between 0 and 1")
    #         return test

    # DEPRECATED
    # @staticmethod
    # def validate_n(value) -> int | None:
    #     if value is None: return None
    #     else:
    #         try:
    #             test = int(value)
    #             if 0 < test > 255: raise ValueError
    #         except ValueError:
    #             raise ValueError(
    #                 f"Invalid value {value}, number of choices (n) must be between 0 and 255")
    #         return test

    # DEPRECATED
    # @staticmethod
    # def validate_timeout(value) -> int | None:
    #     if value is None: return None
    #     else:
    #         try:
    #             test = int(value)
    #             if not test > 0: raise ValueError
    #         except Exception:
    #             raise ValueError(
    #                 f"Invalid value {value}, timeout seconds must convert to an int > 0")
    #         return test

    # DEPRECATED
    # @staticmethod
    # def validate_retries(value: int) -> int:
    #     if value is None: return None
    #     else:
    #         try:
    #             test = int(value)
    #             if not test >= 0: raise ValueError
    #         except Exception:
    #             raise ValueError(
    #                 f"Invalid value {value}, retries must convert to an int >= 0")
    #         return test

    def complete(
            self, append_completion: bool = True,
            call_id: str | int | None = None):
        """Chat completion """

        self.logger.debug(f"Complete {self}")

        # Call API wrapper complete chat method
        request, response = self._api_wrapper.complete_chat(
            model=self._model, messages=self.messages,
            max_tokens=self.max_tokens, temperature=self.temperature, top_p=self.top_p,
            choices=self.choices,
            timeout=self.timeout, retries=self.retries,
            rate_exceptions=self.RATE_EXCEPTIONS,
            timeout_exceptions=self.TIMEOUT_EXCEPTIONS,
            call_id=call_id)

        # Add assistant response
        if append_completion: self.append_completion(request, response)

        # Return response
        return request, response

    commands = Commands({
        UserCommand: append_user_message, SystemCommand: append_system_message,
        CompleteCommand: complete,
        MaxTokensCommand: 'max_tokens', TemperatureCommand: 'temperature',
        TopPCommand: 'top_p',
        TimeoutCommand: 'timeout', RetriesCommand: 'retries',
        ClearCommand: clear, ResetCommand: reset,
        ModelCommand: model})

    def execute(self, command: type | BaseCommand | str):
        self.commands.instance_execute(self, command)

    def parse_execute(self, string: str):
        self.commands.parse_instance_execute(self, string)
