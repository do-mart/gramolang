"""
Versioning
"""


VERSIONS: dict[str:str] = {
    '0.4': "Log starts here with new console class and simplified chat class",
    '0.4.1': "Implementation of Role enum, and Message and Completion NamedTuples",
    '0.5': "Integration of OpenAI API ver. 1.x",
    '0.6': "New wraipi (wrapper of APIs) layer of abstraction over different APIs"
}

VERSION = list(VERSIONS)[-1]
