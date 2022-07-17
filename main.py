#%% Imports
import sys, os
from tkinter import FALSE
# Internal modules
from cardarbiter import CardArbiter

#### RUNTIME CONSTANTS AND OTHER SETTINGS stored in globals.py


DEV = False

HTML = False # Display HTML output 
ADD = False # Actually add cards to Anki


ROOT_PATH = os.path.abspath(__file__)
os.chdir(os.path.dirname(ROOT_PATH)) # cd to directory of main.py file
XML_PATH = r"export.xml"
    
if len(sys.argv) > 1: # If arguments are passed via CMD:
    # Command line arguments come in list, 0 = name of script, 1 = 1rst argument passed, 2 = 2nd argument passed
    if "html" in sys.argv:
        HTML = True
    if "add" in sys.argv:
        ADD = True

if DEV: # Dev mode - will only generate HTML
    HTML = True
    ADD = False

#%% 
if __name__ == "__main__":
    crawler = CardArbiter(XML_PATH)
    crawler.genCards()
    if HTML:
        crawler.displayCards()
    if ADD:
        crawler.addCards()

