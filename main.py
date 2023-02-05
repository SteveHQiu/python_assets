#%% Imports
import sys, os
# Internal modules
# from . import cardarbiter
from cardgenerator import CardGenerator

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
    if 0: # Remove all Auto-tagged cards
        from anki.collection import Collection
        
        PROFILE_HOME = os.path.expanduser(R"~\AppData\Roaming\Anki2\User 1")
        CPATH = os.path.join(PROFILE_HOME, "collection.anki2")
        col = Collection(CPATH)
        
        card_ids = col.find_cards("tag:Auto")
        col.remove_notes_by_card(card_ids)
        
        print(F"Notes: {col.note_count()} | Cards: {col.card_count()}")
        for deck_cont in col.decks.all_names_and_ids():
            print(F"{deck_cont.name}: {col.decks.card_count(deck_cont.id, include_subdecks=False)}")
        
        col.close()
        
        
    
    crawler = CardGenerator(XML_PAGE_PATH, XML_OUTL_PATH)
    crawler.genNotes()
    if HTML:
        crawler.displayCards(HTML_PREVIEW_PATH)
    if ADD:
        crawler.addCards()
        
        

    if DEV: # Report deck information after adding cards
        from anki.collection import Collection
        
        PROFILE_HOME = os.path.expanduser(R"~\AppData\Roaming\Anki2\User 1")
        CPATH = os.path.join(PROFILE_HOME, "collection.anki2")
        col = Collection(CPATH)
        
        print(F"Notes: {col.note_count()} | Cards: {col.card_count()}")
        for deck_cont in col.decks.all_names_and_ids():
            print(F"{deck_cont.name}: {col.decks.card_count(deck_cont.id, include_subdecks=False)}")
            
        col.close()


