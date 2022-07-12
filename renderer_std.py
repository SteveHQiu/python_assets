#%% Imports
# Built-ins
from cgitb import html
from typing import Union, Tuple, List
from collections.abc import Iterable
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

# General
from bs4 import BeautifulSoup

# Internal modules
from globals import OENodePoint


#%% Constants
GRAY = "#e8e8e8" # Can set to empty string to insert nothing

#%% Functions
import inspect
def getFxName(): # Function that will return name of currently calling function, for debug
    return inspect.stack()[1].function


def renderHeaders(node: Element) -> str:
    """
    Will take header element and render
    """
    return "Test header annotation"

def genHtmlElement(content: str, 
                style: List[str] = [],
                color: str = "",
                start: bool = False,
                bullet: str = "",
                close: bool = False,
                ) -> str:
    """
    Generates HTML element with a variety of styling options
    Is to standardize HTML generation, default is to just return content variable

    Args:
        content (str): Actual str text data to render
        bullet_data (str, optional): Styling for list item if rendering a list item. Defaults to "".
        color (str, optional): Str for hex code of color. Defaults to "".
        style (List[str], optional): List of str for styling options (bold, underline, italic). Defaults to [].
        start (bool, optional): Whether to add <li> tag at the beginning for list items. Defaults to True.
        close (bool, optional): Whether to add </li> tag closure at end - usually handled by outer functions since may need to handle nested lists. Defaults to False.

    Returns:
        str: Final generated HTML element
    """
    html_item = "" # Initialize HTML container 
    if start:
        html_item += F"<li {bullet}>" 
        
    if style or color: # If style or color arguments not empty, add all applicable options below:
        html_item += "<span style='" # Open style attribute and span tag
        if "bold" in style:
            html_item += "font-weight:bold;"
        if "underline" in style:
            html_item += "text-decoration:underline;"
        if "italic" in style:
            html_item += "font-style: italic;"
        if color:
            html_item += F"color:{color};"
        html_item += "'>" # Close style attribute and span tag
        
    html_item += content # CONTENT ADDED HERE
    
    if style or color: # Have to close styling span 
        html_item += "</span>"
    if close:
        html_item += "</li>"
    return html_item

## Special rendering functions

def renderCloze(node: OENodePoint, front: bool, level: str, root: bool = True) -> str:
    if front:
        if level == "entry":
            return renderGrouping(node, front, level, root=False) # root=False to avoid re-running renderOptions()
        elif level == "direct_child":
            indicators = "".join(node.indicators)
            return genHtmlElement(F"{indicators} |____", ["underline"], start=True, bullet=node.bullet_data) + ":" # Add colon for prompting
        elif level == "sibling":
            return renderGrouping(node, front, level, root=False) # root=False to avoid re-running renderOptions()
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"
    else: # Functions for rendering backside
        if level == "entry":
            return
        elif level == "direct_child":
            return
        elif level == "sibling":
            return
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"

def renderListed(node: OENodePoint, front: bool, level: str, root: bool = True) -> str:
    if front:
        if level == "entry":
            return renderGrouping(node, front, level, root=False) # root=False to avoid re-running renderOptions()
        elif level == "direct_child":
            return renderGrouping(node, front, "entry", root=False) # Run as if it was an entry-level node, root=False to avoid re-running renderOptions()
            return genHtmlElement(node.stem, ["underline"], start=True, bullet=node.bullet_data) + ":" # Actual code from renderGrouping
        elif level == "sibling":
            return renderGrouping(node, front, level, root=False) # root=False to avoid re-running renderOptions()
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"
    else: # Functions for rendering backside
        if level == "entry":
            return
        elif level == "direct_child":
            return
        elif level == "sibling":
            return
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"

def renderOptions(node: OENodePoint, front: bool, level: str) -> str:
    if {"C", "L"}.intersection(set(node.indicators)): # Pass arguments onto special rendering functions if there's overlap b/n indicators of interest and node indicators 
        if "C" in node.indicators:
            return renderCloze(node, front, level)
        if "L" in node.indicators:
            return renderListed(node, front, level)
    else:
        return ""

