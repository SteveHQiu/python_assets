#%% Imports
# Built-in
import sys, os, base64, re, string, copy
from typing import Union
from collections.abc import Iterable


#%% Constants

PROFILE_HOME = os.path.expanduser(R"~\AppData\Roaming\Anki2\User 1")
CPATH = os.path.join(PROFILE_HOME, "collection.anki2")
MPATH = os.path.join(PROFILE_HOME, "collection.media")



#%% Global Classes

#%% Global functions

