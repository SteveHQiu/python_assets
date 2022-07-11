#%% Imports
# Built-in
import sys, os, base64, re, string
from typing import Union, Tuple, List
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

# General
from bs4 import BeautifulSoup

# Anki
from anki.storage import Collection

# Internal modules
from standard import StandardRenderer


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

def checkOrdered(node: Element) -> bool:    
    if node.find("one:List/one:Number", NAMESPACES) != None:
        return True
    else: # Otherwise assumed to be an unordered item
        return False

def getChildren(node: Element) -> Union[Element, bool]:
    """Gets children of the given node if it exist, otherwise returns False

    Args:
        node (Element): XML node element

    Returns:
        Union[Element, False]: Returns the XML element (OEChildren) which contains the children nodes
    """
    # Only assign children if they exist
    if node.find("one:OEChildren", NAMESPACES) != None:
        return node.find("one:OEChildren", NAMESPACES)
    else: 
        return False

def getNodeText(node: Element) -> Union[str, bool]:
    node_content = node.find("one:T", NAMESPACES)
    if node_content != None and node_content.text != None:
        return node_content.text 
    else:
        False

def getNodeTypeAndData(node: Element) -> Union[Tuple[str, str], Tuple[None, None]]: 
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
    
    return (None, None)

def getStem(node: Element) -> Union[str, bool]:
    node_type, node_data = getNodeTypeAndData(node)
    if node_type == "concept":
        soup = BeautifulSoup(node_data, features="html.parser")
        return soup.select_one('span[style*="font-weight:bold"]').text # Returns first tag that matches selector which searches for tags with attributes containing "font-weight:bold"
    elif node_type == "grouping":
        soup = BeautifulSoup(node_data, features="html.parser")
        return soup.select_one('span[style*="text-decoration:underline"]').text # Returns first tag that matches selector
    else:
        return False

def getIndicators(node: Element) -> List[str]:
    if getStem(node) and re.match(r"(\w+) ?\|", getStem(node)) != None: # Generalized for any stems in case of additional expansions
        return re.match(r"(\w+) ?\|", getStem(node)).group(1)
    else:
        return [] # Return an empty list for indicators otherwise



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

def renderParents():
    
    pass



