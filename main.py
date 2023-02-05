#%% Imports
import os, sys
# Internal modules
# from . import cardarbiter
from cardgenerator import CardGenerator
from anki_api import reportCollection

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
    ADD = True # Actually add cards to Anki
    
    

#%% 
if __name__ == "__main__":

    crawler = CardGenerator(XML_PAGE_PATH, XML_OUTL_PATH)
    crawler.genNotes()
    if HTML:
        crawler.displayCards(HTML_PREVIEW_PATH)
    if ADD:
        crawler.addCards()
        
        

    if DEV: # Report deck information after adding cards
        reportCollection()