## Standard rendering functions

def renderConcept(node: OENodePoint, front: bool, level: str, root: bool = True) -> str:
    """
    root: Keeps track if the current instance of the call is from the root (i.e., call should check for options), 
    otherwise it will skip extra options and go straight to default method. Used for recursively falling back 
    to default options from a special rendering option (i.e., reuse a standard rendering function when certain 
    criteria are met)
    """
    if renderOptions(node, front, level) and root: # Will only return true if node.indicators contain rendering options and has not previously called renderOptions
        # Not actually implemented in Concept-type nodes yet
        return renderOptions(node, front, level) # Use output from renderOptions() instead if applicable, otherwise go through default
    elif front:
        if level == "entry":
            return genHtmlElement(node.stem, ["bold"], start=True, bullet=node.bullet_data) + ":" # Add colon for prompting
        elif level == "direct_child":
            return genHtmlElement("____", ["bold"], start=True, bullet=node.bullet_data) + ":" # Add colon for prompting
        elif level == "sibling":
            return genHtmlElement(node.stem, ["bold"], GRAY, start=True, bullet=node.bullet_data) 
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"
    else: # Functions for rendering backside
        if level == "entry":
            return
        elif level == "direct_child":
            return
        elif level == "sibling":
            return
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"

def renderGrouping(node: OENodePoint, front: bool, level: str, root: bool = True) -> str:
    if renderOptions(node, front, level): # Will only return true if node.indicators contain rendering options
        return renderOptions(node, front, level) # Use output from renderOptions() instead if applicable, otherwise go through default
    if front:
        if level == "entry":
            return genHtmlElement(node.stem, ["underline"], start=True, bullet=node.bullet_data) + ":" # Add colon for prompting
        elif level == "direct_child":
            return "" # Ignore regular Grouping-type nodes
        elif level == "sibling":
            return genHtmlElement(node.stem, ["underline"], GRAY, start=True, bullet=node.bullet_data) 
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"
    else: # Functions for rendering backside
        if level == "entry":
            return
        elif level == "direct_child":
            return
        elif level == "sibling":
            return
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"

def renderNormalText(node: OENodePoint, front: bool, level: str, root: bool = True) -> str:
    if front:
        if level == "entry":
            return "" # Shouldn't have normal text as entry point
        elif level == "direct_child":
            return genHtmlElement("Subpoint", ["italic"], start=True, bullet=node.bullet_data) # Italicized placeholder
        elif level == "sibling":
            return "" # Ignore
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"
    else: # Functions for rendering backside
        if level == "entry":
            return
        elif level == "direct_child":
            return
        elif level == "sibling":
            return
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"

def renderImage(node: OENodePoint, front: bool, level: str, root: bool = True) -> str:
    if front:
        if level == "entry":
            return "" # Shouldn't have image as entry point
        elif level == "direct_child":
            return genHtmlElement("Image", ["italic"], start=True, bullet=node.bullet_data) # Italicized placeholder
        elif level == "sibling":
            return "" # Ignore
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"
    else: # Functions for rendering backside
        if level == "entry":
            return
        elif level == "direct_child":
            return
        elif level == "sibling":
            return
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"

def renderEquation(node: OENodePoint, front: bool, level: str, root: bool = True) -> str:
    if front:
        if level == "entry":
            return "" # Shouldn't have equation as entry point
        elif level == "direct_child":
            return genHtmlElement("Equation", ["italic"], start=True, bullet=node.bullet_data) # Italicized placeholder
        elif level == "sibling":
            return "" # Ignore
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"
    else: # Functions for rendering backside
        if level == "entry":
            return
        elif level == "direct_child":
            return
        elif level == "sibling":
            return
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"

def renderTable(node: OENodePoint, front: bool, level: str, root: bool = True) -> str:
    if front:
        if level == "entry":
            return "" # Shouldn't have table as entry point in standard renderer
        elif level == "direct_child":
            return genHtmlElement("Table", ["italic"], start=True, bullet=node.bullet_data) # Italicized placeholder
        elif level == "sibling":
            return "" # Ignore
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"
    else: # Functions for rendering backside
        if level == "entry":
            return
        elif level == "direct_child":
            return
        elif level == "sibling":
            return
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"

