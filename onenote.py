#%% Imports
# Built-in
import sys, os, base64, re, string, copy
from typing import Union
from collections.abc import Iterable
from uuid import getnode
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from urllib.parse import quote

# General
from bs4 import BeautifulSoup

# Anki
from anki.storage import Collection

#%% Constants
NAMESPACES = {"one": R"http://schemas.microsoft.com/office/onenote/2013/onenote"} # Namespace to prefix tags, may change if API changes


""" Extra notes
To fix XML file
Find:
([^>])\n
Replace: 
$1 
Test
"""

#%% Classes

class OENodePoint:
    """
    Parses an XML OE item from the OneNote export
    """
    def __init__(self, oenode: Element):
        self.id: str | None = oenode.get("objectID") # ID is an attribute of the XML node
        self.xml: Element = oenode # Store original XML node in case needed
        self.bullet_data: str = _getBulletData(oenode)
        
        self.type, self.data = _getNodeTypeAndData(oenode) # Unpack tuple into type and data
        self.stem, self.body = _getStemAndBody(oenode) # Unpack tuple into stem and body
        self.indicators: list[str] = _getIndicators(oenode)
        
        # Attributes below are populated recursively in getChildren()
        self.page_title: str = ""
        self.parent_headers: list[OENodeHeader] = [] # For use in inner scope (i.e., naming images), passed from genCards in cardarbiter
        self.sibling_nodes: list[OENodePoint] = [] # Contains all nodes at same level - .children_nodes of parent node gets passed here
        self.parent_nodes: list[OENodePoint] = [] # For parent context rendering
        self.children_nodes: list[OENodePoint] = [] # 

class OENodeHeader:
    """
    Separate class for OE nodes for headers 
    """
    def __init__(self, header_node: Element):
        # Should only be instantiated on non-empty headers with children
        self.id: str | None = header_node.get("objectID") # ID is an attribute of the XML node
        self.xml: Element = header_node
        self.text: str = _getNodeText(header_node)
        self.level: int = int(header_node.get("quickStyleIndex"))
        self.link: str = header_node.get("objectLink") # Is generated via C# interop API and embedded into XML export
        
        self.page_title: str = "" # Populated by outer scope getHeaders
        self.parent_pages: list[Element] = [] # Populated by outer scope getHeaders
        self.parent_headers: list[OENodeHeader] = [] # Populated by outer scope getHeaders
        self.children_nodes: list[OENodeHeader] = [] # Populated by outer scope getHeaders

def _getBulletData(node: Element) -> str:
    """
    
    """
    if node.find("one:List/one:Number", NAMESPACES) != None:
        if "restartNumberingAt" in node.find("one:List/one:Number", NAMESPACES).attrib: # Search for restart numbering attribute in tag: https://stackoverflow.com/questions/10115396/how-to-test-if-an-attribute-exists-in-some-xml
            number = node.find("one:List/one:Number", NAMESPACES).attrib["restartNumberingAt"]
            return f"value={number}; style='list-style-type: decimal'"
        else: # Assume that ordered item does not need to be reordered
            return "style='list-style-type: decimal'"
    else: # Otherwise assumed to be an unordered item
        return ""
    # Styling can be modified in-line with HTML styling attribute which supports CSS styling directly inside: https://www.w3schools.com/tags/att_style.asp


def _getNodeText(node: Element) -> str:
    node_content = node.find("one:T", NAMESPACES)
    if node_content != None and node_content.text != None:
        # The .text attribute of one:T elements contains the raw text (Without CDATA wrapper)
        return node_content.text 
    else:
        return "" # Returns empty string which will evaluate as False when passed as a logical argument

def _getNodeTypeAndData(node: Element) -> tuple[str, str]: 
    """Gets node type and corresponding data from an XML node element

    Args:
        node (Element): XML node element from OneNote export

    Returns:
        tuple[str, str]: 1st str contains the node type, 2nd contains the corresponding data in string format. Otherwise returns tuple of None
    """
    
    if node.find("one:T", NAMESPACES) != None and node.find("one:T", NAMESPACES).text != None: # Must have text
        text = node.find("one:T", NAMESPACES).text # Remember that text is stored under text property, the object itself is an instance of Element (XML)
        soup = BeautifulSoup(text, features="html.parser")
        if soup.text.strip() != "": # Only assign text type if rendering text is not just whitespace
            # Note that select() methods can search via styling while find() methods seem to capture the whole element that matches search
            if soup.select_one('span[style*="font-weight:bold"]') != None:
                return ("concept", text)
            elif soup.select_one('span[style*="text-decoration:underline"]') != None:
                return ("grouping", text)
            else: 
                return ("standard", text)
        # soup.text should return empty for math-only nodes, hence subsequent processing will be for math-only nodes, all other text-type nodes will have inline math support
        elif "http://www.w3.org/1998/Math/MathML" in text and "mathML" in text: # bs4 output for equations are blank
            return ("equation", text)
        
        
    elif node.find("one:Image/one:Data", NAMESPACES) != None and node.find("one:Image/one:Data", NAMESPACES).text != None: # Image nodes
        image_data = node.find("one:Image/one:Data", NAMESPACES).text
        return ("image", image_data)
        
    elif node.find("one:Table", NAMESPACES) != None and node.find("one:Table/one:Row", NAMESPACES) != None: # Table nodes
        # FIXME - Way to to screen for table
        return ("table", "placeholder data")
    
    return ("", "") # Returns two empty strings which evaluate as false when passed as logical arguments

