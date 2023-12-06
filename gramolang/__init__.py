"""Package Initialization"""

from logging import getLogger

module_logger = getLogger(__name__)

NAME = 'Gramolang'

VERSIONS: dict[str:str] = {
    '0.4': """Logs starts here with new console class and simplified chat class""",
    '0.4.1': """Implementation of Role enum, and Message and Completion NamedTuples""",
    '0.5': """Integrations of the OpenAI API v.1.x""",
    '0.6': """New wrapi (wrapper of APIs) layer for abstraction over different APIs"""
}
VERSION = list(VERSIONS)[-1]

module_logger.debug(f"Initiating package {NAME} Version {VERSION}")
