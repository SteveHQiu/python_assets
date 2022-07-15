# Built-in
from typing import Union
from collections.abc import Iterable
from xml.etree import ElementTree
from xml.etree.ElementTree import Element


# Anki
from anki.storage import Collection

# Internal modules
from internal_globals import OENodeHeader, OENodePoint, getHeaders
from internal_globals import CPATH
from renderer_std import StandardRenderer

#%% Classes
class CardArbiter:
    
    def __init__(self, xml_path):
        self.header_list: list[OENodeHeader] = getHeaders(xml_path) # Input header list, should be able to access rest of nodes through this point
        self.cards: list[tuple[str, str]] = [] # Container for generated cards, format of Tuple[front, back]

    def genCards(self):
        """
        Note that this will still copy media into anki media directory if there are images
        """
        def enterEntryPoints(cur_node: OENodeHeader | OENodePoint):
            for child_node in cur_node.children_nodes: # Starting point for nodes directly under header (or Element if in nested loop)
                if child_node.type in ["concept", "grouping",]: # Only certain types of nodes will trigger card generation

                    # Fill front and back 
                    renderer = StandardRenderer(child_node) # New instance for each entry point
                    renderer.renderHtmlMain()
                    renderer.renderHtmlParents()
                    front = renderer.fronthtml 
                    back = renderer.backhtml
                    self.cards.append((front, back)) # Append rendered HTMLs

                    if child_node.children_nodes: # Recursively search for children 
                        # Only becomes relevant after OENodeHeader loop
                        enterEntryPoints(child_node) 
            return None

        for header in self.header_list:
            enterEntryPoints(header)
            
        return self
        
    def displayCards(self):
        """
        Display generated card in HTML format, for debuggging purposes
        """
        html = ""
        card_num = 1
        for card in self.cards:
            html += f"<br>Card no. {card_num}:<br>\n" + card[0] + "<hr>\n" + card[1] + "<hr><hr><br>\n" # Add front and back with spacing between both and next set of cards
            card_num += 1
        with open("displayCards_output.html", "w", encoding="utf-8") as file:
            file.write(html)
        return self
        
    def addCards(self):
        try: # Open Anki DB using try statement so that any errors during the process will not interrupt Python from closing DB
            col = Collection(CPATH, log=True) # NOTE that this changes the directory
            card_model = col.models.by_name("Basic") # Search for card model
            deck = col.decks.by_name("ZExport") # Set current deck
            
            for card in self.cards:
                front, back = card # Unpack HTML from cards
                # Instantiate new note
                note = col.new_note(card_model) # New new_note() method requires a card model to be passed as a parameter
                note.note_type()['did'] = deck['id'] # Need to set deck ID since it doesn't come with the model
                # Populate note, using strings to identify fields rather than strict indices in case field order changes
                note.fields[note._field_index("Front")] = front
                note.fields[note._field_index("Back")] = back
                ## Set the tags (and add the new ones to the deck configuration
                tags = "Auto" # Multiple tags separated by whitespace
                note.tags = col.tags.canonify(col.tags.split(tags))
                m = note.note_type()
                m['tags'] = note.tags
                col.models.save(m)
                ## Add note to DB
                col.addNote(note)
                
            col.save() # Save changes to DB
        finally: # Should have this always run, otherwise, anki will get stuck        
            col.close() # Need this function, otherwise instance stays open
            return self

        

