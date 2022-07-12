#%% Imports
# Built-in
import sys, os, base64, re, string
from typing import Union, Tuple, List, Set
from collections.abc import Iterable
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

# General
from bs4 import BeautifulSoup

# Anki
from anki.storage import Collection


#%% Constants
DEV = True # Change to False before running via program

ROOT_PATH = os.path.abspath(__file__)
os.chdir(os.path.dirname(ROOT_PATH))
PROFILE_HOME = os.path.expanduser(R"~\AppData\Roaming\Anki2\User 1")
CPATH = os.path.join(PROFILE_HOME, "collection.anki2")
MPATH = os.path.join(PROFILE_HOME, "collection.media")
NAMESPACES = {"one": R"http://schemas.microsoft.com/office/onenote/2013/onenote"} # Namespace to prefix tags, may change if API changes

if DEV:
    XML_PATH = R"export.xml"
else:
    # Command line arguments come in list, 0 = name of script, 1 = 1rst argument passed, 2 = 2nd argument passed
    ARG_FILENAME = sys.argv[1] # Contains filename of exported XML file
    XML_PATH = os.path.join(ROOT_PATH, ARG_FILENAME)


#%% Global functions

def getBulletData(node: Element) -> str:    
    if node.find("one:List/one:Number", NAMESPACES) != None:
        if "restartNumberingAt" in node.find("one:List/one:Number", NAMESPACES).attrib: # Search for restart numbering attribute in tag: https://stackoverflow.com/questions/10115396/how-to-test-if-an-attribute-exists-in-some-xml
            number = node.find("one:List/one:Number", NAMESPACES).attrib["restartNumberingAt"]
            return F"style='list-style-type: decimal'; value={number}"
        else: # Assume that ordered item does not need to be reordered
            return "style='list-style-type: decimal'"
    else: # Otherwise assumed to be an unordered item
        return ""
    # Styling can be modified in-line with HTML styling attribute which supports CSS styling directly inside: https://www.w3schools.com/tags/att_style.asp

def getChildren(node: Element) -> Iterable[Element]:
    """Gets children of the given node if it exist, otherwise returns False

    Args:
        node (Element): XML node element

    Returns:
        Iterable[Element]: Returns the XML element (OEChildren) which contains the children nodes
    """
    # Only assign children if they exist
    if node.find("one:OEChildren", NAMESPACES) != None:
        return node.find("one:OEChildren", NAMESPACES)
    else: 
        return [] # Empty list which will evaluate as False when passed as a logical argument

def getNodeText(node: Element) -> str:
    node_content = node.find("one:T", NAMESPACES)
    if node_content != None and node_content.text != None:
        return node_content.text 
    else:
        return "" # Returns empty string which will evaluate as False when passed as a logical argument

def getNodeTypeAndData(node: Element) -> Tuple[str, str]: 
    """Gets node type and corresponding data from an XML node element

    Args:
        node (Element): XML node element from OneNote export

    Returns:
        Tuple[str, str]: 1st str contains the node type, 2nd contains the corresponding data in string format. Otherwise returns tuple of None
    """
    
    if node.find("one:T", NAMESPACES) != None and node.find("one:T", NAMESPACES).text != None: # Text-based types
        text = node.find("one:T", NAMESPACES).text # Remember that text is stored under text property, the object itself is an instance of Element (XML)
        soup = BeautifulSoup(text, features="html.parser")
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

def getStemAndBody(node: Element) -> Tuple[str, str]:
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

def getIndicators(node: Element) -> List[str]:
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

def getHeaders(xml_file: Union[str, bytes, os.PathLike]) -> List[Element]:
    """
    Returns list of XML items of non-empty headers from XML
    xml_file: path to XML file from OneNote output
    """
    xml_content = ElementTree.parse(xml_file)
    list_OE_headers = xml_content.findall("one:Outline/one:OEChildren", NAMESPACES) # Is actually the XML element of OEChildren containing OE headers, returns list even if there's a single item
    header_list = []
    for headers in list_OE_headers:
        for header_node in headers:
            if getNodeText(header_node) and getChildren(header_node): # Only non-empty header with children will get parsed
                print("Found non-empty header: " + getNodeText(header_node))
                header_list.append(header_node)
    return header_list

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
        
        self.children_nodes: Iterable[Element] = getChildren(oenode)
        self.sibling_nodes: Iterable[Element] = [] # Contains all nodes at same level - is OEChildren XML node from previous items, modified in outer scope
        self.parent_nodes: List[Element] = [] # Instantiate parent attribute which will be modified in outer scope

    
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
    def __init__(self, header_node):
        # Should only be instantiated on non-empty headers with children
        self.id = header_node.get("objectID") # ID is an attribute of the XML node
        self.text = getNodeText(header_node) 
        self.children_nodes = getChildren(header_node)
        self.context_tracker = [] # Acts as the top-level tracker for all subpoints under the header



#%% Execution

# Need to distinguish between header OE and point OE as they should be processed differently        
def iterHeaders(header_list):
    def iterOE(cur_node, parent = False):
        """
        Iterates over children OE nodes given an OE node that contains children.
        Can be used recursively -> entry point is an OENode class instance with children
    
        Parameters
        ----------
        oenode : OE node of OENode classes (header or point) that contains chilren 
    
        Returns
        -------
        None.
    
        """
        nonlocal header # Refer to out scope's oeheader objects
        # Will only run during recursive loops, not during initial loop which is for header
        if parent:
            header.context_tracker.insert(0, cur_node) # Insert most recent oenode at front of list 
        # Main logic using functions defined in OENodePoint class
        for child_node in cur_node.children:
            child_node = OENodePoint(child_node) # Convert item to class instance
            if child_node.text and child_node.getGeneralStem(): # Will only consider concepts/groupings for card generation
                child_node.context = cur_node.children # Set context by adding all children at same level
                # Fill front and back
                OE1_front = child_node.getFront(header)
                OE1_back = child_node.getBack(header, cur_node)
                # Generate card below
                

                # Recursive flow for nodes below level of headers with children, will set parent attribute for these nodes
                if child_node.children:
                    iterOE(child_node, parent = True)
        if parent:
            header.context_tracker.pop(0) # Pop off most recent parent after leaving local scope
        return None
    

    try:
        # Initialize model
        col = Collection(CPATH, log=True) # NOTE that this changes the directory
        card_model = col.models.by_name("Basic") # Search for card model
        deck = col.decks.by_name("ZExport") # Set current deck
    
        for header in header_list:
            # FIXME Can parse header levels at this scope and add to oeheader attribute which can be accessed later
            header = OENodeHeader(header) # Convert item to class instance
            iterOE(header)
            
        col.save() # Save changes to DB
    finally: # Should have this always run, otherwise, anki will get stuck        
        col.close() # Need this function, otherwise instance stays open
        return None