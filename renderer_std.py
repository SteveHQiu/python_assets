#%% Imports
# Built-ins
import re, os
from cgitb import html
from typing import Union, Callable
from collections.abc import Iterable
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
import base64

# General
from bs4 import BeautifulSoup

# Math
from mathml2latex.mathml import process_mathml

# Internal modules
from internal_globals import MPATH, OENodeHeader, OENodePoint, insertSubstring

#%% Constants
GRAY = "#e8e8e8" # Can set to empty string to insert nothing
IMG_STYLING = "style='max-width:600px'"

#%% Classes
class StandardRenderer:
    """
    New instance created for each entry point 
    Acts as storage hub for information input/output for renderer functions
    """
    # FIXME - Move this portion to main so that you can type without circular import
    def __init__(self, node: OENodePoint):        
        self.node = node # Is an instance of OENodePoint, the entry point node
        self.fronthtml = ""
        self.backhtml = ""
        self.img_count_child = 0 # Image counter for each card to assign each image a unique identifier 
        self.img_count_sibling = 0 # Separate image counter for sibling to avoid interference with direct child images
    
    def resetHtml(self):
        self.fronthtml = ""
        self.backhtml = ""
    
    
    def renderHtmlMain(self):
        """
        Note that this method adds to the html attributes rather than overwrite them
        Use resetHtml() to reset front and back HTML if needed

        """
        # Add parent node rendering here or in a separate function
        front = "<ul>\n" # Open list for sibling nodes
        back = "<ul>\n" # Open list for sibling nodes
        for node in self.node.sibling_nodes:
            func = FUNCMAP[node.type] # Retrieve relevant function based on node type
            if self.node.id == node.id: # Node reponsible for entrypoint and called StandardRenderer
                front += func(node=node, front=True, level="entry", renderer=self) 
                back += func(node=node, front=False, level="entry", renderer=self) 
                if node.children_nodes: # Render direct children nodes
                    child_front = "\n<ul>\n" # Open list for direct children nodes
                    child_back = "\n<ul>\n" # Open list for direct children nodes
                    for child_node in node.children_nodes: 
                        cfunc = FUNCMAP[child_node.type] # Refetch relevant function for child node (otherwise will use parent type)
                        child_front += cfunc(node=child_node, front=True, level="direct_child", renderer=self) 
                        child_back += cfunc(node=child_node, front=False, level="direct_child", renderer=self)
                    child_front += "</ul>\n" # Close list for direct children nodes
                    child_back += "</ul>\n" # Close list for direct children nodes
                    front = insertSubstring(front, "</li>", child_front) 
                    back = insertSubstring(back, "</li>", child_back)
                # Children rendering handled by rendering functions, CardArbiter class handles recursive card creation hence rendering can do its own thing
            else: # Assume it is an sibling/adjacent node
                front += func(node=node, front=True, level="sibling", renderer=self) 
                back += func(node=node, front=False, level="sibling", renderer=self)
                # No need for children parsing for sibling nodes 
        front += "</ul>\n" # Close list for sibling nodes
        back += "</ul>\n" # Close list for sibling nodes
        
        self.fronthtml += front
        self.backhtml += back
        return self
    
    def renderHtmlParents(self):
        """
        Render parent nodes for entry node and add it to the generated HTML
        """
        
        # Parent node rendering
        for parent_node in self.node.parent_nodes: # Convert parent nodes into OENodePoint instances
            # Note that each node is wrapped around old node, furthest parent node is added last
            pfront = "<ul>\n" # Open list for parent node
            pback = "<ul>\n"
            # Make list item
            if self.node.type in ["grouping"] and parent_node.id == self.node.parent_nodes[0].id: # Checks if the parent node is the most immediate to entry point; if so, does special processing of immediate parent node if entry point is a grouping
                if parent_node.type in ["concept"]:
                    pfront += genHtmlElement(parent_node.stem, ["bold"], "", li=True, bullet=parent_node.bullet_data)
                    pback += genHtmlElement(parent_node.data, [], "", li=True, bullet=parent_node.bullet_data)
                elif parent_node.type in ["grouping"]:
                    pfront += genHtmlElement(parent_node.stem, ["underline"], "", li=True, bullet=parent_node.bullet_data)
                    pback += genHtmlElement(parent_node.data, [], "", li=True, bullet=parent_node.bullet_data)
            else: # Treat as a distant parent node
                if parent_node.type in ["concept"]:
                    pfront += genHtmlElement(parent_node.stem, ["bold"], GRAY, li=True, bullet=parent_node.bullet_data)
                    pback += genHtmlElement(parent_node.data, [], GRAY, li=True, bullet=parent_node.bullet_data)
                elif parent_node.type in ["grouping"]:
                    pfront += genHtmlElement(parent_node.stem, ["underline"], GRAY, li=True, bullet=parent_node.bullet_data)
                    pback += genHtmlElement(parent_node.data, [], GRAY, li=True, bullet=parent_node.bullet_data)
            pfront += "</ul>\n" # Close list for parent node (should only have 1 item), next level will have its own list
            pback += "</ul>\n"
            
            self.fronthtml = insertSubstring(pfront, "</li>", "\n" + self.fronthtml) # Wrap new HTML around previous HTML by inserting old into new
            self.backhtml = insertSubstring(pback, "</li>", "\n" + self.backhtml) # Most generated HTML elements will have \n at end so won't need to add one

        # Parent header rendering
        header = self.node.parent_headers[0] # Retrieve immediate header of the entry point
        header_html = genHtmlElement(header.page_title, ["italic"], GRAY) + "<br>\n" # Initialize HTML with title and newline 
        header_html += genHtmlElement(f"[{header.text}]", ["underline"], GRAY) # Add itself as the immediate header
        for pheader in header.parent_headers: # Add headers and links to respective element
            header_html += f" - [{pheader.text}]"
        header_html = genHtmlElement(header_html, [], GRAY) + "<br><br>\n" # Wrapped HTML with gray styling span 
        
        self.fronthtml = header_html + self.fronthtml # Add header rendering to front of HTML
        self.backhtml = header_html + self.backhtml
        
        return self
    

