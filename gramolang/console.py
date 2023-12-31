"""
Interactive Console
"""

from typing import TextIO
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from datetime import datetime

from sys import stdin, stdout
import readline
import textwrap

from .common import (
    NAME_VERSION as PACKAGE_NAME_VERSION,
    COMMAND_CHAR, NONE_ARG, NAME_VALUE_SEPS,
    now_delta, write_timedelta, write_error)
from .command import (
    CommandClassError,
    Command, EmptyCommand, UnaryCommand, ToggleCommand,
    Commands)
from .wraipi import APIWrapper
from .chat import (
    Role,
    SystemCommand,
    MaxTokensCommand, TemperatureCommand, TopPCommand, ChoicesCommand,
    TimeoutCommand, RetriesCommand,
    ClearCommand, ResetCommand, ModelCommand,
    Chat)


# Basic helpers
# -------------

def write_backspaces(string: str) -> str: return '\b \b' * len(string)


# Commands
# --------

class MessagesCommand(EmptyCommand):
    """Write all messages with role"""
    NAMES = ('messages', 'mess')

    def __init__(self, *, name=NAMES[0]) -> None:
        super().__init__(name=name)


class InfosCommand(ToggleCommand):
    """Toggle write more information about responses and status."""
    NAMES = ('infos', 'i', 'info')

    def __init__(self, set_value: bool | None = None, name=NAMES[0]) -> None:
        super().__init__(set_value=set_value, name=name)


class RawCommand(ToggleCommand):
    """Toggle write raw response object and other data structures."""
    NAMES = ('raw',)

    def __init__(self, set_value: bool | None = None, name=NAMES[0]) -> None:
        super().__init__(set_value=set_value, name=name)


class WrapCommand(ToggleCommand):
    """Toggle wrap lines."""
    NAMES = ('wrap',)

    def __init__(self, set_value: bool | None = None, name=NAMES[0]) -> None:
        super().__init__(set_value=set_value, name=name)


class WidthCommand(UnaryCommand):
    """Set width for text wrap, write value if no argument."""
    NAMES = ('width',)

    def __init__(self, arg: int | type(NONE_ARG) = NONE_ARG, name=NAMES[0]) -> None:
        if arg is not NONE_ARG: super().__init__(int(arg), name=name)
        else: super().__init__(name=name)


class StopCommand(EmptyCommand):
    """Stop console and return."""
    NAMES = ('stop', 'q', 'quit', 'exit')

    def __init__(self, *, name=NAMES[0]) -> None:
        super().__init__(name=name)


class HelpCommand(EmptyCommand):
    """Write help message."""
    NAMES = ('help', 'h', '?')

    def __init__(self, *, name=NAMES[0]) -> None:
        super().__init__(name=name)


# Main console class
# ------------------

