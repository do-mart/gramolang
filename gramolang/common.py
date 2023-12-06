"""
Common functionalities
"""

from typing import Sequence, NamedTuple
from logging import getLogger
from enum import Enum, StrEnum, unique
from functools import wraps

from pathlib import Path
from os import environ, listdir
from shutil import rmtree
from time import sleep
from datetime import datetime, timedelta
from random import random
from threading import Thread, Event

# Common names substitutions
TEMPERATURE_NAMES = ('temperature', 'temp')
TOP_P_NAMES = ('top_p',)

# Special characters
COMMENT_CHAR = '#'
COMMAND_CHAR = ':'
ESCAPE_CHAR = '\\'

# Separators
ARGUMENTS_SEP = ' '
NAME_ARGUMENTS_SEPS = ('=', ' ', ':')
NAME_ARGUMENTS_SEPS_STR = ''.join(NAME_ARGUMENTS_SEPS)

# Sentinel value for no argument (when None is a possible value)
NONE_ARG = object()

# Logging
module_logger = getLogger(__name__)


# Types
# -----

@unique
class Role(StrEnum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'


class Message(NamedTuple):
    role: Role
    content: str


# Files types
# -----------

@unique
class FileType(str, Enum):
    def __new__(cls, value, extensions):
        obj = str.__new__(cls, [value])
        obj._value_ = value
        obj.extensions = extensions
        if 'extensions' not in cls.__dict__: cls._extensions = {}
        for ext in extensions: cls._extensions[ext] = obj
        return obj

    # def __init__(self, value, extensions):
    #     if 'extensions' not in self.__class__.__dict__:
    #         self.__class__.extensions = {}
    #     for ext in extensions: self.__class__.extensions[ext] = self

    TEXT = ('Text', {'.txt', '.text'})
    CSV = ('CSV', {'.csv'})
    EXCEL = ('Excel', {'.xlsx', '.xls'})

    @classmethod
    def from_extension(cls, value: str):
        try: return cls._extensions[value]
        except KeyError:
            raise Exception(
                f"Invalid extension: '{value}' don't map to a file type.")

# DEPRECATED
# FILETYPE_TO_EXTENSIONS: dict[FileType: tuple[str]] = {
#     FileType.TEXT: ,
#     FileType.CSV: ,
#     FileType.EXCEL:
# }
# EXTENSION_TO_FILETYPE: dict[str: FileType] = {
#     ext: file_type
#     for file_type, extensions in FILETYPE_TO_EXTENSIONS.items()
#     for ext in extensions}


# Very basic stuff
# ----------------

def write_backspaces(string: str) -> str: return '\b \b' * len(string)


def parse_str_to_bool(string: str) -> bool:
    if string.lower() in ('0', 'false'): return False
    else: return bool(string)


def join_none(
        value: int | str | None, *values: int | str | None,
        sep: str = ' ') -> str:
    return sep.join(tuple(str(v) for v in (value, *values) if v is not None))


def split_name_arguments(string):
    i = len(string)
    for c in NAME_ARGUMENTS_SEPS:
        new_i = string.find(c)
        if new_i != -1 and new_i < i: i = new_i
    if i != len(string): return string[:i], string[i:].lstrip(NAME_ARGUMENTS_SEPS_STR)
    else: return string, None


# Text formatting
# ---------------

def mark(
        value: int | str | None, *values: Sequence[int | str | None],
        sep: str = ' ') -> str:
    if value is None and len(values) == 0: return ''
    else: return f"[{join_none(value, *values, sep=sep)}]"


def rmark(
        value: int | str | None, *values: Sequence[int | str | None],
        sep: str = ' ', left: str = ' ') -> str:
    m = mark(value, *values, sep=sep)
    if len(m) == 0: return ''
    else: return f"{left}{m}"


def write_timedelta(d: timedelta | float | int) -> str:
    """Write timedelta (duration) in a consistent format"""
    if not isinstance(d, timedelta): d = timedelta(seconds=d)
    return f"{round(d.total_seconds())}s"


def now_delta(start: datetime, total_seconds=False):
    """Calculate timedelta (duration) since start"""
    delta = datetime.now() - start
    return delta.total_seconds() if total_seconds else delta


def write_now_delta(start: datetime):
    """Write timedelta (duration) since start in a consistent format"""
    return write_timedelta(now_delta(start))


def write_exception(exception: Exception, delta: timedelta = None):
    """Write exception in a consistent format"""
    if delta is not None: delta = f" after {write_timedelta(delta)}"
    else: delta = ''
    return f"{exception.__class__.__name__}{delta}: {exception}"


def write_error(
        exception: Exception | None = None, with_object: str | None = None,
        delta: timedelta = None, re_raise: bool = False, sep: str = ': '):
    """Write error message in a consistent format"""
    parts = []
    if with_object:
        part = f"Error with {with_object}"
        if delta is not None: part += f" after {write_timedelta(delta)}"
        parts.append(part)
    if exception:
        if delta is not None and with_object is None:
            parts.append(write_exception(exception, delta))
        else:
            parts.append(write_exception(exception))
    if re_raise:
        parts.append(f"Re-raising...")
    return sep.join(parts)


def print_error(
        exception: Exception | None = None, with_object: str | None = None,
        delta: timedelta = None, re_raise: bool = False,
        sep: str = ': ', file=None):
    """Print error message in a consistent format"""
    print(
        write_error(
            with_object=with_object, exception=exception, delta=delta,
            re_raise=re_raise, sep=sep),
        file=file)


# Logging
# -------

# DEPRECATED
# def base_log(*args, file: TextIO | None = stdout, **kwargs):
#     """Simple common logger for package
#
#     Time can be added to all log entry with datetime.now().strftime('%X') as a
#     first argument in the print command.
#     """
#     if file is None: return
#     print(*args, **kwargs, file=file, flush=True)


class TimePrinter(Thread):

    def __init__(self, label: str = '', interval: float = 1.0, ndigits: int | None = 2,
            clear_line: bool = False) -> None:

        super().__init__()
        self._label: str = label  # Label to print with time
        self._interval: float = interval  # Interval for re-printing
        self._ndigits: int | None = ndigits  # Number of digits for rounding
        self.clear_line = clear_line  # Clear line when stopped

        self._stop_request: Event = Event()  # Event for non-blocking wait and stop
        self._time_delta: timedelta | None = None  # Duration of counter

        self._line: str = ''  # Last printed line

    def erase_line(self) -> None:
        print(write_backspaces(self._line), end='', flush=True)
        self._line = ''

    def run(self) -> None:

        start_date_time: datetime = datetime.now()

        while True:
            self._stop_request.clear()
            self._time_delta = (datetime.now() - start_date_time).total_seconds()
            self.erase_line()
            self._line = f"{self._label}{round(self._time_delta, self._ndigits)} s"
            print(self._line, end='', flush=True)
            self._stop_request.wait(self._interval)
            if self._stop_request.is_set(): break

        if self.clear_line:
            self.erase_line()
        else:
            print(flush=True)

    def stop(self) -> None:
        self._stop_request.set()

    @property
    def time_delta(self):
        return self._time_delta


# Environment variables and files
# -------------------------------

def get_file_variable(name: str, file: Path | str = None, default=None):
    """Get the value of a variable in a file or return default value.

    The key must be writen in the form name=key on a single line. Only the
    first line starting with name will be read.
    """
    if not isinstance(file, Path): file = Path(file)
    if not file.is_file():
        raise FileNotFoundError(f"API key file doesn't exist: {file}")
    with open(file, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith(name): return split_name_arguments(line)[1]
    return default


def get_file_environ_variable(name: str, file: Path | str = None):
    """Get the value of a variable in a file or in an environment variable."""
    if file is not None:
        value = get_file_variable(name=name, file=file)
        if value is not None: return value
        else: raise KeyError(f"Cannot find variable '{name}' in file: {file}")
    else:
        if name in environ: return environ[name]
        else:
            raise KeyError(f"Environment variable '{name}' doesn't exist.")


# DEPRECATED
# def set_openai_api_key(
#         file: Path | str = None, name: str = OPENAI_API_KEY_NAME):
#     openai.api_key = get_file_environ_variable(name, file)


# File/directory functionalities
# ------------------------------

def _write_new_filename(filename: str, *dirs: Path):
    """Write a new filename that does not exist in a series of directories"""
    i = 0
    f = Path(filename)
    check_filename = True
    while check_filename:
        check_filename = False
        for d in dirs:
            if d.joinpath(filename).exists():
                i += 1
                f = Path(f"{f.stem} [{i}]{f.suffix}")
                check_filename = True
    return f


def remove_dir_entries(dir_path: Path):
    """Remove entries in a directory, re-raise exceptions"""
    for path_name in listdir(dir_path):
        path = dir_path / path_name
        try:
            if path.is_dir(): rmtree(path)
            else: path.unlink()
        except Exception as e:
            raise e


# Decorator for retry with exponential backoff
# --------------------------------------------

def retry(
        retries: int = 0,
        rate_exceptions: Sequence[Exception] | tuple = tuple(),
        timeout_exceptions: Sequence[Exception] | tuple = tuple(),
        base_delay: float = 1, jitter: bool = True, spread_factor: float = 0.5,
        backoff: bool = True, backoff_base: float = 2,
        call_id: str | int | None = None,
        log_messages: Sequence[str] | tuple = tuple()):
    """Retry function call with exponential backoff

    If retries equals 0 (default), the function will be called only once as if
    it had not been decorated. The total number of attempts equals retries + 1.

    Params:
    call_id: Identification for function in log messages
    log_messages: Additional messages to log
    retries: Retries attempts after first attempt (-1 for infinite retry)
    rate_exceptions: Collection of rate exception classes
    timeout_exceptions: Collection of timeout exceptions classes
    base_delay: Base delay in seconds between retries
    jitter: Jitter (spread) delay if True (default)
    spread_factor: Jitter spread as a factor of delay (max. 1)
    backoff: Exponential backoff delay for retries if True (default)
    backoff_base: Base for exponential backoff
    """

    logger = module_logger.getChild(retry.__name__)

    def decorate(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            def write_log(message: str, *messages: str):
                return ' '.join((
                    message,
                    f"{mark(call_id)}[{i}/{retries}][LEV {backoff_level}]",
                    *log_messages, *messages))

            spread = base_delay * spread_factor
            backoff_level = 0

            i = 0
            while True:
                try:
                    logger.debug(write_log(f"Calling {func}"))
                    result = func(*args, **kwargs)
                    logger.debug(write_log('Successfully completed call'))
                    break
                except rate_exceptions + timeout_exceptions as e:
                    logger.debug(write_log('Rate or timeout error with function call', write_exception(e)))
                    if i == retries:
                        logger.debug(write_log("Re-raising..."))
                        raise e
                    delay = base_delay + ((spread * random()) - (spread / 2) if jitter else 0)
                    if isinstance(e, rate_exceptions):
                        backoff_level += 1
                        if backoff: delay *= backoff_base ** backoff_level
                    logger.debug(write_log(f"Sleep({round(delay, 1)}) and retry"))
                    sleep(delay)
                except Exception as e:
                    logger.debug(write_log(
                        'Error (unhandled) with function call',
                        write_error(exception=e, re_raise=True, sep='\n')))
                    raise e
                i += 1

            return result

        return wrapper

    return decorate