##%% Functions
import inspect
def getFxName(): # Function that will return name of currently calling function, for debug
    return inspect.stack()[1].function


def genHtmlElement(content: str, 
                style: list[str] = [],
                color: str = "",
                li: bool = False,
                bullet: str = "",
                ) -> str:
    """
    Generates HTML element with a variety of styling options. 
    Is to standardize HTML generation
    Defaults to return content variable with black color styling span (to prevent it from being colored by parent bullet color)

    Args:
        content (str): Actual str text data to render
        color (str, optional): Str for hex code of color. Defaults to "".
        style (List[str], optional): List of str for styling options (bold, underline, italic). Defaults to [].
        list (bool, optional): Whether to render the element as a list item, adds <li> and </li> at beginning and end of HTML string. Defaults to False.
        bullet (str, optional): Styling for list item if rendering a list item. Defaults to "". Will have no effect if list=False

    Returns:
        str: Final generated HTML element
    """
    html_item = "" # Initialize HTML container 
    if li:
        html_item += f"<li {bullet}>"
        if color: # Change color of bullet if there is a color argument passed
            if "style" in html_item: # If there is a styling element already
                html_item = insertSubstring(html_item, "'", f"; color:{color}") # Insert color property in styling element
            else:
                html_item = insertSubstring(html_item, ">", f"style='color:{color}'") # Create and insert new styling element with color
        else: # Assume color is black
            if "style" in html_item: # If there is a styling element already
                html_item = insertSubstring(html_item, "'", "; color:#000000") # Insert color property in styling element
            else:
                html_item = insertSubstring(html_item, ">", "style='color:#000000'") # Create and insert new styling element with color
            
                
        
    if style or color: # If style or color arguments not empty, add all applicable options below:
        html_item += "<span style='" # Open style attribute and span tag
        if "bold" in style:
            html_item += "font-weight:bold;"
        if "underline" in style:
            html_item += "text-decoration:underline;"
        if "italic" in style:
            html_item += "font-style:italic;"
        if color:
            html_item += f"color:{color};"
        else: # Otherwise color black
            html_item += f"color:#000000;"
        html_item += "'>" # Close style attribute and span tag
    else: # Assume no styling and color black (so that it won't be affected by bullet color)
        html_item += "<span style='color:#000000;'>" # Open style attribute and span tag
        
        
        
    html_item += content # CONTENT ADDED HERE
    
    if style or color: # Have to close styling span 
        html_item += "</span>"
        
    if li: # Will close automatically if there is a starting point 
        html_item += "</li>\n"
    return html_item


