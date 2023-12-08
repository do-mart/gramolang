"""
Even more automatic completions

"""

from logging import getLogger

from pathlib import Path
from os import listdir
from datetime import datetime, timedelta
from time import sleep
from concurrent.futures import ThreadPoolExecutor

from .common import (
    FileType,
    rmark, now_delta, write_error, _write_new_filename)
from .wraipi import APIWrapper
from .chat import Chat
from .sheet import complete


# Function settings
CACHE_DIR_NAME = '.cache'       # Cache directory
RELOAD_CACHE = True             # Files still in the cache are reloaded in the pool
IGNORE_DOT_FILE = True          # Ignore system dot (.) files

PRINT_NEW_FILES_STATUS = False      # Print status if new file
PRINT_NEW_ERRORS_STATUS = False     # Print status if new error

# Logging
module_logger = getLogger(__name__)


def validate(file_type: FileType):
    if file_type in (FileType.TEXT, FileType.CSV):
        raise Exception(f"{file_type.value} file not supported for now.")
    return file_type


def complete_file(
        path: Path, new_path: Path | str = None,
        api_keys: dict[type(APIWrapper): str] | None = None,
        api_key_files: dict[type(APIWrapper): Path] | None = None,
        model: str = Chat.MODELS[0],
        timeout: int | None = None, retries: int | None = 0,
        max_conversations: int | None = None,
        file_id: str | int | None = None):
    """Autocomplete file"""

    start = datetime.now()
    logger = module_logger.getChild(complete_file.__name__)

    file_type = FileType.from_path(path)
    validate(file_type)
    logger.info(
        f"File type for extension '{path.suffix}'{rmark(file_id)}: "
        f"{file_type.value}")

    match file_type:
        case FileType.EXCEL:
            return complete(
                workbook_path=path, new_workbook_path=new_path,
                api_keys=api_keys, api_key_files=api_key_files, model=model,
                timeout=timeout, retries=retries, max_conversations=max_conversations,
                file_id=file_id)


def complete_remove_file(
        path: Path, new_path: Path,
        api_keys: dict[type(APIWrapper): str] | None = None,
        api_key_files: dict[type(APIWrapper): Path] | None = None,
        model: str = Chat.MODELS[0],
        timeout: int | None = None, retries: int | None = 0,
        max_conversations: int | None = None,
        file_id: str | int | None = None):
    """Autocomplete and remove original file"""

    # Call to complete file
    result = complete_file(
        path=path, new_path=new_path,
        api_keys=api_keys, api_key_files=api_key_files, model=model,
        timeout=timeout, retries=retries, max_conversations=max_conversations,
        file_id=file_id)

    # Delete original file
    if new_path.is_file(): path.unlink()

    # Return call result
    return result