def _getStemAndBody(node: Element) -> tuple[str, str]:
    node_type, node_data = _getNodeTypeAndData(node)
    if node_type == "concept":
        soup = BeautifulSoup(node_data, features="html.parser")
        stem_tag = soup.select_one('span[style*="font-weight:bold"]') # Returns first tag that matches selector which searches for tags with attributes containing "font-weight:bold"
        stem = stem_tag.text
        stem_tag.decompose() # Deletes tag from soup variable
        body = soup.text # Use updated soup variable to assign the body text
        return (stem, body)
    elif node_type == "grouping":
        soup = BeautifulSoup(node_data, features="html.parser")
        stem_tag = soup.select_one('span[style*="text-decoration:underline"]') # Returns first tag that matches selector
        stem = stem_tag.text
        stem_tag.decompose() # Deletes tag from soup variable
        body = soup.text # Use updated soup variable to assign the body text
        return (stem, body)
    else:
        return ("", "")

def _getIndicators(node: Element) -> list[str]:
    if _getStemAndBody(node)[0] and re.match(R"(\w+) ?\|", _getStemAndBody(node)[0]) != None: # Generalized for any stems in case of additional expansions
        indicator_str = re.match(R"(\w+) ?\|", _getStemAndBody(node)[0]).group(1)
        return list(indicator_str) # Convert indicators into set of characters
    else:
        return list() # Return an empty set for indicators otherwise


def getHeaders(page_xml: ElementTree.ElementTree, outline_xml: ElementTree.ElementTree) -> list[OENodeHeader]:
    """
    Returns list of XML items of non-empty headers from XML and populates their parent trackers
    xml_file: path to XML file from OneNote output
    """
    # Page title processing
    page_title, page_id = _getTitleAndID(page_xml)
    parent_page_map = {child: parent for parent in outline_xml.iter() for child in parent} # Create child-parent map to get a page's parent section (no convenient way to find parents otherwise)
    outline_pages = outline_xml.findall(R".//one:Page", NAMESPACES)
    current_page = outline_xml.find(fR".//one:Page[@ID='{page_id}']", NAMESPACES)
    index = outline_pages.index(current_page)
    parent_pages: list[Element] = [] 
    current_page_level = current_page.get("pageLevel")
    for i in range(index, 0, -1): # Is a repeat of process for determining header hierarchy done below
        if outline_pages[i-1].get("pageLevel") < current_page_level:
            current_page_level = outline_pages[i-1].get("pageLevel") # Set new higher page level
            parent_pages.append(outline_pages[i-1]) # Append entire Element, will have to retrieve later 
            
    
    # Header instantiation
    list_page_boxes = page_xml.findall("one:Outline/one:OEChildren", NAMESPACES) # Returns OEChildren Element containing an OE for each header 
    # Note that each outline (page box) only has a SINGLE one:Children
    styled_headers: list[OENodeHeader] = [] # Is not always a superset of iterable headers (e.g., in the case of unstyled headers which are still iterable if they contain child nodes)
    iterable_headers: list[OENodeHeader] = []
    for header_node in (header for list_headers in list_page_boxes for header in list_headers): # First variable is assignment statement, then starts outer loops going to inner loops: https://www.geeksforgeeks.org/nested-list-comprehensions-in-python/
        if _getNodeText(header_node): # Only parse non-empty nodes
            header_node = OENodeHeader(header_node)
            if header_node.xml.get("quickStyleIndex") not in [2, None]: # Quick styles #2 is normal text, 1st order is #1, 2nd order is #3 (skips over #2) and so on 
                styled_headers.append(header_node) 
            if header_node.xml.find("one:OEChildren", NAMESPACES): # Is iterable if there are children, can't use getChildren here, otherwise will enter recursion before all fields are populated
                iterable_headers.append(header_node) # Convert to OENodeHeader before appending
                print("Found non-empty header: " + header_node.text)
            
    styled_header_ids = [s_header.id for s_header in styled_headers] 
    
    # POPULATE PLACEHOLDER ATTRIBUTES (.page_title, .parent_headers, .children_nodes)
    for header in iterable_headers: 
        header.page_title = page_title # Populate title property of instantiated OENodeHeader
        header.parent_pages = parent_pages
        if header.id in styled_header_ids: # Search for iterable header in styled header list using IDs (since objects are not equal even if they have the same values)
            index = styled_header_ids.index(header.id) # Index used for identifying parent headers in flattened header list 
        else:
            index = 0 # Otherwise skip header 
        current_level = header.level # Tracks current level of header
        for i in range(index, 0, -1): # step=-1 makes index decrease instead of increasing
            if styled_headers[i-1].level < current_level: 
                # Checks if styled header directly above is hierarchically higher (i.e., lower style #) than headers that we've seen, will stop at level=1 since there is no level=0
                current_level = styled_headers[i-1].level # If header above is higher, set new current level
                header.parent_headers.append(styled_headers[i-1]) # Add the above header as a parent header
        
        # Children populated last since it requires previous fields to be populated first (in order to pull from them)
        header.children_nodes = _getChildren(header) # Recursively instantiates children as OENodePoints
    return iterable_headers # Return processed iterable_headers

