#%% Imports
# Built-in
import os

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
    
    def __init__(self, front, back, tags = None) -> None:
        self.front: str = front
        self.back: str = back
        self.tags: list[str] = tags
        self.deck = "Default" # Onenote notebook, pages, section path
        self.model = "Basic" 

#%%

def addCardsFromNotes(notes: list[ProtoNote], deck_name: str = None, card_type: str = None):
    try: # Open Anki DB using try statement so that any errors during the process will not interrupt Python from closing DB
        col = Collection(CPATH) # Open collection
        
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