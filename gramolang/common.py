"""
Common functionalities for multiple modules
"""

from typing import Sequence, NamedTuple
from logging import getLogger
from enum import Enum, StrEnum, unique
from functools import wraps

from pathlib import Path
from os import listdir
from shutil import rmtree
from time import sleep
from datetime import datetime, timedelta
from random import random

from .version import VERSION


NAME = 'Gramolang'
NAME_VERSION = f"{NAME} v{VERSION}"

# Common names substitutions
TEMPERATURE_NAMES = ('temperature', 'temp')
TOP_P_NAMES = ('top_p',)

# Special characters
COMMENT_CHAR = '#'
COMMAND_CHAR = ':'
ESCAPE_CHAR = '\\'

# Separators
SPACE_SEP = ' '
NAME_VALUE_SEPS = ('=', ':')

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
    def from_extension(cls, extension: str):
        try: return cls._extensions[extension]
        except KeyError:
            raise Exception(
                f"Invalid extension: '{extension}' don't map to a file type.")

    @classmethod
    def from_path(cls, path: Path):
        if not path.is_file():
            raise FileNotFoundError(f"Invalid path: '{path}' is not a file.'")
        return cls.from_extension(path.suffix)


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

def parse_str_to_bool(string: str) -> bool:
    if string.lower() in ('0', 'false'): return False
    else: return bool(string)


def join_none(
        value: int | str | None, *values: int | str | None,
        sep: str = ' ') -> str:
    return sep.join(tuple(str(v) for v in (value, *values) if v is not None))


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


def write_timedelta(d: timedelta | float | int, ndigits=None) -> str:
    """Write timedelta (duration) in a consistent format"""
    if not isinstance(d, timedelta): d = timedelta(seconds=d)
    return f"{round(d.total_seconds(), ndigits=ndigits)} s"


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


# Parser/splitter for commands and text variables attributions
# ------------------------------------------------------------
def index_partition(string: str, i: int) -> tuple[str, str]:
    return string[:i], string[i + 1:]


def parse_name_value(string, single_name=False) -> tuple[str | None, str | None]:
    """Parse name/value pair or command/arguments pair"""

    string = string.strip()
    if not string: return '', ''

    sep = None
    i = len(string)
    for c in NAME_VALUE_SEPS:
        new_i = string.find(c)
        if new_i != -1 and new_i < i:
            sep = c
            i = new_i

    if sep:
        name, value = index_partition(string, i)
    else:
        i = string.find(SPACE_SEP)
        if i != -1: name, value = index_partition(string, i)
        elif single_name: name, value = string, ''
        else: name, value = '', string

    name = name.rstrip() if name != '' else None
    value = value.lstrip() if value != '' else None

    return name, value


# Environment variables and files
# -------------------------------

# TODO: See if I only what to allow equal sign for name-value separator
#       or all other characters.

def get_file_variable(
        path: Path, name: str | None = None, default: str | None = None):
    """Get the value of a variable in a file or return default value.

    The key must be writen in the form name=key on a single line. Only the
    first line starting with name will be read. The equal (=) signe can be
    replaced by any character in NAME_VALUE_SEPS.

    If name is None, use the first value not in a name=value attribution.
    """
    if not isinstance(path, Path): path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"API key file doesn't exist: {path}")
    with open(path, 'r') as path:
        for line in path:
            if line.lstrip().startswith(COMMENT_CHAR): continue
            n, value = parse_name_value(line)
            if name is None and n is None: return value
            elif n == name: return value
    return default


# DEPRECATED
# def get_file_environ_variable(name: str, file: Path | str = None):
#     """Get the value of a variable in a file or in an environment variable."""
#     if file is not None:
#         value = get_file_variable(name=name, path=file)
#         if value is not None: return value
#         else: raise KeyError(f"Cannot find variable '{name}' in file: {file}")
#     else:
#         if name in environ: return environ[name]
#         else:
#             raise KeyError(f"Environment variable '{name}' doesn't exist.")


# File/directory functionalities
# ------------------------------

def write_new_filename(filename: str, *dirs: Path):
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
