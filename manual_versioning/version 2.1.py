# -*- coding: utf-8 -*-
import sys, os, base64, re, string;
from anki.storage import Collection;
from xml.etree import ElementTree;
from bs4 import BeautifulSoup;

"""
Changelog
-Added support for ordered lists

"""

#%% Constants
PROFILE_HOME = os.path.expanduser(r"~\AppData\Roaming\Anki2\User 1");
cpath = os.path.join(PROFILE_HOME, "collection.anki2");
mpath = os.path.join(PROFILE_HOME, "collection.media");
namespace = {"one": r"http://schemas.microsoft.com/office/onenote/2013/onenote"}; # Namespace to prefix tags
root_path = os.path.expanduser(r"~\OneDrive - ualberta.ca\Coding\OneNote2AnkiPython");
file_name = sys.argv[1]; # Command line arguments come in list, 0 = name of script, 1 = 1rst argument passed, 2 = 2nd argument passed
file_path = os.path.join(root_path, file_name);


# Note that elements with children nodes are iterable with the children notes being items of the container
# Findall returns list format, even if single item, hence need to specify item

#%% Functions

def getHeaders(xml_input) -> list:
    """
    Returns list of XML items of non-empty headers from XML
    \n xml_input: path to XML file from OneNote
    """
    xml_content = ElementTree.parse(xml_input);
    list_OE_headers = xml_content.findall("one:Outline/one:OEChildren", namespace); # Is actually the XML element of OEChildren containing OE headers
    header_list = [];
    for headers in list_OE_headers:
        for OE_header in headers:
            OE_content = OE_header.find("one:T", namespace);
            if OE_content != None and OE_content.text != None: # Need to screen out empty lines
                header_text = OE_header.find("one:T", namespace).text;
                print("Header:", header_text);
                if OE_header.find("one:OEChildren", namespace) != None: # Only for headers that have children
                    header_list.append(OE_header);
    return header_list;

