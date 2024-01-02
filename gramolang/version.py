"""
Versioning
"""


DESCRIPTIONS: dict[str:str] = {
    '0.4': "Log starts here with new console class and simplified chat class",
    '0.4.1': "Implementation of Role enum, and Message and Completion NamedTuples",
    '0.5': "Integration of OpenAI API ver. 1.x",
    '0.6': "New wraipi (wrapper of AI organizations APIs) layer of abstraction",
    '0.6.1': "Integration of a version control system (VCS) and code clean up",
    '0.6.2': "Consolidation and bug fix for API keys retrieval methods",
    '0.6.3': "Simplification of commands nomenclature",
    '0.6.4': "Simplified API keys implementation and examples modules",
    '0.6.5': "New common all_models interface in API wrappers"
}

VERSION = list(DESCRIPTIONS)[-1]
