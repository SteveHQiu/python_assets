# Built-in
import os
from typing import Union
from collections.abc import Iterable
from xml.etree import ElementTree
from xml.etree.ElementTree import Element


# Anki
from anki.storage import Collection

# Internal modules
# from . import internal_globals, renderer_std
from internal_globals import CPATH
from renderer import StandardRenderer
from onenote import OENodeHeader, OENodePoint, getHeaders

#%% Classes
class Note:
    
    def __init__(self, front, back, tags = None) -> None:
        self.front: str = front
        self.back: str = back
        self.tags: list[str] = tags
        self.path = "" # Onenote notebook, pages, section path

class CardGenerator:
    
    def __init__(self, xml_path: Union[str, bytes, os.PathLike], outline_path: Union[str, bytes, os.PathLike]):
        self.outline: ElementTree.ElementTree = ElementTree.parse(outline_path)
        self.page: ElementTree.ElementTree = ElementTree.parse(xml_path)
        self.header_list: list[OENodeHeader] = getHeaders(self.page, self.outline) # Input header list, should be able to access rest of nodes through this point
        self.notes: list[Note] = [] # Container for generated cards, format of Tuple[front, back]

    def genNotes(self):
        """
        Note that this will still copy media into anki media directory if there are images
        """
        def enterEntryPoints(cur_node: OENodeHeader | OENodePoint):
            for child_node in cur_node.children_nodes: # Starting point for nodes directly under header (or Element if in nested loop)
                if child_node.type in ["concept", "grouping",]: # Only certain types of nodes will trigger card generation

                    # Fill front and back 
                    renderer = StandardRenderer(child_node) # New instance for each entry point
                    renderer.renderHtml()
                    note = Note(renderer.fronthtml, renderer.backhtml)
                    self.notes.append(note) # Append rendered HTMLs

                    if child_node.children_nodes: # Recursively search for children 
                        # Only becomes relevant after OENodeHeader loop
                        enterEntryPoints(child_node) 
            return None

        for header in self.header_list:
            enterEntryPoints(header)
            
        return self
        
    def displayCards(self, html_path):
        """
        Display generated card in HTML format, for debuggging purposes
        """
        html = ""
        card_num = 1
        for note in self.notes:
            html += f"<br>Card no. {card_num}:<br>\n" + note.front + "<hr>\n" + note.back + "<hr><hr><br>\n" # Add front and back with spacing between both and next set of cards
            card_num += 1
        with open(html_path, "w", encoding="utf-8") as file:
            file.write(html)
        return self
        
    def addCards(self):
        try: # Open Anki DB using try statement so that any errors during the process will not interrupt Python from closing DB
            col = Collection(CPATH) # Open collection
            
            card_num = 1
            for note in self.notes:
                # Define deck and note type - can be used in the future to create different note types
                deck = col.decks.add_normal_deck_with_name("TestDeck::Test2") # Returns a container with the deck id
                model = col.models.by_name("Basic") # Returns a NoteType dict which is needed to specify new note

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
            return self

        


# %%