#%% Classes
class OENodePoint:
    """
    Parses an XML OE item from the OneNote export
    """
    def __init__(self, oenode, card_forward = True, card_reverse = False):
        self.id = oenode.get("objectID"); # ID is an attribute of the XML node
        # Text is stored under a separate tag
        if oenode.find("one:T", namespace) != None and oenode.find("one:T", namespace).text != None:
            self.text = oenode.find("one:T", namespace).text;
        else: 
            self.text = False;
        # Image is stored under a separate tag
        if oenode.find("one:Image/one:Data", namespace) != None and oenode.find("one:Image/one:Data", namespace).text != None:
            self.image = oenode.find("one:Image/one:Data", namespace).text;
        else: 
            self.image = False;
        # Only assign children if they exist
        if oenode.find("one:OEChildren", namespace) != None:
            self.children = oenode.find("one:OEChildren", namespace)
        else: 
            self.children = False;
        # Is the field to replace the style in the bullet of lists
        if oenode.find("one:List/one:Number", namespace) != None:
            self.ordered = "style='list-style-type: decimal;'";
        else: # Otherwise assumed to be an unordered item
            self.ordered = "";
        # Instantiate parent attribute which will be modified in outer scope
        self.parents = [];
        # Instantiate context attribute to take OEChildren container from previous items, modified in outer scope
        self.context = False; 
            
    def getGroupingStem(self) -> str:
        """
        Returns the stem of the grouping or attribute within HTML string
        """
        soup = BeautifulSoup(self.text, features="html.parser");
        if soup.select_one('span[style*="text-decoration:underline"]') != None:
            return soup.select_one('span[style*="text-decoration:underline"]').text; # Returns first tag that matches selector
        else:
            return False;
    
    def getConceptStem(self) -> str:
        """
        Returns the stem of the concept within HTML string
        """
        soup = BeautifulSoup(self.text, features="html.parser");
        if soup.select_one('span[style*="font-weight:bold"]') != None:
            return soup.select_one('span[style*="font-weight:bold"]').text; # Returns first tag that matches selector which searches for tags with attributes containing "font-weight:bold"
        else:
            return False;
    
    def getGeneralStem(self) -> str:
        """
        Returns the appropriate stem when given a concept/attribute i.e., tests if there is a stem
        """
        if self.getConceptStem():
            return self.getConceptStem();
        elif self.getGroupingStem():
            return self.getGroupingStem();
        else:
            return False;
        
        
    def getIndicators(self) -> str:
        """
        

        Returns
        -------
        str
            DESCRIPTION.

        """
        if self.getGeneralStem() and re.match(r"(\w+) ?\|", self.getGeneralStem()) != None: # Generalized for any stems in case of additional expansions
            return re.match(r"(\w+) ?\|", self.getGeneralStem()).group(1);
        else:
            return ""; # Return an empty list for indicators otherwise
    
    def getFront(self, oeheader) -> str:
        """
        Returns full front HTML with focus on item at calling item
        """
        front_html = "";
        for oepoint in self.context: # Using OEChildren container that will be passed into the context attribute in outer scope
            oepoint = OENodePoint(oepoint); # Convert into class 
            if oepoint.text and oepoint.getGeneralStem(): # Screens for concepts/groupings using class attriburtes and methods
                # Will only expand if current OE node in loop is the same as the instance calling this method
                if self.id == oepoint.id:
                    # Render stems depending on point type
                    if oepoint.getConceptStem():
                        front_html = "".join((front_html,"<li %s><span style='font-weight:bold'>%s</span>:" % (oepoint.ordered, oepoint.getGeneralStem()))); # Start list item
                    if oepoint.getGroupingStem():
                        front_html = "".join((front_html,"<li %s><span style='text-decoration:underline'>%s</span>:" % (oepoint.ordered, oepoint.getGeneralStem())));
                    # Render sub-points if any
                    if oepoint.children:
                        substems = "\n<ul>\n"
                        for oesubpoint in oepoint.children:
                            oesubpoint = OENodePoint(oesubpoint); # Convert to class
                            if oesubpoint.text and oesubpoint.getConceptStem():
                                substems = "".join((substems, "<li %s><span style='font-weight:bold'>%s</span>:</li>\n" % (oesubpoint.ordered, "___")));
                            elif oesubpoint.text and not oesubpoint.getGroupingStem(): # Filters for raw points, excludes groupings and attributes
                                substems = "".join((substems, "<li %s>Subpoint</li>\n" % oesubpoint.ordered));
                        substems = "".join((substems, "</ul>\n"));
                        front_html = "".join((front_html, substems)); # Append substems to main HTML
                    front_html = "".join((front_html,"</li>\n")); # Close list item
                # Render other concept/grouping OE nodes that are not the calling object and 
                elif oepoint.getGeneralStem():
                    if oepoint.getConceptStem():
                        front_html = "".join((front_html,"<li %s><span style='font-weight:bold;color:#BEBEBE'>%s</span></li>\n" % (oepoint.ordered, oepoint.getGeneralStem()))); # Will only render stems, ignores points without stems
                    if oepoint.getGroupingStem():
                        front_html = "".join((front_html,"<li %s><span style='text-decoration:underline;color:#BEBEBE'>%s</span></li>\n" % (oepoint.ordered, oepoint.getGeneralStem()))); # Will only render stems, ignores points without stems
        # Wrap UL tags around main body, add parents and header - this part should not be a part of the body loop
        front_html = "".join(("<ul>\n",front_html,"</ul>"));
        for parent in oeheader.context_tracker: # Wraps info of parent nodes around returned HTML list 
            if self.getGroupingStem() and oeheader.context_tracker.index(parent) == 0: # Only display parent in non-grey if it is a grouping, index is to make sure that it is the immediate parent, of the current node, otherwise will treat as a distant parent 
                if parent.getConceptStem():
                    front_html = "".join(("<ul>\n<li %s><span style='font-weight:bold'>%s</span>\n" % (parent.ordered, parent.getConceptStem()), front_html, "\n</li>\n</ul>"));
                else: # Assume parent is a grouping instead
                    front_html = "".join(("<ul>\n<li %s><span style='text-decoration:underline'>%s</span>\n" % (parent.ordered, parent.getGroupingStem()), front_html, "\n</li>\n</ul>"));
            else: # For when current node is a concept and for distant parents
                if parent.getConceptStem():
                    front_html = "".join(("<ul>\n<li %s><span style='font-weight:bold;color:#BEBEBE'>%s</span>\n" % (parent.ordered, parent.getConceptStem()), front_html, "\n</li>\n</ul>"));
                else: # Assume parent is a grouping instead
                    front_html = "".join(("<ul>\n<li %s><span style='text-decoration:underline;color:#BEBEBE'>%s</span>\n" % (parent.ordered, parent.getGroupingStem()), front_html, "\n</li>\n</ul>"));
        front_html = "".join(("<span style='color:#BEBEBE'>%s</span>\n\n" % oeheader.text, front_html));
        print(front_html);
        return front_html;

    def getBack(self, oeheader, oenode) -> str:
        """
        Returns greyed HTML list of complete items contained within the given container
        with item with the given index ungreyed i.e., focuses on item of index
        """
        # def getChildText(oechildren):
        #     """
        #     Used to render children nodes, currently not used
        #     """
        #     nonlocal subsubpoints; # Uses subsubpoints str container from the function that calls it
        #     subsubpoints = "".join((subsubpoints,"<ul>\n")); # Open container
        #     for oepoint in oechildren:
        #         oepoint = OENodePoint(oepoint);
        #         if oepoint.text:
        #             subsubpoints = "".join((subsubpoints,"<li %s><span style='color:#BEBEBE'>%s</span>" % (oepoint.ordered, oepoint.text)));
        #             if oepoint.children:
        #                 subsubpoints = getChildText(oepoint.children);
        #             subsubpoints = "".join((subsubpoints,"</li>\n" ));
        #         if oepoint.image:
        #             subsubpoints = "".join((subsubpoints,"<li %s><span style='color:#BEBEBE'>+Image</li>\n" % oepoint.ordered));
        #     subsubpoints = "".join((subsubpoints,"</ul>\n")); # Close container
        #     return subsubpoints;
        
        back_html = "";
        context_img = ""; # Context pictures should always apply to all nodes at the same level, thus can be displayed at the end
        img_count = 0; # Counter to index multiple images at same level so that there are no duplicates of images
        for oepoint in self.context: # Using OEChildren container that will be passed into the context attribute in outer scope
            oepoint = OENodePoint(oepoint); # Convert into class 
            if oepoint.text: # Will consider any non-empty points, not just concepts/groupings
                # Will only expand if current OE node in loop is the same as the instance calling this method
                if self.id == oepoint.id: 
                    img_stem = re.sub(r'[^\w\s]', '', oepoint.getGeneralStem());
                    back_html = "".join((back_html,"<li %s>%s" % (oepoint.ordered, oepoint.text))); # Render point and start list item
                    # Render sub-points if any
                    if oepoint.children:
                        subpoints = "\n<ul>\n"; # Open sub-list
                        subnode_img_count = 0;
                        for oesubpoint in oepoint.children:
                            oesubpoint = OENodePoint(oesubpoint); # Convert to class
                            if oesubpoint.text: # Process subpoints containing text 
                                subpoints = "".join((subpoints, "<li %s>\n" % oesubpoint.ordered)); # Start sub-list item
                                # Process subpoints differently depending on type of subpoint
                                if oesubpoint.getConceptStem(): # Show stem and grey body of concepts
                                    concept_stem = oesubpoint.getConceptStem();
                                    concept_body = oesubpoint.text.replace(concept_stem, "", 1); # Remove stem to only get body
                                    subpoints = "".join((subpoints, "<span style='font-weight:bold'>%s</span>" % concept_stem)); 
                                    subpoints = "".join((subpoints, "<span style='color:#BEBEBE'>%s</span>" % concept_body));
                                elif oesubpoint.getGroupingStem(): # Grey out groupings
                                    subpoints = "".join((subpoints, "<span style='color:#BEBEBE'>%s</span>" % oesubpoint.text)); 
                                else: # Assume it is a regular point and will display it regularly 
                                    subpoints = "".join((subpoints, oesubpoint.text)); 
                                if oesubpoint.children:
                                    # subsubpoints = ""; # Declare and initiate subsubpoint container
                                    # subsubpoints = getChildText(oesubpoint.children)); # Use getChildrenText recursive function to add to all children nodes that aren't highlighted
                                    # subpoints = "".join((subpoints, subsubpoints));
                                    subpoints = "".join((subpoints, "->"));
                                subpoints = "".join((subpoints, "</li>\n")); # End sub-list item
                            if oesubpoint.image: # Process subpoints containing image
                                img_name = "%s.png" % (img_stem + str(subnode_img_count)); # FIXME Might need to link more contexts in the future so that same concepts don't have overlapping picture names
                                img_path = os.path.join(mpath, img_name);
                                img_str = oesubpoint.image;
                                img_bytes = img_str.encode("utf-8");
                                with open(img_path, "wb") as img_file: # Write image to media directory
                                    img_file.write(base64.decodebytes(img_bytes)); # Convert bytes format to base64 format which is read by write() functio
                                subpoints = "".join((subpoints, "<li %s><img src='%s'style='max-width:600px'></li>" % (oesubpoint.ordered, img_name)));
                                subnode_img_count += 1;
                        subpoints = "".join((subpoints, "</ul>\n")); # Close sub-list 
                        back_html = "".join((back_html, subpoints)); # Append subpoints to main HTML
                    back_html = "".join((back_html,"</li>\n")); # Close list item
                else: # For non-focused text-points of same rank 
                    back_html = "".join((back_html,"<li %s><span style='color:#BEBEBE'>" % oepoint.ordered));
                    if oepoint.children: # Add indicator of children before adding content
                        back_html = "".join((back_html,"(+)"))
                    back_html = "".join((back_html,"%s</span></li>\n" % oepoint.text)); #
            if oepoint.image: # For images of same rank
                # Set up naming system for images - will replace with hash at a diffferent location
                img_pattern = re.compile('[\W_]+'); # To remove punctuation from filename
                img_stem = img_pattern.sub('', oenode.text)[0:75]; # oenode refers to the calling outer node passed into this method, also have to truncate to account for filename size
                img_name = "%s.png" % (img_stem + str(img_count)); # FIXME might need to add more context relative to the title  
                img_path = os.path.join(mpath, img_name);
                img_str = oepoint.image;
                img_bytes = img_str.encode("utf-8");
                with open(img_path, "wb") as img_file: # Write image to media directory
                    img_file.write(base64.decodebytes(img_bytes)); # Convert bytes format to base64 format which is read by write() functio
                context_img = "".join((context_img,"<li %s><img src='%s'style='max-width:600px'></li>\n" % (oepoint.ordered, img_name))); # Store reference in context_img variable and add at very end
                # back_html = "".join((back_html,"<li %s><img src='%s'style='max-width:600px'></li>\n" % (oepoint.ordered, img_name))) # Legacy line that can be used instead if you want images to be in order
                img_count += 1;
        back_html = "".join((back_html, context_img)); # Add images to end
        # Wrap UL tags around main body, add parents and header - this part should not be a part of the body loop
        back_html = "".join(("<ul>\n",back_html,"</ul>"));
        for parent in oeheader.context_tracker: # Wraps info of parent nodes around returned HTML list 
            if self.getGroupingStem() and oeheader.context_tracker.index(parent) == 0: # Only display parent in non-grey if it is a grouping, index is to make sure that it is the immediate parent, of the current node, otherwise will treat as a distant parent
                back_html = "".join(("<ul>\n<li %s>%s\n" % (parent.ordered, parent.text), back_html, "\n</li>\n</ul>"));
            else:
                back_html = "".join(("<ul>\n<li %s><span style='color:#BEBEBE'>%s</span>\n" % (parent.ordered, parent.text), back_html, "\n</li>\n</ul>"));
        back_html = "".join(("<span style='color:#BEBEBE'>%s</span>\n\n" % oeheader.text, back_html));
        print(back_html);
        return back_html;
    

        
