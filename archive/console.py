"""
Interactive Console
"""

# TODO: Change to use command interface
# TODO: Help function with commands
# TODO: Fix the choice 0 prompt that appears everywhere

from threading import Thread, Event
from datetime import datetime, timedelta
import textwrap

from gramolang import NAME as PACKAGE_NAME, __version__
from common import TOP_P_NAMES, TEMPERATURE_NAMES, COMMAND_CHAR, parse_str_to_bool
from command import split_command
from chat import Chat

# Module name
NAME = 'Interactive Console'

# Default Model Properties (change to set initial values)
# Note: None value won't set the property and API's default will be used
TEMPERATURE: int | None = None  # Default temperature
TOP_P: int | None = None        # Top probability sampling for nucleus
N: int | None = None            # Number of choices

# Default Shell Properties (Change to set initial values)
WRAP: bool = False      # Wrap lines to a specific width
WIDTH: int = 80         # Width for line break
INFOS: bool = False     # Print more information about responses
RAW: bool = False       # Print the raw response completion instance

# Prompt argument for user input
INPUT_PROMPT: str = '> '


def print_help():
    """Write help message to be printed"""
    print("TODO: Finish help message ;-)")
    print("\nAgent commands")
    for command_class in Chat.commands:
        print(Chat.commands.write_command_help(command_class))


def toggle_cmd(var, name, args):
    if args:
        try: return parse_str_to_bool(args)
        except Exception: print(f"Invalid boolean value: {args}")
    else:
        print(f"Toggle {name} = {not var}")
        return not var


class PrintTime(Thread):

    @staticmethod
    def erase(string) -> None:
        print('\b \b' * len(string), end='', flush=True)

    def __init__(
            self, label: str, interval: float,
            ndigits: int | None = 2, clear_line: bool = False) -> None:
        super().__init__()
        self._label: str = label                # Label to print with time
        self._interval: float = interval        # Interval for re-printing
        self._ndigits: int | None = ndigits     # Number of digits for rounding
        self.clear_line = clear_line            # Clear line when stopped

        self._stop_request: Event = Event()         # Event for non-blocking wait and stop
        self._time_delta: timedelta | None = None   # Duration of counter

    def run(self) -> None:
        start_date_time: datetime = datetime.now()
        line = ''
        while True:
            self._stop_request.clear()
            self._time_delta = (datetime.now() - start_date_time).total_seconds()
            PrintTime.erase(line)
            line = f"{self._label}{round(self._time_delta, self._ndigits)} s"
            print(line, end='', flush=True)
            self._stop_request.wait(self._interval)
            if self._stop_request.is_set(): break
        if self.clear_line: PrintTime.erase(line)
        else: print(flush=True)

    def stop(self) -> None: self._stop_request.set()

    @property
    def time_delta(self): return self._time_delta


# Internal Constants
_RESPONSE_TIME_LABEL = 'Time: '  # Label for printing response time
_INTERVAL = 0.1                  # Refresh interval from printing response time
_NDIGITS = 2                     # Number of digits for rounding seconds


def main(model: str = Chat.MODEL) -> None:

    # Startup infos
    print(f"{PACKAGE_NAME} v{__version__} {NAME}")

    # Create agent and set default properties
    agent = Chat()
    agent._model = model
    print(f"Model: {agent._model}")
    agent.temperature = TEMPERATURE
    agent.top_p = TOP_P
    agent.choices = N

    # States variables (see default values for description)
    wrap = WRAP
    width = WIDTH
    infos = INFOS
    raw = RAW

    # Main loop
    while True:

        # Prompt for input
        user_input = input(INPUT_PROMPT)

        # TODO: Fix bug with command '\=2' that do not raise an error
        # TODO: Detect empty command with equal '=', e.g. '\n='

        # Process input for command or message
        if user_input.startswith(COMMAND_CHAR):
            command, args = split_command(user_input[1:])
            if len(command) == 0: continue
            command = command.lower()
            if command.startswith(('q', 'exit')): break
            elif command == 'wrap': wrap = toggle_cmd(wrap, 'wrap', args)
            elif command == 'raw': raw = toggle_cmd(raw, 'raw', args)
            elif command in ('i', 'info', 'infos'): infos = toggle_cmd(infos, 'infos', args)
            elif command == 'clear':
                print(agent.clear.__doc__)
                agent.clear()
            elif command == 'reset':
                print(agent.reset.__doc__)
                agent.reset()
                agent.temperature = TEMPERATURE
                agent.top_p = TOP_P
                agent.choices = N
            elif command in ('sys', 'system', 'sys_role', 'system_role'):
                if args:
                    if args.startswith(COMMAND_CHAR): agent.append_system_message()
                    else: agent.append_system_message(args)
                else:
                    for m in agent.messages:
                        if m['role'] == 'system': print(f"system: {m['content']}")
            elif command in TEMPERATURE_NAMES:
                if args:
                    if args.startswith(COMMAND_CHAR): args = None
                    try: agent.temperature = args
                    except ValueError as e: print(f"Error! {e}")
                else:
                    print(f"temperature = {agent.temperature}")
            elif command == TOP_P_NAMES:
                if args:
                    if args.startswith(COMMAND_CHAR): args = None
                    try: agent.top_p = args
                    except ValueError as e: print(f"Error! {e}")
                else:
                    print(f"top_p = {agent.top_p}")
            elif command == 'n':
                if args:
                    if args.startswith(COMMAND_CHAR): args = None
                    try: agent.choices = args
                    except ValueError as e: print(f"Error! {e}")
                else:
                    print(f"n = {agent.choices}")
            elif command in ('m', 'mess', 'message', 'messages'):
                for m in agent.messages:
                    print(f"{m['role']}: {m['content']}")
            else:
                print(f'Invalid command!')
            continue

        # If not a command, add user message
        agent.append_user_message(user_input)

        # Complete request
        # TODO: Add a way to cancel completion, perhaps with a try to catch cancel signal
        #       (implement after progressive completion).
        print_time = PrintTime(
            label=_RESPONSE_TIME_LABEL, interval=_INTERVAL,
            ndigits=_NDIGITS, clear_line=not infos)
        print_time.start()
        error = None
        try: request, response = agent.complete(append_completion=True)
        except Exception as e: error = e
        print_time.stop()
        print_time.join()

        # There was an error
        if error:
            print(f"{error.__class__.__name__}! {error}")
            continue

        # Print response
        if raw:
            print(f"request = {request}")
            print(f"response = {response}")
        else:
            for i, choice in enumerate(response.choices):
                print(f"Choice {i}:")
                if wrap:
                    for line in textwrap.wrap(choice.message.content, width):
                        print(line)
                else: print(choice.message.content)

        # Print information
        if infos:
            print(f"Finish reason: {response.choices[0].finish_reason}")
            messages_infos = {}
            # TODO: encapsulate in class
            for m in agent.messages:
                messages_infos[m['role']] = messages_infos.get(m['role'], 0) + 1
            print(
                f"Messages: {len(agent.messages)} ("
                f"{' + '.join(tuple(str(c) + ' ' + r for r, c in messages_infos.items()))})")
            print(
                f"Usage: {response.usage.total_tokens} tokens ("
                f"{response.usage.prompt_tokens} for prompts + "
                f"{response.usage.completion_tokens} for completions)")
