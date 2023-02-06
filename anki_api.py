#%% Imports
# Built-in
import os, sys, re

# Anki
from anki.storage import Collection
from anki.notes import Note

from anki.decks import DeckManager
from anki.models import ModelManager
from anki.tags import TagManager

# Internal modules
from internal_globals import CPATH

#%% Classes
class ProtoNote:
    
    def __init__(self, front, back, deck = "Default", model = "Basic", tags = None) -> None:
        self.front: str = front
        self.back: str = back
        self.tags: list[str] = tags
        self.deck = deck 
        self.model = model 

#%%

def addCardsFromNotes(notes: list[ProtoNote],
                      deck_name: str = None,
                      card_type: str = None,
                      replace = False):
    try: # Open Anki DB using try statement so that any errors during the process will not interrupt Python from closing DB
        col = Collection(CPATH) # Open collection
        
        if replace: # Remove all auto cards from target decks
            target_decks: set[str] = {n.deck for n in notes}
            if deck_name:
                target_decks.add(deck_name)
            
            for targ_deck in target_decks:
                remCards(F'tag:Auto "deck:{targ_deck}"', col) # Remove auto cards from target deck
            
                
        
        card_num = 1
        for note in notes:
            # Define deck and note type - can be used in the future to create different note types
            if deck_name:
                deck = col.decks.add_normal_deck_with_name(deck_name) # Returns a container with the deck id
            else:
                deck = col.decks.add_normal_deck_with_name(note.deck) 
            if card_type:
                model = col.models.by_name(card_type) # Returns a NoteType dict which is needed to specify new note
            else:
                model = col.models.by_name(note.model) 

            # Convert note into Anki format and add it
            anki_note = col.new_note(model) # Create new note instance **Doesn't add note to collection
            anki_note.fields[anki_note._field_index("Front")] = note.front # Note fields are stored in list of strings, need method to find index of labeled field
            anki_note.fields[anki_note._field_index("Back")] = note.back
            anki_note.add_tag("Auto") # Tag strings with spaces will be treated as separate tags 
            col.add_note(anki_note, deck.id) # Adds note to DB

            print(f"Added card #{card_num}")
            card_num += 1
            
        col.save() # Save DB, mostly redundant but added just in case 
    finally: # Should have this always run, otherwise, anki will get stuck        
        col.close() # Need this function, otherwise instance stays open

def reportCollection(col_open: Collection | bool = False ):
    try:
        if not col_open: # Instantiate collection if not already open
            col = Collection(CPATH)
        else:
            col = col_open

        print(F"Notes: {col.note_count()} | Cards: {col.card_count()}")
        for deck_cont in col.decks.all_names_and_ids():
            print(F"{deck_cont.name}: {col.decks.card_count(deck_cont.id, include_subdecks=False)}".encode("ascii", "replace"))
        
    finally:
        if col_open:
            return
        col.close()
    

     
def remCards(filter: str = "tag:Auto", col_open: Collection | bool = False):
    # Remove cards according to a filter
    try:
        if not col_open: # Instantiate collection if not already open
            col = Collection(CPATH)
        else:
            col = col_open
            
        print(F"Before removal")
        reportCollection(col)
        
        card_ids = col.find_cards(filter)
        col.remove_notes_by_card(card_ids)
        
        print(F"After removal")
        reportCollection(col)
        

    finally:
        if col_open:
            return
        col.close()

#%%
if __name__ == "__main__":
    if len(sys.argv) > 1: # If arguments passed in and running as main module
            
        if "report" in sys.argv:
            reportCollection()
        
        if "remove" in sys.argv:
            remCards("tag:Auto")
    else:
        reportCollection()