#%% Global Classes
class OENodePoint:
    """
    Parses an XML OE item from the OneNote export
    """
    def __init__(self, oenode):
        self.id = oenode.get("objectID") # ID is an attribute of the XML node
        self.ordered = checkOrdered(oenode)
        
        self.type, self.data = getNodeTypeAndData(oenode) # Unpack tuple into type and data
        self.stem = getStem(oenode)
        self.indicators = getIndicators(oenode)
        
        self.children_nodes = getChildren(oenode)
        self.sibling_nodes = [] # Contains all nodes at same level - is OEChildren container from previous items, modified in outer scope
        self.parent_nodes = [] # Instantiate parent attribute which will be modified in outer scope

    
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
                        front_html = "".join((front_html,"<li %s><span style='font-weight:bold'>%s</span>:" % (oepoint.ordered, oepoint.getGeneralStem()))) # Start list item
                    if oepoint.getGroupingStem():
                        front_html = "".join((front_html,"<li %s><span style='text-decoration:underline'>%s</span>:" % (oepoint.ordered, oepoint.getGeneralStem())))
                    # Render sub-points if any
                    if oepoint.children:
                        substems = "\n<ul>\n"
                        for oesubpoint in oepoint.children:
                            oesubpoint = OENodePoint(oesubpoint) # Convert to class
                            if oesubpoint.getConceptStem(): # Rendering for concepts
                                substems = "".join((substems, "<li %s><span style='font-weight:bold'>%s</span>:</li>\n" % (oesubpoint.ordered, "___")))
                            elif "C" in oesubpoint.getIndicators(): # Rendering for concept-like attributes
                                substems = "".join((substems, "<li %s><span style='text-decoration:underline'>%s</span>:</li>\n" % (oesubpoint.ordered, f"{oesubpoint.getIndicators()} |___")))
                            elif "L" in oesubpoint.getIndicators(): # Rendering for listed attributes
                                substems = "".join((substems, "<li %s><span style='text-decoration:underline'>%s</span>:</li>\n" % (oesubpoint.ordered, oesubpoint.getGeneralStem())))
                            elif oesubpoint.text and not oesubpoint.getGroupingStem(): # Filters for non-empty (text) raw points, excludes groupings and attributes
                                substems = "".join((substems, "<li %s><span style='font-style: italic'>%s</span></li>\n" % (oesubpoint.ordered, "Subpoint")))
                        substems = "".join((substems, "</ul>\n"))
                        front_html = "".join((front_html, substems)) # Append substems to main HTML
                    front_html = "".join((front_html,"</li>\n")) # Close list item
                # Render other concept/grouping OE nodes that are not the calling object and 
                elif oepoint.getGeneralStem():
                    if oepoint.getConceptStem():
                        front_html = "".join((front_html,"<li %s><span style='font-weight:bold;color:#e8e8e8'>%s</span></li>\n" % (oepoint.ordered, oepoint.getGeneralStem()))) # Will only render stems, ignores points without stems
                    if oepoint.getGroupingStem():
                        front_html = "".join((front_html,"<li %s><span style='text-decoration:underline;color:#e8e8e8'>%s</span></li>\n" % (oepoint.ordered, oepoint.getGeneralStem()))) # Will only render stems, ignores points without stems
        # Wrap UL tags around main body, add parents and header - this part should not be a part of the body loop
        front_html = "".join(("<ul>\n",front_html,"</ul>"))
        
        for parent in oeheader.context_tracker: # Wraps info of parent nodes around returned HTML list 
            if self.getGroupingStem() and oeheader.context_tracker.index(parent) == 0: # Only display parent in non-grey if it is a grouping, index is to make sure that it is the immediate parent, of the current node, otherwise will treat as a distant parent 
                if parent.getConceptStem():
                    front_html = "".join(("<ul>\n<li %s><span style='font-weight:bold'>%s</span>\n" % (parent.ordered, parent.getConceptStem()), front_html, "\n</li>\n</ul>"))
                else: # Assume parent is a grouping instead
                    front_html = "".join(("<ul>\n<li %s><span style='text-decoration:underline'>%s</span>\n" % (parent.ordered, parent.getGroupingStem()), front_html, "\n</li>\n</ul>"))
            else: # For when current node is a concept and for distant parents
                if parent.getConceptStem():
                    front_html = "".join(("<ul>\n<li %s><span style='font-weight:bold;color:#e8e8e8'>%s</span>\n" % (parent.ordered, parent.getConceptStem()), front_html, "\n</li>\n</ul>"))
                else: # Assume parent is a grouping instead
                    front_html = "".join(("<ul>\n<li %s><span style='text-decoration:underline;color:#e8e8e8'>%s</span>\n" % (parent.ordered, parent.getGroupingStem()), front_html, "\n</li>\n</ul>"))
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
                    # subsubpoints = "".join((subsubpoints,"<li %s><span style='color:#e8e8e8'>%s</span>" % (oepoint.ordered, oepoint.text)))
                    subsubpoints = "".join((subsubpoints,"<li %s>%s" % (oepoint.ordered, oepoint.text)))
                    if oepoint.children:
                        subsubpoints = getChildText(oepoint.children)
                    subsubpoints = "".join((subsubpoints,"</li>\n" ))
                if oepoint.image: # Really shouldn't be reaching this point since raw points should not conatain diagrams
                    subsubpoints = "".join((subsubpoints,"<li %s><span style='color:#e8e8e8'>%s</span></li>\n" % (oepoint.ordered, "+Diagram")))
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
                    back_html = "".join((back_html,"<li %s>%s" % (oepoint.ordered, oepoint.text))) # Render point and start list item
                    # Render sub-points if any
                    if oepoint.children:
                        subpoints = "\n<ul>\n" # Open sub-list
                        subnode_img_count = 0
                        for oesubpoint in oepoint.children:
                            oesubpoint = OENodePoint(oesubpoint) # Convert to class
                            if oesubpoint.text: # Process subpoints containing text 
                                subpoints = "".join((subpoints, "<li %s>\n" % oesubpoint.ordered)) # Start sub-list item
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
                                subpoints = "".join((subpoints, "<li %s><img src='%s'style='max-width:600px'></li>" % (oesubpoint.ordered, img_name)))
                                subnode_img_count += 1
                        subpoints = "".join((subpoints, "</ul>\n")) # Close sub-list 
                        back_html = "".join((back_html, subpoints)) # Append subpoints to main HTML
                    back_html = "".join((back_html,"</li>\n")) # Close list item
                else: # For non-focused text-points of same rank 
                    back_html = "".join((back_html,"<li %s><span style='color:#e8e8e8'>" % oepoint.ordered))
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
                context_img = "".join((context_img,"<li %s><img src='%s'style='max-width:600px'></li>\n" % (oepoint.ordered, img_name))) # Store reference in context_img variable and add at very end
                # back_html = "".join((back_html,"<li %s><img src='%s'style='max-width:600px'></li>\n" % (oepoint.ordered, img_name))) # Legacy line that can be used instead if you want images to be in order
                img_count += 1
        back_html = "".join((back_html, context_img)) # Add images to end
        # Wrap UL tags around main body, add parents and header - this part should not be a part of the body loop
        back_html = "".join(("<ul>\n",back_html,"</ul>"))
        for parent in oeheader.context_tracker: # Wraps info of parent nodes around returned HTML list 
            if self.getGroupingStem() and oeheader.context_tracker.index(parent) == 0: # Only display parent in non-grey if it is a grouping, index is to make sure that it is the immediate parent, of the current node, otherwise will treat as a distant parent
                back_html = "".join(("<ul>\n<li %s>%s\n" % (parent.ordered, parent.text), back_html, "\n</li>\n</ul>"))
            else:
                back_html = "".join(("<ul>\n<li %s><span style='color:#e8e8e8'>%s</span>\n" % (parent.ordered, parent.text), back_html, "\n</li>\n</ul>"))
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