def genHtmlRecursively(node: OENodePoint, 
                       fx_genHtml: Callable,
                       data_atr: str = "data",
                       bul_atr: str = "bullet_data",
                       **kwargs) -> str:
    """Generates the HTML rendering of a node and all of its children recursively 
    using a HTML generating function and styling arguments

    Args:
        node (OENodePoint): Root node to render
        fx_genHtml: Function for generating the HTML string, kwargs will be fed into this function 
        data_atr: String that specifies where the content within the node lies (e.g., node.data, node.stem), defaults to node.data
        bul_atr: String that specifies where bullet styling lies defaults to node.bullet_data


    Returns:
        str: HTML str containing rendered root node and its children
    """
    # Main rendering logic (will be repeated during recursion)
    renderable_types = ["concept", "grouping", "standard"] # This filter applies on all instances of call, 
    html_item = ""
    if node.type in renderable_types and node.__getattribute__(data_atr).strip() != "": # Only render text type and not whitespace
        html_item += fx_genHtml(node.__getattribute__(data_atr), bullet=node.__getattribute__(bul_atr), **kwargs) # Defaults to rendering node.data and node.bullet_data     
           
    # Recursive logic
    if node.children_nodes:
        children_nodes = node.children_nodes # Convert each child node into OENodePoint
        has_renderable_children = any([cnode.type in renderable_types for cnode in children_nodes]) # Checks types of children nodes to see if they are renderable
        if has_renderable_children:
            html_children = "\n<ul>\n" # Open list
            for child_node in children_nodes:
                html_children += genHtmlRecursively(child_node, fx_genHtml, **kwargs) # Use same func and arguments as root since same type and same context 
            html_children += "</ul>\n" # Close list
            html_item = insertSubstring(html_item, "</li>", html_children) # Insert children into last item 
    return html_item

## Special rendering functions

def renderCloze(node: OENodePoint, front: bool, level: str, renderer: StandardRenderer, root: bool = True) -> str:
    if front:
        if level == "entry":
            return renderGrouping(node, front, level, renderer, root=False) # root=False to avoid re-running renderOptions()
        elif level == "direct_child":
            indicators = "".join(node.indicators)            
            return genHtmlElement(f"{indicators} |____:", ["underline"], li=True, bullet=node.bullet_data) # Add colon for prompting
        elif level == "sibling":
            return renderGrouping(node, front, level, renderer, root=False) # root=False to avoid re-running renderOptions()

    else: # Functions for rendering backside
        if level == "entry":
            return renderGrouping(node, front, level, renderer, root=False) # root=False to avoid re-running renderOptions()
        elif level == "direct_child":
            text_styled = genHtmlElement(node.stem, ["underline"], "") + genHtmlElement(node.body, [], GRAY) # Style stem and body differently
            return genHtmlElement(text_styled, [], "", li=True, bullet=node.bullet_data) # Create a greyed list item using styled text
        elif level == "sibling":
            return renderGrouping(node, front, level, renderer, root=False) # root=False to avoid re-running renderOptions()


def renderListed(node: OENodePoint, front: bool, level: str, renderer: StandardRenderer, root: bool = True) -> str:
    if front:
        if level == "entry":
            return renderGrouping(node, front, level, renderer, root=False) # root=False to avoid re-running renderOptions()
        elif level == "direct_child":
            return renderGrouping(node, front, "entry", renderer, root=False) # Run as if it was an entry-level node, root=False to avoid re-running renderOptions()
            return genHtmlElement(node.stem + ":", ["underline"], li=True, bullet=node.bullet_data) # Actual code from renderGrouping
        elif level == "sibling":
            return renderGrouping(node, front, level, renderer, root=False) # root=False to avoid re-running renderOptions()

    else: # Functions for rendering backside
        if level == "entry":
            return renderGrouping(node, front, level, renderer, root=False) # root=False to avoid re-running renderOptions()
        elif level == "direct_child":
            text = bool(node.children_nodes)*"(+)" + node.data # Branchless adding of children prefix 
            return genHtmlElement(text, [], "", li=True, bullet=node.bullet_data) # No formatting
        elif level == "sibling":
            return renderGrouping(node, front, level, renderer, root=False) # root=False to avoid re-running renderOptions()


def renderOptions(node: OENodePoint, front: bool, level: str, renderer: StandardRenderer) -> str:
    if {"C", "L"}.intersection(set(node.indicators)): # Pass arguments onto special rendering functions if there's overlap b/n indicators of interest and node indicators 
        if "C" in node.indicators:
            return renderCloze(node, front, level, renderer)
        if "L" in node.indicators:
            return renderListed(node, front, level, renderer)
    else:
        return ""

## Standard rendering functions

