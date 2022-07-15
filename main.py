#%% Imports
import sys, os
# Internal modules
from cardarbiter import CardArbiter

#### RUNTIME CONSTANTS AND OTHER SETTINGS stored in globals.py

DEV = True # Change to False before running via program

ROOT_PATH = os.path.abspath(__file__)
os.chdir(os.path.dirname(ROOT_PATH)) # cd to directory of main.py file

if DEV:
    XML_PATH = r"export.xml"
else:
    # Command line arguments come in list, 0 = name of script, 1 = 1rst argument passed, 2 = 2nd argument passed
    ARG_FILENAME = sys.argv[1] # Contains filename of exported XML file
    XML_PATH = os.path.join(ROOT_PATH, ARG_FILENAME)

#%% 
if __name__ == "__main__":
    crawler = CardArbiter(XML_PATH)
    crawler.genCards()
    crawler.displayCards()
    crawler.addCards()