def watch_pool_files(
        root_dir: Path | str,
        in_dir_name: str = 'in', out_dir_name: str = 'out',
        api_keys: dict[type(APIWrapper): str] | None = None,
        api_key_files: dict[type(APIWrapper): Path] | None = None,
        model: str = Chat.MODELS[0],
        timeout: int | None = None, retries: int | None = 0,
        max_files: int | None = None, max_conversations: int | None = None,
        status_delay: int = 1 * 60, refresh_delay: int = 1):
    """Watch directory and autocomplete files as they are added

    OpenAI API Key must be set prior to function call, see set_openai_api_key()

    Params:
        ...
        refresh_delay: Delay in seconds for printing pool status
        idle_delay: Delay in seconds since last message for printing idle message
        max_files: Max. worker threads in pool to process files
        ...
    """

    start = datetime.now()
    logger = module_logger.getChild(watch_pool_files.__name__)

    def valid_file(path: Path, dir_name: str):
        """Test for valid file for completion"""
        try:
            validate(FileType.from_path(path))
            return True
        except Exception:
            logger.warning(
                f"Invalid file or file type, "
                f"please remove '{path.name}' from {dir_name} directory.")
            return False

    # Start messages
    logger.info("Watch and pool files for chat completion.")
    logger.info(f"Start time: {start.strftime('%c')}")

    # Directories initialization
    logger.info(f"Root directory: {root_dir}")
    if not isinstance(root_dir, Path): root_dir = Path(root_dir)
    root_dir.mkdir(exist_ok=True)

    logger.info(f"Input directory (drop file here): {in_dir_name}")
    in_dir = root_dir / in_dir_name
    in_dir.mkdir(exist_ok=True)

    logger.info(f"Output directory (get file here): {out_dir_name}")
    out_dir = root_dir / out_dir_name
    out_dir.mkdir(exist_ok=True)

    logger.info(f"Cache directory: {CACHE_DIR_NAME}")
    cache_dir = root_dir / CACHE_DIR_NAME
    cache_dir.mkdir(exist_ok=True)

    # Check cache content
    cache_entries = tuple(e for e in listdir(cache_dir))
    if IGNORE_DOT_FILE:
        cache_entries = tuple(
            e for e in cache_entries if not e.startswith('.'))
    pool_filenames = []
    if len(cache_entries) > 0:
        logger.warning(
            f"Warning: cache is not empty,"
            f"these entries are safe to delete if they are not reloaded automatically: "
            f', '.join((repr(e) for e in cache_entries)))
        if RELOAD_CACHE:
            logger.info("Add old files to the list of pool files.")
            for entry_name in cache_entries:
                if valid_file(cache_dir/entry_name, 'cache'):
                    pool_filenames.append((entry_name, entry_name))

    # Idle delay
    status_delay = timedelta(seconds=round(status_delay))

    # Exceptions (not use for now)
    exceptions = []

    # Inner function to print status
    def write_status(f=None, e=None):
        nonlocal last_status_time
        status = f"Status: "
        if f is not None: status += f"{f} new file(s), "
        if e is not None: status += f"{e} new error(s), "
        q = len(future_names)
        status += \
            f"{q} file(s) in queue, " \
            f"completed {file_id_counter - q} file(s) with {total_errors} error(s) " \
            f"({datetime.now().strftime('%X')})"
        last_status_time = datetime.now()
        return status

    # Context manager for the thread pool executor
    with ThreadPoolExecutor(max_workers=max_files) as executor:

        # Main watch loop
        file_id_counter = -1
        total_errors = 0
        future_names = {}
        last_status_time = datetime.now()
        invalid_entry_names = set()

        while True:

            # Print idle status
            if status_delay is not None and now_delta(last_status_time) > status_delay:
                logger.info(write_status())
                # print_f("I am bored, please feed me...")

            # Cache new file(s) (if any)
            prev_invalid_entry_names = set(invalid_entry_names)
            invalid_entry_names.clear()
            for entry_name in listdir(in_dir):

                # Reconstitute path
                entry_path = in_dir / entry_name

                # Skip tests
                if IGNORE_DOT_FILE and entry_name.startswith('.'): continue
                if entry_name in prev_invalid_entry_names:
                    invalid_entry_names.add(entry_name)
                    continue
                if not valid_file(entry_path, 'input'):
                    invalid_entry_names.add(entry_name)
                    continue

                # Rename and cache file
                new_filename = _write_new_filename(
                    datetime.now().strftime('%Y-%m-%d %H%M%S') + ' ' + entry_name,
                    cache_dir, out_dir)
                entry_path.rename(cache_dir / new_filename)
                pool_filenames.append((entry_name, new_filename))

            # Pool files
            new_files_count = 0
            for filename in pool_filenames:
                file_id_counter += 1
                file_id = f"file {file_id_counter}"
                new_files_count += 1
                new_name = f"file '{filename[1]}'{rmark(file_id)}"
                logger.info(f"Pooling file '{filename[0]}' as {new_name}")
                future = executor.submit(
                    complete_remove_file,
                    path=cache_dir / filename[1], new_path=out_dir / filename[1],
                    file_id=file_id,
                    api_keys=api_keys, api_key_files=api_key_files,
                    model=model, timeout=timeout, retries=retries,
                    max_conversations=max_conversations)
                future_names[future] = new_name
            pool_filenames.clear()

            # DEPRECATED
            # Print status with new files
            # if PRINT_NEW_FILES_STATUS and new_files_count > 0:

            # Debug log status if new files
            if new_files_count > 0:
                logger.debug(write_status(f=new_files_count))

            # Manage thread exceptions
            done_futures = (
                future for future in tuple(future_names) if future.done())
            new_errors_count = 0
            for future in done_futures:
                name = future_names[future]
                future_names.pop(future)
                if future.exception() is not None:
                    logger.critical(
                        write_error(
                            future.exception(), name, re_raise=True, sep='\n'))
                    raise future.exception()
                elif future.result() is not None:
                    exceptions.append(future.result())
                    new_errors_count += len(future.result())
            total_errors += new_errors_count

            # DEPRECATED
            # # Print status with new errors
            # if PRINT_NEW_ERRORS_STATUS and new_errors_count > 0:
            #     print_status(e=new_errors_count)

            # Debug log status if new error(s)
            if new_errors_count > 0:
                logger.debug(write_status(e=new_errors_count))

            # Sleep
            sleep(refresh_delay)