def ignoreNode(node: OENodePoint, front: bool, level: str, root: bool = True) -> str:
    if front:
        if level == "entry":
            return ""
        elif level == "direct_child":
            return ""
        elif level == "sibling":
            return ""
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"
    else: # Functions for rendering backside
        if level == "entry":
            return ""
        elif level == "direct_child":
            return ""
        elif level == "sibling":
            return ""
        else: # Insert error message
            return "<li>ERROR: Unable to parse node level"




#%% Classes
class StandardRenderer:
    """
    New instance created for each entry point 
    """
    # FIXME - Move this portion to main so that you can type without circular import
    def __init__(self, node: OENodePoint):        
        self.node = node # Is an instance of OENodePoint, the entry point node
        self.funcmap = {
            "concept": renderConcept,
            "grouping": renderGrouping,
            "standard": renderNormalText,
            "image": renderImage,
            "equation": renderEquation,
            "table": renderTable,
            "": ignoreNode,
        } # Mapping of node type label to corresponding function 
        self.fronthtml = ""
        self.backhtml = ""
    
    def resetHtml(self):
        self.fronthtml = ""
        self.backhtml = ""
    
    def renderParents(self):
        pass
    
    def renderHtml(self):
        """
        Note that this method adds to the html attributes rather than overwrite them
        Use resetHtml() to reset front and back HTML if needed

        """
        # Add parent node rendering here or in a separate function
        front = "<ul>\n" # Open list for sibling nodes
        back = "<ul>\n" # Open list for sibling nodes
        for node in (OENodePoint(node) for node in self.node.sibling_nodes): # Convert to OENodePoint within generator expression
            func = self.funcmap[node.type] # Retrieve relevant function based on node type
            if self.node.id == node.id: # Node reponsible for entrypoint and called StandardRenderer
                front += func(node, True, "entry") # Has <li> start tag but needs closure
                back += func(node, False, "entry") # Has <li> start tag but needs closure
                if node.children_nodes: # Render direct children nodes
                    front = "<ul>\n" # Open list for direct children nodes
                    back = "<ul>\n" # Open list for direct children nodes
                    for child_node in (OENodePoint(cnode) for cnode in node.children_nodes): # Convert each child node into OENodePoint
                        cfunc = self.funcmap[child_node.type] # Refetch relevant function for child node (otherwise will use parent type)
                        front += cfunc(child_node, True, "direct_child") + "</li>\n"*bool(cfunc(child_node, True, "direct_child")) # Branchless conditional list item closure
                        back += cfunc(child_node, False, "direct_child") + "</li>\n"*bool(cfunc(child_node, False, "direct_child")) # Branchless conditional list item closure
                    front = "</ul>\n" # Close list for direct children nodes
                    back = "</ul>\n" # Close list for direct children nodes
                front += "</li>\n"*bool(func(node, True, "entry")) # Branchless conditional list item closure (refers to function at start of if statement)
                back += "</li>\n"*bool(func(node, False, "entry")) # Branchless conditional list item closure (refers to function at start of if statement)
                # Children rendering handled by rendering functions, CardArbiter class handles recursive card creation hence rendering can do its own thing
            else: # Assume it is an sibling/adjacent node
                front += func(node, True, "sibling") + "</li>\n"*bool(func(node, True, "sibling")) # Branchless conditional list item closure
                back += func(node, False, "sibling") + "</li>\n"*bool(func(node, False, "sibling")) # Branchless conditional list item closure
                # No need for children parsing for sibling nodes 
        front = "</ul>\n" # Close list for sibling nodes
        back = "</ul>\n" # Close list for sibling nodes
        # Note that even without branchless closure, extra </li> tag won't affect rendering when node is ignored by the renderer function
        
        self.fronthtml += front
        self.backhtml += back
        return self
    
    