class OENodeHeader:
    """
    Separate class for OE nodes for headers 
    """
    def __init__(self, oenode):
        self.id = oenode.get("objectID"); # ID is an attribute of the XML node
        # Text is stored under a separate tag
        if oenode.find("one:T", namespace) != None and oenode.find("one:T", namespace).text != None:
            self.text = oenode.find("one:T", namespace).text;
        else: 
            self.text = False;
        # Only assign children if they exist
        if oenode.find("one:OEChildren", namespace) != None:
            self.children = oenode.find("one:OEChildren", namespace)
        else: 
            self.children = False;
        self.context_tracker = []; # Acts as the top-level tracker for all subpoints under the header

#%% Execution

# Need to distinguish between header OE and point OE as they should be processed differently        
def iterHeaders(header_list):
    def iterOE(oenode, parent = False):
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
        nonlocal oeheader; # Refer to out scope's oeheader objects
        # Will only run during recursive loops, not during initial loop which is for header
        if parent:
            oeheader.context_tracker.insert(0, oenode); # Insert most recent oenode at front of list 
        # Main logic using functions defined in OENodePoint class
        for oepoint in oenode.children:
            oepoint = OENodePoint(oepoint); # Convert item to class instance
            if oepoint.text and oepoint.getGeneralStem(): # Will only consider concepts/groupings for card generation
                oepoint.context = oenode.children; # Set context
                # Fill front and back
                OE1_front = oepoint.getFront(oeheader);
                OE1_back = oepoint.getBack(oeheader, oenode);
                # Generate card
                ## Instantiate new note
                note = col.new_note(card_model); # New new_note() method requires a card model to be passed as a parameter
                note.note_type()['did'] = deck['id']; # Need to set deck ID since it doesn't come with the model
                ## Populate note, using strings to identify fields rather than strict indices in case field order changes
                note.fields[note._field_index("Front")] = OE1_front;
                note.fields[note._field_index("Back")] = OE1_back;
                ## Set the tags (and add the new ones to the deck configuration
                tags = "test1 test2";
                note.tags = col.tags.canonify(col.tags.split(tags));
                m = note.note_type();
                m['tags'] = note.tags;
                col.models.save(m);
                ## Add note to DB
                col.addNote(note);
                # Recursive flow for nodes below level of headers with children, will set parent attribute for these nodes
                if oepoint.children:
                    iterOE(oepoint, parent = True);
        if parent:
            oeheader.context_tracker.pop(0); # Pop off most recent parent after leaving local scope
        return None;

    
    # for oeheader in header_list:
    #     oeheader = OENodeHeader(oeheader); # Convert item to class instance
    #     iterOE(oeheader);
    
    # Uncomment when ready to generate cards
    try:
        # Initialize model
        col = Collection(cpath, log=True); # NOTE that this changes the directory
        card_model = col.models.by_name("Basic"); # Search for card model
        deck = col.decks.by_name("Test"); # Set current deck
    
        for oeheader in header_list:
            # FIXME Can parse header levels at this scope and add to oeheader attribute which can be accessed later
            oeheader = OENodeHeader(oeheader); # Convert item to class instance
            iterOE(oeheader);
            
        col.save(); # Save changes to DB
    finally: # Should have this always run, otherwise, anki will get stuck        
        col.close(); # Need this function, otherwise instance stays open
        return None;

        
#%% 
# file_path = os.path.join(root_path, "Export.xml"); # For debugging when required to manually set file path instead of from CLI arguments
header_list = getHeaders(file_path);
iterHeaders(header_list);

