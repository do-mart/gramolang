"""
Package Initialization

TODO: Change API key mechanism to only use hard key or environment variable.
TODO: Use configparser to retrieve key from file and load in environment
TODO: Move root modules in new examples package with a common module for the
      key import mechanism.
TODO: Create complete in text file chat for one conversation based on sheet?
"""

# Forwards
from .common import NAME, NAME_VERSION
from .wraipi import OpenAIWrapper, AnthropicWrapper
from .chat import Chat