def renderConcept(node: OENodePoint, front: bool, level: str, renderer: StandardRenderer, root: bool = True) -> str:
    """
    root: Keeps track if the current instance of the call is from the root (i.e., call should check for options), 
    otherwise it will skip extra options and go straight to default method. Used for recursively falling back 
    to default options from a special rendering option (i.e., reuse a standard rendering function when certain 
    criteria are met)
    """
    if root and renderOptions(node, front, level, renderer): # Will only return true if node.indicators contain rendering options and has not previously called renderOptions
        # Note that root must be evaluated first, otherwise will try to evaluate function and enter infinite recursion
        # Not actually implemented in Concept-type nodes yet
        return renderOptions(node, front, level, renderer) # Use output from renderOptions() instead if applicable, otherwise go through default
    elif front:
        if level == "entry":
            return genHtmlElement("【" + node.stem + ":】", ["bold"], li=True, bullet=node.bullet_data) # Add unformatted colon for prompting
        elif level == "direct_child":
            return genHtmlElement("____:", ["bold"], li=True, bullet=node.bullet_data) # Add unformatted colon for prompting
        elif level == "sibling":
            return genHtmlElement(node.stem, ["bold"], GRAY, li=True, bullet=node.bullet_data) 

    else: # Functions for rendering backside
        if level == "entry":
            return genHtmlElement("【" + node.data + ":】", li=True, bullet=node.bullet_data) # Convert to list item but keep raw data
        elif level == "direct_child":
            text_styled = genHtmlElement(node.stem, ["bold"], "") + genHtmlElement(node.body, [], GRAY) # Style stem and body differently
            return genHtmlElement(text_styled, [], "", li=True, bullet=node.bullet_data) # Wrap styled text in list tags
        elif level == "sibling":
            text = bool(node.children_nodes)*"(+)" + node.data # Branchless adding of children prefix 
            return genHtmlElement(text, [], GRAY, li=True, bullet=node.bullet_data) 


def renderGrouping(node: OENodePoint, front: bool, level: str, renderer: StandardRenderer, root: bool = True) -> str:
    if root and renderOptions(node, front, level, renderer): # Will only return true if node.indicators contain rendering options
        # Note that root must be evaluated first, otherwise will try to evaluate function and enter infinite recursion
        return renderOptions(node, front, level, renderer) # Use output from renderOptions() instead if applicable, otherwise go through default
    if front:
        if level == "entry":
            return genHtmlElement("【" + node.stem + ":】", ["underline"], li=True, bullet=node.bullet_data) # Add colon for prompting
        elif level == "direct_child":
            return "" # Ignore regular Grouping-type nodes
        elif level == "sibling":
            return genHtmlElement(node.stem, ["underline"], GRAY, li=True, bullet=node.bullet_data) 

    else: # Functions for rendering backside
        if level == "entry":
            return genHtmlElement("【" + node.data + ":】", li=True, bullet=node.bullet_data) # Convert to list item but keep raw data
        elif level == "direct_child":
            text = bool(node.children_nodes)*"(+)" + node.data # Branchless adding of children prefix 
            return genHtmlElement(text, [], GRAY, li=True, bullet=node.bullet_data) 
        elif level == "sibling":
            text = bool(node.children_nodes)*"(+)" + node.data # Branchless adding of children prefix 
            return genHtmlElement(text, [], GRAY, li=True, bullet=node.bullet_data) 


def renderNormalText(node: OENodePoint, front: bool, level: str, renderer: StandardRenderer, root: bool = True) -> str:
    if front:
        if level == "entry":
            return "" # Shouldn't have normal text as entry point
        elif level == "direct_child":
            return genHtmlElement("Subpoint", ["italic"], li=True, bullet=node.bullet_data) # Italicized placeholder
        elif level == "sibling":
            return "" # Ignore

    else: # Functions for rendering backside
        if level == "entry":
            return "" # Shouldn't have normal text as entry point
        elif level == "direct_child":
            return genHtmlRecursively(node, genHtmlElement, style=[], color="", li=True) # Render node and children with original format
        elif level == "sibling":
            return genHtmlRecursively(node, genHtmlElement, style=[], color=GRAY, li=True)


