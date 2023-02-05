# Built-in
import os
from typing import Union
from collections.abc import Iterable
from xml.etree import ElementTree
from xml.etree.ElementTree import Element


# Anki


# Internal modules
# from . import internal_globals, renderer_std
from renderer import StandardRenderer
from onenote import OENodeHeader, OENodePoint, getHeaders
from anki_api import ProtoNote, addCardsFromNotes

#%% Classes

class CardGenerator:
    
    def __init__(self, xml_path: Union[str, bytes, os.PathLike], outline_path: Union[str, bytes, os.PathLike]):
        self.outline: ElementTree.ElementTree = ElementTree.parse(outline_path)
        self.page: ElementTree.ElementTree = ElementTree.parse(xml_path)
        self.header_list: list[OENodeHeader] = getHeaders(self.page, self.outline) # Input header list, should be able to access rest of nodes through this point
        self.notes: list[ProtoNote] = [] # Container for generated cards, format of Tuple[front, back]

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
                    note = ProtoNote(renderer.fronthtml, renderer.backhtml)
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
        addCardsFromNotes(self.notes)
        

        


#%%
