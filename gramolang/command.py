"""
Text command interface

TODO: Find better name for the command type/categories
"""

from typing import Any, Sequence
from logging import getLogger
from inspect import isclass

from .common import (
    ESCAPE_CHAR, ARGUMENTS_SEP, NONE_ARG,
    parse_str_to_bool, split_name_arguments)


# Names for system command
SYSTEM_COMMAND_NAMES = ('system', 'sys', 'system_role', 'sys_role')

# String substitutions for None (lower case)
NONE_STRINGS = (ESCAPE_CHAR, r'\none')


# Exceptions
class CommandError(Exception): pass
class CommandClassError(Exception): pass


# Logging
module_logger = getLogger(__name__)


# Helper functionalities
# ----------------------

def write_name_summary(names: Sequence[str], summary: str):
    return f"{', '.join(names)}: {summary}"


# Classes definitions
# -------------------


class BaseCommand:
    """Base class for all commands

    Note: inheritable-only class, it is not meant to be instantiated directly.
    """

    NAMES = tuple()

    def __init__(self, *args, name: str | None = None, **kwargs) -> None:
        if name is not None:
            name = name.lower()
            if name not in self.NAMES:
                raise CommandClassError(f"Command name '{name}' not in class names")
        self._name: str | None = name
        self._args: tuple = args
        self._kwargs: tuple = kwargs

    @property
    def name(self) -> str | None: return self._name

    @property
    def args(self) -> list: return self._args

    @property
    def kwargs(self) -> dict: return self._kwargs

    @classmethod
    def summary(cls) -> str:
        return (
            cls.__doc__.splitlines()[0].strip() if cls.__doc__ is not None
            else None)

    @classmethod
    def parse_args(cls, *args: str, name: str | None = None, **kwargs):
        # TODO: Split name=value pair and pass as kwarg
        args = tuple(None if a.lower() in NONE_STRINGS else a for a in args)
        kwargs = {k: None if v.lower() in NONE_STRINGS else v for k, v in kwargs.items()}
        return cls(*args, name=name, **kwargs)

    @classmethod
    def parse(cls, arguments: str, name: str | None = None):
        # TODO: Ignore anything after comment char (#)?
        arguments = arguments.strip()
        arguments = tuple((a for a in arguments.split(sep=ARGUMENTS_SEP) if a))
        return cls.parse_args(*arguments, name=name)


class BaseEmptyCommand(BaseCommand):
    """Base class for a command without parameters

    Note: inheritable-only class, it is not meant to be instantiated directly.
    """
    def __init__(self, *, name: str | None = None) -> None:
        super().__init__(name=name)


class BaseUnaryCommand(BaseCommand):
    """Base class for a command with one or no parameter

    Note: inheritable-only class, it is not meant to be instantiated directly.
    """
    def __init__(self, arg=NONE_ARG, name: str | None = None) -> None:
        if arg is NONE_ARG: super().__init__(name=name)
        else: super().__init__(arg, name=name)

    @classmethod
    def parse(cls, arguments: str, name: str | None = None):
        # TODO: Ignore anything after comment char (#)?
        arguments = arguments.strip()
        if arguments: return cls.parse_args(arguments, name=name)
        else: return cls(name=name)


class BaseUnaryRequiredCommand(BaseCommand):
    """Base class for a command with one required argument

    Note: inheritable-only class, it is not meant to be instantiated directly.
    """
    def __init__(self, arg, name: str | None = None) -> None:
        super().__init__(arg, name=name)


class BaseToggleCommand(BaseUnaryCommand):
    """Base class for a toggle command

    Note: inheritable-only class, it is not meant to be instantiated directly.
    """
    def __init__(
            self, set_value: bool | None = None, name: str | None = None
            ) -> None:
        if set_value is None: super().__init__(name=name)
        else: super().__init__(bool(set_value), name=name)
        self.set_value: bool | None = set_value

    @classmethod
    def parse_args(cls, *args: str, name: str | None = None, **kwargs):
        if len(args) > 1 or len(kwargs) > 0:
            raise TypeError(
                f"Command class {cls.__name__} only take 1 positional argument.")
        elif len(args) == 1:
            return cls(parse_str_to_bool(args[0]), name=name)
        else:
            return cls(name=name, **kwargs)

    @classmethod
    def parse(cls, arguments: str, name: str | None = None):
        arguments = arguments.strip()
        if arguments: return cls.parse_args(arguments, name=name)
        else: return cls(name=name)


class Commands:
    """Command interface for an object class"""

    def __init__(
            self, cls_to_target: dict[type: Any], *args):
        self.logger = module_logger.getChild(self.__class__.__name__)
        self._class_to_target: dict[type: Any] = {}
        self._names_to_class: dict[str: type[BaseCommand]] = {}
        for d in (cls_to_target,) + args:
            for cls in d:
                if cls in self._class_to_target:
                    raise CommandError(
                        f"Command class {cls.__name__} already in collection")
                self._class_to_target[cls] = d[cls]
                for name in cls.NAMES:
                    name = name.lower()
                    if name in self._names_to_class:
                        raise CommandError(
                            f"Name '{name}' for command class {cls.__name__} "
                            f"already in collection")
                    self._names_to_class[name] = cls

    def __contains__(self, key) -> bool:
        if isclass(key):
            return key in self._class_to_target
        if isinstance(key, BaseCommand):
            return type(key) in self._class_to_target
        return key.lower() in self._names_to_class

    def __getitem__(self, key) -> type[BaseCommand]:
        if isclass(key):
            if key in self._class_to_target:
                return key
            else:
                raise CommandClassError(
                    f"No command class '{key.__name__}' in collection")
        if isinstance(key, BaseCommand):
            cls = type(key)
            if cls in self._class_to_target:
                return cls
            elif cls is not BaseCommand:
                raise CommandClassError(
                    f"Command class '{cls.__name__}' of "
                    f"instance '{key}' not in collection")
        key = key.lower()
        if key in self._names_to_class:
            return self[self._names_to_class[key]]
        else:
            raise CommandClassError(
                f"No command class with name '{key}' in collection")

    def __iter__(self): return iter(self._class_to_target)

    def summary(self, key) -> str | None:
        target_doc = self._class_to_target[self[key]].__doc__
        if target_doc is not None: return target_doc.splitlines()[0].strip()
        if self[key].summary() is not None: return self[key].summary()
        else: return None

    def write_command_help(self, key) -> str:
        return write_name_summary(self[key].NAMES, self.summary(key))

    # Not in use
    # def parse_args(self, name: str, *args, **kwargs) -> BaseCommand:
    #     return self[name](*args, name=name, **kwargs)

    def parse(self, string: str) -> BaseCommand:
        name, arguments = split_name_arguments(string)
        if arguments is None: return self[name](name=name)
        else: return self[name].parse(arguments=arguments, name=name)

    def instance_execute(self, instance, command: BaseCommand):
        target = self._class_to_target[type(command)]
        self.logger.debug(f"Execute {command} with target {target.__repr__()} on {instance}.")
        if callable(target):
            return target(instance, *command.args, **command.kwargs)
        elif type(target) is property:
            if len(command.args) > 0 or len(command.kwargs) > 0:
                return target.fset(instance, *command.args, **command.kwargs)
            else:
                return target.fget(instance)
        else:
            if len(command.args) > 0 or len(command.kwargs) > 0:
                return setattr(
                    instance, target, *command.args, **command.kwargs)
            else:
                return getattr(instance, target)

    def parse_instance_execute(self, target_instance, string: str):
        return self.instance_execute(
            instance=target_instance, command=self.parse(string=string))
