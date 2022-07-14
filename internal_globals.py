#%% Imports
# Built-in
import sys, os, base64, re, string
from typing import Union
from collections.abc import Iterable
from uuid import getnode
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

# General
from bs4 import BeautifulSoup

# Anki
from anki.storage import Collection


#%% Constants


PROFILE_HOME = os.path.expanduser(R"~\AppData\Roaming\Anki2\User 1")
CPATH = os.path.join(PROFILE_HOME, "collection.anki2")
MPATH = os.path.join(PROFILE_HOME, "collection.media")
NAMESPACES = {"one": R"http://schemas.microsoft.com/office/onenote/2013/onenote"} # Namespace to prefix tags, may change if API changes

""" Extra notes
To fix XML file
Find:
([^>])\n
Replace: 
$1 

"""

#%% Global Classes
class OENodePoint:
    """
    Parses an XML OE item from the OneNote export
    """
    def __init__(self, oenode):
        self.id = oenode.get("objectID") # ID is an attribute of the XML node
        self.xml = oenode # Store original XML node in case needed
        self.bullet_data = getBulletData(oenode)
        
        self.type, self.data = getNodeTypeAndData(oenode) # Unpack tuple into type and data
        self.stem, self.body = getStemAndBody(oenode) # Unpack tuple into stem and body
        self.indicators = getIndicators(oenode)
        
        self.children_nodes: list[OENodePoint] = getChildren(oenode)
        self.sibling_nodes: list[OENodePoint] = [] # Contains all nodes at same level - .children_nodes of parent node gets passed here
        self.parent_nodes: list[Element] = [] # Instantiate parent attribute which will be modified in outer scope
        self.parent_headers: list[Element] = [] # For use in inner scope (i.e., naming images)
    
    def getFront(self, oeheader) -> str:
        """
        Returns full front HTML with focus on item at calling item
        """
        front_html = ""
        for oepoint in self.context: # Using OEChildren container that will be passed into the context attribute in outer scope
            oepoint = OENodePoint(oepoint) # Convert into class 
            if oepoint.text and oepoint.getGeneralStem(): # Screens for concepts/groupings using class attriburtes and methods
                # Will only expand if current OE node in loop is the same as the instance calling this method
                if self.id == oepoint.id:
                    # Render stems depending on point type
                    if oepoint.getConceptStem():
                        front_html = "".join((front_html,"<li %s><span style='font-weight:bold'>%s</span>:" % (oepoint.bullet_data, oepoint.getGeneralStem()))) # Start list item
                    if oepoint.getGroupingStem():
                        front_html = "".join((front_html,"<li %s><span style='text-decoration:underline'>%s</span>:" % (oepoint.bullet_data, oepoint.getGeneralStem())))
                    # Render sub-points if any
                    if oepoint.children:
                        substems = "\n<ul>\n"
                        for oesubpoint in oepoint.children:
                            oesubpoint = OENodePoint(oesubpoint) # Convert to class
                            if oesubpoint.getConceptStem(): # Rendering for concepts
                                substems = "".join((substems, "<li %s><span style='font-weight:bold'>%s</span>:</li>\n" % (oesubpoint.bullet_data, "___")))
                            elif "C" in oesubpoint.getIndicators(): # Rendering for concept-like attributes
                                substems = "".join((substems, "<li %s><span style='text-decoration:underline'>%s</span>:</li>\n" % (oesubpoint.bullet_data, f"{oesubpoint.getIndicators()} |___")))
                            elif "L" in oesubpoint.getIndicators(): # Rendering for listed attributes
                                substems = "".join((substems, "<li %s><span style='text-decoration:underline'>%s</span>:</li>\n" % (oesubpoint.bullet_data, oesubpoint.getGeneralStem())))
                            elif oesubpoint.text and not oesubpoint.getGroupingStem(): # Filters for non-empty (text) raw points, excludes groupings and attributes
                                substems = "".join((substems, "<li %s><span style='font-style: italic'>%s</span></li>\n" % (oesubpoint.bullet_data, "Subpoint")))
                        substems = "".join((substems, "</ul>\n"))
                        front_html = "".join((front_html, substems)) # Append substems to main HTML
                    front_html = "".join((front_html,"</li>\n")) # Close list item
                # Render other concept/grouping OE nodes that are not the calling object and 
                elif oepoint.getGeneralStem():
                    if oepoint.getConceptStem():
                        front_html = "".join((front_html,"<li %s><span style='font-weight:bold;color:#e8e8e8'>%s</span></li>\n" % (oepoint.bullet_data, oepoint.getGeneralStem()))) # Will only render stems, ignores points without stems
                    if oepoint.getGroupingStem():
                        front_html = "".join((front_html,"<li %s><span style='text-decoration:underline;color:#e8e8e8'>%s</span></li>\n" % (oepoint.bullet_data, oepoint.getGeneralStem()))) # Will only render stems, ignores points without stems
        # Wrap UL tags around main body, add parents and header - this part should not be a part of the body loop
        front_html = "".join(("<ul>\n",front_html,"</ul>"))
        
        for parent in oeheader.context_tracker: # Wraps info of parent nodes around returned HTML list 
            if self.getGroupingStem() and oeheader.context_tracker.index(parent) == 0: # Only display parent in non-grey if it is a grouping, index is to make sure that it is the immediate parent, of the current node, otherwise will treat as a distant parent 
                if parent.getConceptStem():
                    front_html = "".join(("<ul>\n<li %s><span style='font-weight:bold'>%s</span>\n" % (parent.bullet_data, parent.getConceptStem()), front_html, "\n</li>\n</ul>"))
                else: # Assume parent is a grouping instead
                    front_html = "".join(("<ul>\n<li %s><span style='text-decoration:underline'>%s</span>\n" % (parent.bullet_data, parent.getGroupingStem()), front_html, "\n</li>\n</ul>"))
            else: # For when current node is a concept and for distant parents
                if parent.getConceptStem():
                    front_html = "".join(("<ul>\n<li %s><span style='font-weight:bold;color:#e8e8e8'>%s</span>\n" % (parent.bullet_data, parent.getConceptStem()), front_html, "\n</li>\n</ul>"))
                else: # Assume parent is a grouping instead
                    front_html = "".join(("<ul>\n<li %s><span style='text-decoration:underline;color:#e8e8e8'>%s</span>\n" % (parent.bullet_data, parent.getGroupingStem()), front_html, "\n</li>\n</ul>"))
        front_html = "".join(("<span style='color:#e8e8e8'>%s</span>\n\n" % oeheader.text, front_html))
        front_html = "".join(("<span style='color:#e8e8e8'>%s - </span>" % getTitle(XML_PATH), front_html))
        print(front_html)
        return front_html

    def getBack(self, oeheader, oenode) -> str:
        """
        Returns greyed HTML list of complete items contained within the given container
        with item with the given index ungreyed i.e., focuses on item of index
        """
        def getChildText(oechildren):
            """
            Used to render children nodes
            """
            nonlocal subsubpoints # Uses subsubpoints str container from the function that calls it
            subsubpoints = "".join((subsubpoints,"<ul>\n")) # Open container
            for oepoint in oechildren:
                oepoint = OENodePoint(oepoint)
                if oepoint.text: # Render points but won't gray out since this function currently only runs for raw points
                    # subsubpoints = "".join((subsubpoints,"<li %s><span style='color:#e8e8e8'>%s</span>" % (oepoint.bullet_data, oepoint.text)))
                    subsubpoints = "".join((subsubpoints,"<li %s>%s" % (oepoint.bullet_data, oepoint.text)))
                    if oepoint.children:
                        subsubpoints = getChildText(oepoint.children)
                    subsubpoints = "".join((subsubpoints,"</li>\n" ))
                if oepoint.image: # Really shouldn't be reaching this point since raw points should not conatain diagrams
                    subsubpoints = "".join((subsubpoints,"<li %s><span style='color:#e8e8e8'>%s</span></li>\n" % (oepoint.bullet_data, "+Diagram")))
            subsubpoints = "".join((subsubpoints,"</ul>\n")) # Close container
            return subsubpoints
        
        back_html = ""
        context_img = "" # Context pictures should always apply to all nodes at the same level, thus can be displayed at the end
        img_count = 0 # Counter to index multiple images at same level so that there are no duplicates of images
        for oepoint in self.context: # Using OEChildren container that will be passed into the context attribute in outer scope
            oepoint = OENodePoint(oepoint) # Convert into class 
            if oepoint.text: # Will consider any non-empty points, not just concepts/groupings
                # Will only expand if current OE node in loop is the same as the instance calling this method
                if self.id == oepoint.id: 
                    img_stem = re.sub(r'[^\w\s]', '', oepoint.getGeneralStem())
                    back_html = "".join((back_html,"<li %s>%s" % (oepoint.bullet_data, oepoint.text))) # Render point and start list item
                    # Render sub-points if any
                    if oepoint.children:
                        subpoints = "\n<ul>\n" # Open sub-list
                        subnode_img_count = 0
                        for oesubpoint in oepoint.children:
                            oesubpoint = OENodePoint(oesubpoint) # Convert to class
                            if oesubpoint.text: # Process subpoints containing text 
                                subpoints = "".join((subpoints, "<li %s>\n" % oesubpoint.bullet_data)) # Start sub-list item
                                # Process subpoints differently depending on type of subpoint
                                if oesubpoint.getConceptStem(): # Show stem and grey body of concepts
                                    concept_stem = oesubpoint.getConceptStem()
                                    concept_body = oesubpoint.text.replace(concept_stem, "", 1) # Remove stem to only get body
                                    subpoints = "".join((subpoints, "<span style='font-weight:bold'>%s</span>" % concept_stem)) 
                                    subpoints = "".join((subpoints, "<span style='color:#e8e8e8'>%s</span>" % concept_body))
                                    if oesubpoint.children: # Add children indicator 
                                        subpoints = "".join((subpoints, "<span style='color:#e8e8e8'>%s</span>" % "(+)"))
                                elif oesubpoint.getGroupingStem(): # Process groupings
                                    if "C" in oesubpoint.getIndicators(): # Rendering for concept-like attributes
                                        subpoints = "".join((subpoints, oesubpoint.text))
                                    elif "L" in oesubpoint.getIndicators(): # Rendering for listed attributes
                                        subpoints = "".join((subpoints, oesubpoint.text))
                                    else: # Assume that the current subpoint is a grouping
                                        subpoints = "".join((subpoints, "<span style='color:#e8e8e8'>%s</span>" % oesubpoint.text)) 
                                    if oesubpoint.children: # Add children indicator
                                        subpoints = "".join((subpoints, "<span style='color:#e8e8e8'>%s</span>" % "(+)"))
                                else: # Assume it is a regular point and will display it regularly 
                                    subpoints = "".join((subpoints, oesubpoint.text)) 
                                    if oesubpoint.children: # Only render children subpoints for raw points since they won't get another card dedicated to them
                                        subsubpoints = "" # Declare and initiate subsubpoint container
                                        subsubpoints = getChildText(oesubpoint.children) # Use getChildrenText recursive function to add to all children nodes that aren't highlighted
                                        subpoints = "".join((subpoints, subsubpoints))
                                subpoints = "".join((subpoints, "</li>\n")) # End sub-list item
                            if oesubpoint.image: # Process subpoints containing image
                                img_name = "%s.png" % (img_stem + str(subnode_img_count)) # FIXME Might need to link more contexts in the future so that same concepts don't have overlapping picture names
                                img_path = os.path.join(MPATH, img_name)
                                img_str = oesubpoint.image
                                img_bytes = img_str.encode("utf-8")
                                with open(img_path, "wb") as img_file: # Write image to media directory
                                    img_file.write(base64.decodebytes(img_bytes)) # Convert bytes format to base64 format which is read by write() functio
                                subpoints = "".join((subpoints, "<li %s><img src='%s'style='max-width:600px'></li>" % (oesubpoint.bullet_data, img_name)))
                                subnode_img_count += 1
                        subpoints = "".join((subpoints, "</ul>\n")) # Close sub-list 
                        back_html = "".join((back_html, subpoints)) # Append subpoints to main HTML
                    back_html = "".join((back_html,"</li>\n")) # Close list item
                else: # For non-focused text-points of same rank 
                    back_html = "".join((back_html,"<li %s><span style='color:#e8e8e8'>" % oepoint.bullet_data))
                    if oepoint.children: # Add indicator of children before adding content
                        back_html = "".join((back_html,"(+)"))
                    back_html = "".join((back_html,"%s</span></li>\n" % oepoint.text)) #
            if oepoint.image: # For images of same rank
                # Set up naming system for images - will replace with hash at a diffferent location
                img_pattern = re.compile('[\W_]+') # To remove punctuation from filename
                img_stem = img_pattern.sub('', oenode.text)[0:75] # oenode refers to the calling outer node passed into this method, also have to truncate to account for filename size
                img_name = "%s.png" % (img_stem + str(img_count)) # FIXME might need to add more context relative to the title  
                img_path = os.path.join(MPATH, img_name)
                img_str = oepoint.image
                img_bytes = img_str.encode("utf-8")
                with open(img_path, "wb") as img_file: # Write image to media directory
                    img_file.write(base64.decodebytes(img_bytes)) # Convert bytes format to base64 format which is read by write() functio
                context_img = "".join((context_img,"<li %s><img src='%s'style='max-width:600px'></li>\n" % (oepoint.bullet_data, img_name))) # Store reference in context_img variable and add at very end
                # back_html = "".join((back_html,"<li %s><img src='%s'style='max-width:600px'></li>\n" % (oepoint.bullet_data, img_name))) # Legacy line that can be used instead if you want images to be in order
                img_count += 1
        back_html = "".join((back_html, context_img)) # Add images to end
        # Wrap UL tags around main body, add parents and header - this part should not be a part of the body loop
        back_html = "".join(("<ul>\n",back_html,"</ul>"))
        
        
        for parent in oeheader.context_tracker: # Wraps info of parent nodes around returned HTML list 
            if self.getGroupingStem() and oeheader.context_tracker.index(parent) == 0: # Only display parent in non-grey if it is a grouping, index is to make sure that it is the immediate parent, of the current node, otherwise will treat as a distant parent
                back_html = "".join(("<ul>\n<li %s>%s\n" % (parent.bullet_data, parent.text), back_html, "\n</li>\n</ul>"))
            else:
                back_html = "".join(("<ul>\n<li %s><span style='color:#e8e8e8'>%s</span>\n" % (parent.bullet_data, parent.text), back_html, "\n</li>\n</ul>"))
        back_html = "".join(("<span style='color:#e8e8e8'>%s</span>\n\n" % oeheader.text, back_html))
        back_html = "".join(("<span style='color:#e8e8e8'>%s - </span>" % getTitle(XML_PATH), back_html))
        print(back_html)
        return back_html
    