def _getTitleAndID(page_xml: ElementTree.ElementTree) -> tuple[str, str]:
    """
    Returns string of title of page being parsed 
    """
    page_id = page_xml.getroot().get("ID")
    print(f"Page ID: {page_id}")
    if page_xml.find("one:Title/one:OE/one:T", NAMESPACES) != None:
        page_title = page_xml.find("one:Title/one:OE/one:T", NAMESPACES).text
    else: 
        page_title = "Untitled"
    return (page_title, page_id)

def _getChildren(header_node: OENodeHeader) -> list[OENodePoint]:
    """Gets children of the given node if it exist, otherwise returns False
    IS THE ENTRY POINT FOR INITIALIZATION OF ALL OENodePoint instances as this function is recursively called during OENodePoint instantiation from iterating over headers
    Outer function starts with header node while inner recursive function handles both headers and points 
    
    Args:
        node (Element): XML node element

    Returns:
        Iterable[Element]: Returns the XML element (OEChildren) which contains the children nodes
    """
    
    parent_node_tracker: list[OENodePoint] =  [] # For use by inner function
    
    def _iterChildren(node: OENodeHeader | OENodePoint) -> list[OENodePoint]:
        # Only assign children if they exist
        if node.xml.find("one:OEChildren", NAMESPACES):
            if type(node) == OENodePoint: # Only add node to parent tracker if current node is a point (rather than a header)
                parent_node_tracker.insert(0, node)
                
            child_nodes = [OENodePoint(cnode) for cnode in node.xml.find("one:OEChildren", NAMESPACES)] # List comprehensions less prone to breaking than generators
            for child_node in child_nodes:
                if type(node) == OENodeHeader:
                    child_node.parent_headers = [node] # Inherit directly from header since its .parents_headers may be empty if it's a top-level header
                elif type(node) == OENodePoint:
                    child_node.parent_headers = node.parent_headers # Inherit from parent node which will have inherited it from immediate header
                child_node.page_title = node.page_title # Inherit from parent
                child_node.sibling_nodes = child_nodes # Assign current node's children container, list doesn't get modified so don't need to copy (each cycle creates new list)
                child_node.parent_nodes = copy.copy(parent_node_tracker) # Copy tracker nodes using shallow copy since tracker gets modified by outer scope
                child_node.children_nodes = _iterChildren(child_node) # Recursively call function, will rebound from recursion at nodes without children
                
            if type(node) == OENodePoint: # Mirror entry conditions
                parent_node_tracker.pop(0)
                
            return child_nodes # List comprehensions less prone to breaking than generators
        
        else: 
            return [] # Empty list which will evaluate as False when passed as a logical argument
    
    return _iterChildren(header_node)

def getParentNames(page_xml: ElementTree.ElementTree, outline_xml: ElementTree.ElementTree):
    page_title, page_id = _getTitleAndID(page_xml)
    parent_page_map = {child: parent for parent in outline_xml.iter() for child in parent} # Create child-parent map to get a page's parent section (no convenient way to find parents otherwise)
    node_page = outline_xml.find(F".//one:Section/one:Page[@ID='{page_id}']", NAMESPACES) # Returns OEChildren Element containing an OE for each header 
    
    parent_sections: list[Element] = []
    node_focused = node_page  
      
    while "Notebook" not in node_focused.tag: # Look up until reaching notebook level # E.g., '{http://schemas.microsoft.com/office/onenote/2013/onenote}Notebook'
        print(node_focused.tag) 
        node_focused = parent_page_map[node_focused] # Get parent node
        parent_sections.insert(0, node_focused) # Append parent node to front of container
    
    parent_names = [n.get("name") if not n.get("nickname") else n.get("nickname")
           for n in parent_sections] # Get nickname if available
    
    return parent_names

#%% Testing:
if __name__ == "__main__":
    page_xml: ElementTree.ElementTree = ElementTree.parse(R"data\page_xml.xml")
    outline_xml: ElementTree.ElementTree = ElementTree.parse(R"data\outline_xml.xml")
    
    print(getParentNames(page_xml, outline_xml))
    
#%%