class NodeIterator:
    def __init__(self, header_list: List[Element]):
        self.header_list = header_list # Input header list
        self.parent_node_tracker = [] # Container for parent XML nodes when going into nested lists below level of first order OENodePoints
        self.cards = [] # Container for generated cards, format of Tuple[front, back]

    
    def genCards(self):
        """
        Note that this will still copy media into anki media directory if there are images
        """
        def iterNodes(cur_node: Union[OENodeHeader, Element]):
            for child_xml_node in cur_node.children_nodes: # Starting point for nodes directly under header (or Element if in nested loop)
                child_node = OENodePoint(child_xml_node) # Convert item to class instance
                if child_node.type in ["concept", "grouping",]: # Only certain types of nodes will trigger card generation
                    child_node.parent_nodes = self.parent_node_tracker # Copy parent_node_tracker information into current node's parent_nodes, should only be relevant when this function is recursively called
                    child_node.sibling_nodes = cur_node.children_nodes # Set children of upper node as sibling nodes to the child nodes that we are about to process                    
                    
                    # Fill front and back 
                    renderer = StandardRenderer(child_node)
                    renderer.renderHtml()
                    self.cards.append((renderer.fronthtml, renderer.backhtml)) # Append rendered HTMLs

                    if child_node.children_nodes: # Recursively search for children 
                        # Only becomes relevant after OENodeHeader loop
                        self.parent_node_tracker.insert(0, child_xml_node) # Add a parent node before going into nested loop
                        iterNodes(child_node) 
                        self.parent_node_tracker.pop(0) # Pop off parent node after leaving nested loop
            return None

        for header in self.header_list:
            # FIXME Can parse header levels at this scope and add to oeheader attribute which can be accessed later
            header = OENodeHeader(header) # Convert item to class instance
            iterNodes(header)
        return self
        
    def displayCards(self):
        """
        Display generated card in HTML format, for debuggging purposes
        """
        html = ""
        card_num = 1
        for card in self.cards:
            html += F"<br>Card no. {card_num}:<br>" + card[0] + "<hr>" + card[1] + "<hr><hr><br>" # Add front and back with spacing between both and next set of cards
            card_num += 1
        with open("displayCards_output.html", "w") as file:
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

        
#%% 
if __name__ == "__main__":
    header_list = getHeaders(XML_PATH)
    crawler = NodeIterator(header_list)
    crawler.genCards()
    crawler.displayCards()