class OENodeHeader:
    """
    Separate class for OE nodes for headers 
    """
    def __init__(self, header_node: Element):
        # Should only be instantiated on non-empty headers with children
        self.id = header_node.get("objectID") # ID is an attribute of the XML node
        self.xml = header_node
        self.text = getNodeText(header_node)
        self.level = header_node.get("quickStyleIndex")
        self.children_nodes = getChildren(header_node)
        self.parent_headers: list[OENodeHeader] = []
        self.page_title = "" # Populated by outer scope in getHeaders()

#%% Global functions

def insertSubstring(text: str, substr: str, ins: str, end = True, before = True) -> str:
    """Inserts string into another string in front of a specified substring if it is found
    Otherwise returns original string. If text to search is empty, it will return the substring instead

    Args:
        text (str): String to insert into
        substr (str): Substring to search
        ins (str): String to insert
        end (bool, optional): Search from end. Defaults to True. Otherwise search from beginning
        before: Inserts string at beginning of substring. Otherwise inserts at end

    Returns:
        str: New modified string or original string if search substring not found
    """
    if end:
        ind = text.rfind(substr) # Finds highest index of substring
    else:
        ind = text.find(substr) # Finds lowest index of substring
    if ind >= 0: # If match is found
        if not before: 
            ind += len(ins) # Increase index by length of insert string so that text is inserted at end of substring
        return text[:ind] + ins + text[ind:] 
    elif text: # If text is non-empty, return text
        return text
    else: # Otherwise, text is an empty string, should return substring instead
        return substr