class Console:

    # Name
    NAME: str = 'Interactive Console'

    # Prompt argument for user input
    INPUT_PROMPT: str = '> '

    # Default output file
    INPUT_FILE: TextIO = stdin
    OUTPUT_FILE: TextIO = stdout

    # Internal Constants
    _RESPONSE_TIME_LABEL = 'Time: '  # Label for printing response time
    _INTERVAL = 0.1                  # Refresh interval from printing response time
    _NDIGITS = 2                     # Number of digits for rounding seconds

    def __init__(
            self,
            api_keys: dict[type(APIWrapper): str] | None = None
            ) -> None:

        # Status signal
        self._running: bool = False
        self.stop_signal: bool = False

        # Create client and chat
        self.chat: Chat = Chat(api_keys=api_keys)

        # States variables (see default here)
        self._infos: bool = False   # Write more information about responses
        self._raw: bool = False     # Write raw response completion instance
        self._wrap: bool = False    # Wrap lines to a specific width
        self._width: int = 80       # Width for line break

    @property
    def running(self): return self._running

    # Console writing/printing methods
    # --------------------------------

    def write(self, *args, end: str = '', **kwargs):
        if not self._running: return
        print(*args, **kwargs, end=end, file=self.OUTPUT_FILE, flush=True)

    def write_line(self, *args, **kwargs):
        self.write(*args, **kwargs, end='\n')

    def write_value(self, name: str, value):
        self.write_line(f"{name} {NAME_VALUE_SEPS[0]}", value.__repr__())

    # Inner generic toggle method
    # ---------------------------

    def _toggle(self, name, set_value: bool | None = None):
        attr_name = f"_{name}"
        if set_value is not None: setattr(self, attr_name, set_value)
        else: setattr(self, attr_name, not getattr(self, attr_name))
        self.write_line(f"Toggle {name} =", getattr(self, attr_name))

    # Wrappers for chat commands
    # --------------------------

    def messages(self, role: Role | None = None):
        """Write all messages with role."""
        messages = self.chat.role_messages(role) if role else self.chat.messages
        for m in messages: self.write_line(f"{m.role}: {m.content}")
        self.write_line(
            'No' if len(messages) == 0 else str(len(messages)),
            f"{str(role) + ' ' if role else ''}message(s) in chat")

    def system(self, message: str | None = None):
        """Add system message or write all system messages."""
        if message is not None:
            self.chat.append_system_message(message)
        else:
            self.messages(Role.SYSTEM)

    def max_tokens(self, value: int | None | type(NONE_ARG) = NONE_ARG):
        """Set/print max. number of tokens for chat completion."""
        if value is not NONE_ARG: self.chat.max_tokens = value
        else: self.write_value("Max. tokens", self.chat.max_tokens)

    def temperature(self, value: float | None | type(NONE_ARG) = NONE_ARG):
        """Set/print temperature for chat completion."""
        if value is not NONE_ARG: self.chat.temperature = value
        else: self.write_value("Temperature", self.chat.temperature)

    def top_p(self, value: float | None | type(NONE_ARG) = NONE_ARG):
        """Set/print top probability for chat completion."""
        if value is not NONE_ARG: self.chat.top_p = value
        else: self.write_value(f"Top P.", self.chat.top_p)

    def choices(self, value: int | None | type(NONE_ARG) = NONE_ARG):
        """Set/print number of choices for chat completion."""
        if value is not NONE_ARG: self.chat.choices = value
        else: self.write_value(f"Nb choices (n)", self.chat.choices)

    def timeout(self, value: int | None | type(NONE_ARG) = NONE_ARG):
        """Set/print request timeout for chat completion."""
        if value is not NONE_ARG: self.chat.timeout = value
        else: self.write_value(f"Timeout", self.chat.timeout)

    def retries(self, value: int | type(NONE_ARG) = NONE_ARG):
        """Set/show retries for chat completion."""
        if value is not NONE_ARG: self.chat.retries = int(value)
        else: self.write_value(f"Retries", self.chat.retries)

    def clear(self):
        self.write_line(self.chat.clear.__doc__)
        self.chat.clear()

    def reset(self):
        self.write_line(self.chat.reset.__doc__)
        self.chat.reset()

    def model(self, value: str | None | type(NONE_ARG) = NONE_ARG) -> str:
        if value is not NONE_ARG: self.chat.model(value)
        else: self.write_value("Model", self.chat.model())

    # Other console command
    # ---------------------

    def infos(self, set_value: bool | None = None): self._toggle('infos', set_value)

    def raw(self, set_value: bool | None = None): self._toggle('raw', set_value)

    def wrap(self, set_value: bool | None = None): self._toggle('wrap', set_value)

    def width(self, value: int | type(NONE_ARG) = NONE_ARG):
        if value is not NONE_ARG: self._width = int(value)
        else: self.write_value(f"Width", self._width)

    # Other commands
    # --------------

    def stop(self): self._running = False

    def write_help(self) -> None:
        """Write help message"""
        self.write_line("Commands:")
        for command_class in self.commands:
            self.write_line(self.commands.write_command_help(command_class))

    # Command interface
    # -----------------

    commands = Commands({
        MessagesCommand: messages, SystemCommand: system,
        MaxTokensCommand: max_tokens, TemperatureCommand: temperature,
        TopPCommand: top_p, ChoicesCommand: choices,
        TimeoutCommand: timeout, RetriesCommand: retries,
        ClearCommand: clear, ResetCommand: reset,
        ModelCommand: model,
        InfosCommand: infos, RawCommand: raw,
        WrapCommand: wrap, WidthCommand: width,
        StopCommand: stop,
        HelpCommand: write_help})

    def execute(self, command: type | Command | str):
        self.commands.instance_execute(self, command)

    def parse_execute(self, string: str):
        self.commands.parse_instance_execute(self, string)

    # Main run
    # --------

    def run(self) -> None:

        # Change status:
        self._running = True

        # Startup infos
        self.write_line(f"{PACKAGE_NAME_VERSION} {self.NAME}")
        self.write_line(f"Model: {self.chat.model()}")

        # Executor for completion thread
        with ThreadPoolExecutor(max_workers=1) as executor:

            # Main prompt/command and response loop
            while self._running:

                # Prompt for input
                user_input = input(self.INPUT_PROMPT)

                # Process input for command or message
                if user_input.startswith(COMMAND_CHAR):
                    command = user_input[1:]
                    try: self.parse_execute(command)
                    except CommandClassError:
                        self.write_line("Invalid command name")
                    except Exception as e:
                        self.write_line("Invalid command:", e)
                    continue

                # If not a command, add user message
                self.chat.append_user_message(user_input)

                # Complete request and print timer
                # TODO: Implement completion cancel mechanism
                start = datetime.now()
                future = executor.submit(
                    self.chat.complete, append_completion=True)

                time_delta_line = ''
                while not future.done():
                    time_delta = now_delta(start)
                    self.write(write_backspaces(time_delta_line))
                    time_delta_line = (
                        f"{self._RESPONSE_TIME_LABEL}"
                        f"{write_timedelta(time_delta, self._NDIGITS)}")
                    self.write(time_delta_line)
                    wait((future,), timeout=self._INTERVAL)
                self.write(write_backspaces(time_delta_line))

                if future.exception():
                    self.write_line(write_error(future.exception()))
                    continue
                else:
                    request, response = future.result()

                # Print response
                if self._raw:
                    self.write_line(f"request = {request}")
                    self.write_line(f"response = {response}")
                else:
                    for i, choice in enumerate(response.choices):
                        if len(response.choices) > 1: self.write_line(f"\nChoice {i}:")
                        if self._wrap:
                            for time_delta_line in textwrap.wrap(choice.message.content, self._width):
                                self.write_line(time_delta_line)
                        else: self.write_line(choice.message.content)

                # Print information
                if self._infos:
                    self.write_line(time_delta_line)
                    self.write_line(f"Finish reason: {response.choices[0].finish_reason}")
                    counts = self.chat.messages_counts()
                    self.write_line("Model:", response.model)
                    self.write_line(
                        f"Messages: {len(self.chat.messages)} ("
                        f"{' + '.join(tuple(str(c) + ' ' + r for r, c in counts.items()))})")
                    self.write_line(
                        f"Usage: {response.usage.total_tokens} tokens ("
                        f"{response.usage.prompt_tokens} prompt + "
                        f"{response.usage.completion_tokens} completion)")