def renderImage(node: OENodePoint, front: bool, level: str, renderer: StandardRenderer, root: bool = True) -> str:
    def genImageName(node: OENodePoint) -> str:
        re_punct = re.compile('[\W_]+') # Regexp that matches any non-alphanumeric
        title = node.parent_headers[0].page_title # Use first node's page title
        img_name = re_punct.sub("", title)[:30] # Instantiate img_name string with first 30 chars of title (with punct removed)
        for h_node in node.parent_headers:
            img_name += re_punct.sub("", h_node.text)[:20] # Add first 20 chars of each header to img_name
        for p_node in node.parent_nodes: # Should only have Concept and Grouping-type nodes as parents
            img_name += re_punct.sub("", p_node.stem)[:20] # Add first 20 chars of stem to img_name
            # Each node has relevant parent_node information encoded, hence this function doesn't need to take into account the level argument
        return img_name[:190] # Return first 190 characters - Windows allows for 255 max characters for absolute path, give ~60 chars for dir path
        # Media folder (60 characters): C:\Users\steve\AppData\Roaming\Anki2\User 1\collection.media
    
    if front:
        if level == "entry":
            return "" # Shouldn't have image as entry point, unless there's a specific function (e.g., name this picture)
        elif level == "direct_child":
            return genHtmlElement("Image", ["italic"], li=True, bullet=node.bullet_data) # Italicized placeholder
        elif level == "sibling":
            return "" # Ignore

    else: # Functions for rendering backside
        if level == "entry":
            return "" # Shouldn't have image as entry point, unless there's a specific function (e.g., name this picture)
        elif level == "direct_child":
            renderer.img_count_child += 1
            img_name = genImageName(node) + str(renderer.img_count_child) + ".png" # Append img_count to make it a unique name
        elif level == "sibling":
            renderer.img_count_sibling += 1
            img_name = genImageName(node) + str(renderer.img_count_sibling) + ".png" 
        
        # Common image generation path
        img_path = os.path.join(MPATH, img_name)
        img_data_bytes = node.data.encode("utf-8")
        with open(img_path, "wb") as file:
            file.write(base64.decodebytes(img_data_bytes)) # Convert bytes format to base64 format which is read by write() functio
        return genHtmlElement(f"<img src='{img_name}' {IMG_STYLING}>", [], "", li=True, bullet=node.bullet_data)


def renderEquation(node: OENodePoint, front: bool, level: str, renderer: StandardRenderer, root: bool = True) -> str:
    if front:
        if level == "entry":
            return "" # Shouldn't have equation as entry point
        elif level == "direct_child":
            return genHtmlElement("Equation", ["italic"], li=True, bullet=node.bullet_data) # Italicized placeholder
        elif level == "sibling":
            return "" # Ignore

    else: # Functions for rendering backside
        if level == "entry":
            return "" # Shouldn't have equation as entry point
        elif level == "direct_child":
            pass # Pass onto common processing
        elif level == "sibling":
            pass # Pass onto common processing
        
        math_str = node.data.replace("<!--[if mathML]>", "").replace("<![endif]-->", "") # Replace end tags
        html_tags: list[str] = re.findall("<.*?>", math_str) # Finds all HTML tags
        for tag in html_tags: # Iterate through matches to replace namespace component (no easy regex way to do it)
            new_tag = tag.replace("mml:", "")
            math_str = math_str.replace(tag, new_tag, 1) # Replace first instance of the match with new tag
        soup = BeautifulSoup(math_str, features="html.parser")
        latex = "<anki-mathjax>" + str(process_mathml(soup)) + "</anki-mathjax>" # Conversion to string just in case conversion fails
        return genHtmlElement(latex, [], li=True, bullet=node.bullet_data)
        

def renderTable(node: OENodePoint, front: bool, level: str, renderer: StandardRenderer, root: bool = True) -> str:
    if front:
        if level == "entry":
            return "" # Shouldn't have table as entry point in standard renderer
        elif level == "direct_child":
            return "" # Ignore
        elif level == "sibling":
            return "" # Ignore

    else: # Functions for rendering backside
        if level == "entry":
            return "" # Shouldn't have table as entry point in standard renderer
        elif level == "direct_child":
            return genHtmlElement("Table", ["italic"], li=True, bullet=node.bullet_data) # Italicized placeholder
        elif level == "sibling":
            return genHtmlElement("Table", ["italic"], li=True, bullet=node.bullet_data) # Italicized placeholder


def ignoreNode(node: OENodePoint, front: bool, level: str, renderer: StandardRenderer, root: bool = True) -> str:
    if front:
        if level == "entry":
            return ""
        elif level == "direct_child":
            return ""
        elif level == "sibling":
            return ""

    else: # Functions for rendering backside
        if level == "entry":
            return ""
        elif level == "direct_child":
            return ""
        elif level == "sibling":
            return ""


FUNCMAP = {
            "concept": renderConcept,
            "grouping": renderGrouping,
            "standard": renderNormalText,
            "image": renderImage,
            "equation": renderEquation,
            "table": renderTable,
            "": ignoreNode,
        } # Mapping of node type label to corresponding function 



# %%