def getBulletData(node: Element) -> str:
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

def getChildren(node: Element) -> list[OENodePoint]:
    """Gets children of the given node if it exist, otherwise returns False

    Args:
        node (Element): XML node element

    Returns:
        Iterable[Element]: Returns the XML element (OEChildren) which contains the children nodes
    """
    # Only assign children if they exist
    if node.find("one:OEChildren", NAMESPACES) != None:
        return [OENodePoint(cnode) for cnode in node.find("one:OEChildren", NAMESPACES)]
    else: 
        return [] # Empty list which will evaluate as False when passed as a logical argument

def getNodeText(node: Element) -> str:
    node_content = node.find("one:T", NAMESPACES)
    if node_content != None and node_content.text != None:
        # The .text attribute of one:T elements contains the raw text (Without CDATA wrapper)
        return node_content.text 
    else:
        return "" # Returns empty string which will evaluate as False when passed as a logical argument

def getNodeTypeAndData(node: Element) -> tuple[str, str]: 
    """Gets node type and corresponding data from an XML node element

    Args:
        node (Element): XML node element from OneNote export

    Returns:
        tuple[str, str]: 1st str contains the node type, 2nd contains the corresponding data in string format. Otherwise returns tuple of None
    """
    
    if node.find("one:T", NAMESPACES) != None and node.find("one:T", NAMESPACES).text != None : # Must have text
        text = node.find("one:T", NAMESPACES).text # Remember that text is stored under text property, the object itself is an instance of Element (XML)
        soup = BeautifulSoup(text, features="html.parser")
        if soup.text.strip() != "": # Only assign text type if rendering text is not just whitespace
            # Note that select() methods can search via styling while find() methods seem to capture the whole element that matches search
            if soup.select_one('span[style*="font-weight:bold"]') != None:
                return ("concept", text)
            elif soup.select_one('span[style*="text-decoration:underline"]') != None:
                return ("grouping", text)
            elif "http://www.w3.org/1998/Math/MathML" in text: # Might not give correct rendering
                return ("equation", text)
            else: 
                return ("standard", text)
        
        
    elif node.find("one:Image/one:Data", NAMESPACES) != None and node.find("one:Image/one:Data", NAMESPACES).text != None: # Image nodes
        image_data = node.find("one:Image/one:Data", NAMESPACES).text
        return ("image", image_data)
        
    elif node.find("one:Table", NAMESPACES) != None and node.find("one:Table/one:Row", NAMESPACES) != None: # Table nodes
        # FIXME - Way to to screen for table
        return ("table", "placeholder data")
    
    return ("", "") # Returns two empty strings which evaluate as false when passed as logical arguments

