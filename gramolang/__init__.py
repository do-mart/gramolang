"""
Package Initialization

"""

# TODO: Create complete in text file chat for one conversation based on sheet?

from logging import getLogger

# Forwards
from .wraipi import OpenAIAPIWrapper, AnthropicAPIWrapper
from .chat import Chat


module_logger = getLogger(__name__)

NAME = 'Gramolang'

VERSIONS: dict[str:str] = {
    '0.4': """Log starts here with new console class and simplified chat class""",
    '0.4.1': """Implementation of Role enum, and Message and Completion NamedTuples""",
    '0.5': """Integrations of OpenAI API ver. 1.x""",
    '0.6': """New wraipi (wrapper of APIs) layer of abstraction over different APIs"""
}
VERSION = list(VERSIONS)[-1]

NAME_VERSION = f"{NAME} v{VERSION}"

module_logger.debug(f"Initializing {NAME_VERSION}")
