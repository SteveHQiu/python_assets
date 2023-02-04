#%% Imports
import sys, os
# Internal modules
# from . import cardarbiter
from cardarbiter import CardArbiter

#### RUNTIME CONSTANTS AND OTHER SETTINGS stored in globals.py





ROOT_PATH = os.path.abspath(__file__)
os.chdir(os.path.dirname(ROOT_PATH)) # cd to directory of main.py file
XML_PAGE_PATH = R"data\page_xml.xml"
XML_OUTL_PATH = R"data\outline_xml.xml"
HTML_PREVIEW_PATH = R"data\displayCards_output.html"
DEV = True
    
if len(sys.argv) > 1: # If arguments are passed via CMD:
    # Command line arguments come in list, 0 = name of script, 1 = 1rst argument passed, 2 = 2nd argument passed
    DEV = False # If CMD arguments, will turn Dev false
    
    if "html" in sys.argv:
        HTML = True
    else:
        HTML = False
    if "add" in sys.argv:
        ADD = True
    else:
        ADD = False
        
if DEV: # Dev mode - will only generate HTML
    HTML = True # Display HTML output 
    ADD = False # Actually add cards to Anki

#%% 
if __name__ == "__main__":
    crawler = CardArbiter(XML_PAGE_PATH, XML_OUTL_PATH)
    crawler.genNotes()
    if HTML:
        crawler.displayCards(HTML_PREVIEW_PATH)
    if ADD:
        crawler.addCards()