def getStemAndBody(node: Element) -> tuple[str, str]:
    node_type, node_data = getNodeTypeAndData(node)
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

def getIndicators(node: Element) -> list[str]:
    if getStemAndBody(node)[0] and re.match(R"(\w+) ?\|", getStemAndBody(node)[0]) != None: # Generalized for any stems in case of additional expansions
        indicator_str = re.match(R"(\w+) ?\|", getStemAndBody(node)[0]).group(1)
        return list(indicator_str) # Convert indicators into set of characters
    else:
        return list() # Return an empty set for indicators otherwise



def getTitle(xml_file: Union[str, bytes, os.PathLike]) -> str:
    """
    Returns string of title of page being parsed 
    """
    xml_content = ElementTree.parse(xml_file)
    if xml_content.find("one:Title/one:OE/one:T", NAMESPACES) != None:
        xml_title = xml_content.find("one:Title/one:OE/one:T", NAMESPACES).text
    else: 
        xml_title = "Untitled"
    return xml_title

def getHeaders(xml_file: Union[str, bytes, os.PathLike]) -> list[OENodeHeader]:
    """
    Returns list of XML items of non-empty headers from XML and populates their parent trackers
    xml_file: path to XML file from OneNote output
    """
    xml_content = ElementTree.parse(xml_file)
    xml_title = getTitle(xml_file)
    list_outlines = xml_content.findall("one:Outline/one:OEChildren", NAMESPACES) # Returns OEChildren Element containing an OE for each header 
    # Note that each outline (page box) only has a SINGLE one:Children
    styled_headers: list[OENodeHeader] = [] # Is not always a superset of iterable headers (e.g., in the case of unstyled headers which are still iterable if they contain child nodes)
    iterable_headers: list[OENodeHeader] = []
    for header_node in (header for list_headers in list_outlines for header in list_headers): # First variable is assignment statement, then starts outer loops going to inner loops: https://www.geeksforgeeks.org/nested-list-comprehensions-in-python/
        if getNodeText(header_node): # Only parse non-empty nodes
            header_node = OENodeHeader(header_node)
            header_node.page_title = xml_title # Populate title property of instantiated OENodeHeader
            if header_node.xml.get("quickStyleIndex") not in [2, None]: # Quick styles #2 is normal text, 1st order is #1, 2nd order is #3 (skips over #2) and so on 
                styled_headers.append(header_node) 
            if header_node.children_nodes: # Is iterable if there are children
                iterable_headers.append(header_node) # Convert to OENodeHeader before appending
                print("Found non-empty header: " + header_node.text)
    styled_header_ids = [s_header.id for s_header in styled_headers] 
    
    for header in iterable_headers: # Modify items in iterable_headers
        if header.id in styled_header_ids: # Search for iterable header in styled header list using IDs (since objects are not equal even if they have the same values)
            index = styled_header_ids.index(header.id)
        else:
            index = 0 # Start at top of list (no parent headers)
        for i in range(index, 0, -1): # -1 step (decrement)
            if int(styled_headers[i-1].level) < int(header.level): # If the header above the current header in styled_headers is of a higher level (i.e., lower style #), add the above header as a parent
                header.parent_headers.append(styled_headers[i-1])
        # print([pheader.text for pheader in header.parent_headers])
    return iterable_headers # Return processed iterable_headers


