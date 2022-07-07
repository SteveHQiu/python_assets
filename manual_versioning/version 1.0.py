# -*- coding: utf-8 -*-
import sys, os, base64, re, string;
from anki.storage import Collection;
from xml.etree import ElementTree;
from bs4 import BeautifulSoup;

"""
Changelog
-Added CLI integration 

"""

#%% Constants
PROFILE_HOME = os.path.expanduser(r"~\AppData\Roaming\Anki2\User 1");
cpath = os.path.join(PROFILE_HOME, "collection.anki2");
mpath = os.path.join(PROFILE_HOME, "collection.media");
root_path = os.path.expanduser(r"~\OneDrive - ualberta.ca\Coding\OneNote2AnkiPython");
file_name = sys.argv[1]; # Command line arguments come in list, 0 = name of script, 1 = 1rst argument passed, 2 = 2nd argument passed
file_path = os.path.join(root_path, file_name);

namespace = {"one": r"http://schemas.microsoft.com/office/onenote/2013/onenote"}; # Namespace to prefix tags
# Note that elements with children nodes are iterable with the children notes being items of the container
# Findall returns list format, even if single item, hence need to specify item

#%% Functions

def getHeaders(xml_input) -> list:
    """
    Returns list of XML items of non-empty headers from XML
    \n xml_input: path to XML file from OneNote
    """
    xml_content = ElementTree.parse(xml_input);
    list_OE_headers = xml_content.find("one:Outline/one:OEChildren", namespace); # Is actually the XML element of OEChildren containing OE headers
    header_list = [];
    for OE_header in list_OE_headers:
        OE_content = OE_header.find("one:T", namespace);
        if OE_content != None and OE_content.text != None: # Need to screen out empty lines
            header_text = OE_header.find("one:T", namespace).text;
            print(header_text);
            if OE_header.find("one:OEChildren", namespace) != None: # Only for headers that have children
                header_list.append(OE_header);
    return header_list;

def notNone(xml_element) -> bool:
    """Checks XML text element to see if it is a NoneType or contains no text"""
    if xml_element != None and xml_element.text != None:
        return True;
    else:
        return False;

def getConceptStem(html_str: str) -> str:
    """
    Returns the stem of the concept within HTML string
    \n html_str: str of HTML content of concept
    """
    soup = BeautifulSoup(html_str, features="html.parser");
    if soup.select_one('span[style*="font-weight:bold"]') != None:
        return soup.select_one('span[style*="font-weight:bold"]').text; # Returns first tag that matches selector which searches for tags with attributes containing "font-weight:bold"
    else:
        return None;

def getGroupingStem(html_str: str) -> str:
    """
    Returns the stem of the grouping or attribute within HTML string
    \n html_str: str of HTML content of grouping or attribute
    """
    soup = BeautifulSoup(html_str, features="html.parser");
    if soup.select_one('span[style*="text-decoration:underline"]') != None:
        return soup.select_one('span[style*="text-decoration:underline"]').text; # Returns first tag that matches selector
    else:
        return None;

def getGeneralStem(html_str: str) -> str:
    """
    Returns the appropriate stem when given a concept/attribute i.e., tests if there is a stem
    \n html_str: str of HTML content
    """
    if getConceptStem(html_str) != None:
        return getConceptStem(html_str);
    elif getGroupingStem(html_str) != None:
        return getGroupingStem(html_str);
    else:
        return None;

# def getChildNodes(OE_node: "XML object for an OE element node") -> \
#     "Returns non-empty child nodes":
#     if OE_node.find("one:OEChildren", namespace) != None: # Look for children in concept
#         for OE_node in OE_node.find("one:OEChildren", namespace):
#             if OE_node.find("one:T", namespace).text != None: # Look for non-empty child nodes
#                 level2_strhtml = level2.find("one:T", namespace).text;
#                 OE1_nodes.append(level2_strhtml);
#             # if OE_node.find("one:Image", namespace) != None
#     return None; # Returns none if OEChildren can't be found

def listItemsStem(OEChildren: iter, index: int) -> str:
    """
    Returns full front HTML with focus on item at given index
    \n OEChildren: OEChildren XML object container for OE nodes of interest
    \n index: Index of OE node (within OEChildren container) to focus on    
    """
    front_html = "";
    current = 0;
    for OE_node in OEChildren:
        OE_node_content = OE_node.find("one:T", namespace);
        # OE_node_image = OE_node.find("one:Image/one:Data", namespace);
        # print(OE_node_content);
        if notNone(OE_node_content) and getGeneralStem(OE_node_content.text) != None:
            stem = getGeneralStem(OE_node_content.text);
            print(stem);
            if current == index:
                if getConceptStem(OE_node_content.text) != None:
                    front_html = "".join((front_html,"<li><span style='font-weight:bold'>%s</span>:" % stem)); # Start list item
                if getGroupingStem(OE_node_content.text) != None:
                    front_html = "".join((front_html,"<li><span style='text-decoration:underline'>%s</span>:" % stem));
                print(front_html);
                if OE_node.find("one:OEChildren", namespace) != None:
                    substems = "\n<ul>\n"
                    for OE_subnode in OE_node.find("one:OEChildren", namespace):
                        OE_subnode_content = OE_subnode.find("one:T", namespace);
                        if notNone(OE_subnode_content) and getConceptStem(OE_subnode_content.text) != None:
                            substems = "".join((substems, "<li><span style='font-weight:bold'>%s</span>:</li>\n" % "___"));
                        elif notNone(OE_subnode_content) and getGroupingStem(OE_subnode_content.text) == None: # Filters for raw points, excludes groupings and attributes
                            substems = "".join((substems, "<li>Subpoint</li>\n"));
                    substems = "".join((substems, "</ul>\n"));
                    front_html = "".join((front_html, substems)); # Append substems to main HTML
                front_html = "".join((front_html,"</li>\n")); # Close list item
            elif getGeneralStem(OE_node_content.text) != None:
                if getConceptStem(OE_node_content.text) != None:
                    front_html = "".join((front_html,"<li><span style='font-weight:bold;color:#BEBEBE'>%s</span></li>\n" % stem)); # Will only render stems, ignores points without stems
                if getGroupingStem(OE_node_content.text) != None:
                    front_html = "".join((front_html,"<li><span style='text-decoration:underline;color:#BEBEBE'>%s</span></li>\n" % stem)); # Will onder render stems, ignores points without stems
                print("Subpoint");
        current += 1;
    front_html = "".join(("<ul>\n",front_html,"</ul>"));
    return front_html;

def listItemsFull(OEChildren: list, index: int, parent_node: str) -> str:
    """
    Returns greyed HTML list of complete items contained within the given container
    with item with the given index ungreyed i.e., focuses on item of index 
    \n OEChildren: OEChildren XML object container for OE nodes of interest
    \n index: Index of OE node (within OEChildren container) to focus on
    \n parent_node: str of parent node that is used to label image
    """
    def getChildText(OEChildren: list):
        """
        Is recursively used inside of the listItemsFull() function 
        \n OEChildren: OEChildren XML object container for OE nodes of interest
        """
        nonlocal subsubpoints; # Uses subsubpoints str container from the function that calls it
        subsubpoints = "".join((subsubpoints,"<ul>\n")); # Open container
        for OE_node in OEChildren:
            OE_node_content = OE_node.find("one:T", namespace);
            OE_node_img = OE_node.find("one:Image/one:Data", namespace); # Should not parse image data
            # print(OE_node_content);
            if notNone(OE_node_content):
                subsubpoints = "".join((subsubpoints,"<li><span style='color:#BEBEBE'>%s</span>" % OE_node_content.text));
                if OE_node.find("one:OEChildren", namespace) != None:
                    subsubpoints = getChildText(OE_node.find("one:OEChildren", namespace));
                subsubpoints = "".join((subsubpoints,"</li>\n" ));
                # print(OE_node_content.text);
            if OE_node_img != None and OE_node_img.text != None:
                subsubpoints = "".join((subsubpoints,"<li><span style='color:#BEBEBE'>+Diagram</li>\n"));
        subsubpoints = "".join((subsubpoints,"</ul>\n")); # Close container
        return subsubpoints;
    
    back_html = "";
    context_img = ""; # Context pictures should always apply to all nodes at the same level, thus can be displayed at the end
    current = 0;
    print(current);
    img_count = 0; # Counter to keep track of images so that there are no duplicates of images
    for OE_node in OEChildren:
        OE_node_content = OE_node.find("one:T", namespace);
        OE_node_img = OE_node.find("one:Image/one:Data", namespace);
        # print(OE_node_content);
        if notNone(OE_node_content):
            if current == index:
                OE_node_stem = getGeneralStem(OE_node_content.text);
                OE_node_stem = re.sub(r'[^\w\s]', '', OE_node_stem);
                back_html = "".join((back_html,"<li>%s" % OE_node_content.text)); # Start list item
                # print(back_html);
                if OE_node.find("one:OEChildren", namespace) != None:
                    subpoints = "\n<ul>\n"; # Open sub-list
                    subnode_img_count = 0;
                    for OE_subnode in OE_node.find("one:OEChildren", namespace):
                        OE_subnode_content = OE_subnode.find("one:T", namespace);
                        OE_subnode_img = OE_subnode.find("one:Image/one:Data", namespace);
                        if notNone(OE_subnode_content): # Filters for any text features including raw points 
                            subpoints = "".join((subpoints, "<li>\n")); # Start sub-list item
                            if getConceptStem(OE_subnode_content.text) != None:
                                concept_stem = getConceptStem(OE_subnode_content.text);
                                concept_body = OE_subnode_content.text.replace(concept_stem, "", 1); # Remove stem to only get body
                                subpoints = "".join((subpoints, "<span style='font-weight:bold'>%s</span>" % concept_stem)); 
                                subpoints = "".join((subpoints, "<span style='color:#BEBEBE'>%s</span>" % concept_body));
                            elif getGroupingStem(OE_subnode_content.text) != None: # Filters for groupings which will be greyed out
                                subpoints = "".join((subpoints, "<span style='color:#BEBEBE'>%s</span>" % OE_subnode_content.text)); 
                            else: 
                                subpoints = "".join((subpoints, OE_subnode_content.text)); 
                            if OE_subnode.find("one:OEChildren", namespace) != None:
                                subsubpoints = ""; # Declare and initiate subsubpoint container
                                subsubpoints = getChildText(OE_subnode.find("one:OEChildren", namespace)); # Use getChildrenText recursive function to add to all children nodes that aren't highlighted
                                subpoints = "".join((subpoints, subsubpoints));
                            subpoints = "".join((subpoints, "</li>\n")); # End sub-list item
                        if OE_subnode_img != None and OE_subnode_img.text != None:
                            img_name = "%s.png" % (OE_node_stem + str(subnode_img_count)); # FIXME Might need to link more contexts in the future so that same concepts don't have overlapping picture names
                            img_path = os.path.join(mpath, img_name);
                            img_str = OE_subnode_img.text;
                            img_bytes = img_str.encode("utf-8");
                            with open(img_path, "wb") as img_file: # Write image to media directory
                                img_file.write(base64.decodebytes(img_bytes)); # Convert bytes format to base64 format which is read by write() functio
                            subpoints = "".join((subpoints,"<li><img src='%s'style='max-width:600px'></li>" % img_name));
                            subnode_img_count += 1;
                    subpoints = "".join((subpoints, "</ul>\n")); # Close sub-list 
                    back_html = "".join((back_html, subpoints)); # Append subpoints to main HTML
                back_html = "".join((back_html,"</li>\n")); # Close list item
            else: # For points of same rank 
                back_html = "".join((back_html,"<li><span style='color:#BEBEBE'>"));
                if OE_node.find("one:OEChildren", namespace) != None:
                    back_html = "".join((back_html,"(+)"))
                back_html = "".join((back_html,"%s</span></li>\n" % OE_node_content.text)); #
                # print(OE_node_content.text);
        if OE_node_img != None and OE_node_img.text != None:
            img_name = "%s.png" % (parent_node + str(img_count)); # FIXME might need to add more context relative to the title  
            img_path = os.path.join(mpath, img_name);
            img_str = OE_node_img.text;
            img_bytes = img_str.encode("utf-8");
            with open(img_path, "wb") as img_file: # Write image to media directory
                img_file.write(base64.decodebytes(img_bytes)); # Convert bytes format to base64 format which is read by write() functio
            context_img = "".join((context_img,"<li><img src='%s'style='max-width:600px'></li>\n" % img_name)); # Store reference in context_img variable and add at very end
            # back_html = "".join((back_html,"<li><img src='%s'style='max-width:600px'></li>\n" % img_name)) # Legacy line that can be used instead if you want images to be in order
            img_count += 1;
        current += 1;
    back_html = "".join((back_html, context_img));
    back_html = "".join(("<ul>\n",back_html,"</ul>"));
    return back_html;

def iterHeaders(OEChildren_outline: object) -> None:
    """
    Iterates over all nodes in given container to generate cards
    
    Parameters
    ----------
    OEChildren_outline : object
        XML OEChildren object of Outline tag under OneNote page XML

    Returns
    -------
    None
    """
    def iterOE(OE_header: object) -> None:
        """
        Function that generates cards of child OE items
    
        Parameters
        ----------
        OE_header : object
            OE XML object from onenote with sub-items
    
        Returns
        -------
        None
        """
        nonlocal header_tracker;
        nonlocal parent_tracker;
        nonlocal indent_tracker; # Levels {0: root points, 1: sub points, 2: sub-sub points,...}
        OEChildren1 = OE_header.find("one:OEChildren", namespace);
        if notNone(OE_header.find("one:T", namespace)): 
            OE_header_text = OE_header.find("one:T", namespace).text;
            img_pattern = re.compile('[\W_]+');
            OE_header_imgstem = img_pattern.sub('', OE_header_text)[0:75];
            # if getGeneralStem(OE_header_text) != None:
            #     OE_header_stem = getGeneralStem(OE_header_text);
            #     parent_tracker = "".join((parent_tracker, "<span style='color:#BEBEBE'>%s</span>\n\n" % OE_header_stem));
        # print(OE_header_ind);
        for OE1 in OEChildren1: # Parse concepts at lowest level of bullets
            OE1_ind = list(OEChildren1).index(OE1); # Returns the index of the current OE in the OEChildren container
            # print(OE1, list(OEChildren1).index(OE1));
            OE1_content = OE1.find("one:T", namespace);
            if notNone(OE1_content) and getGeneralStem(OE1_content.text) != None:
                print(getGeneralStem(OE1_content.text));
                # Fill in fields for cards
                OE1_front = listItemsStem(OEChildren1, OE1_ind);
                for parent in parent_tracker: # Wraps info of parent nodes around returned HTML list 
                    if getGroupingStem(OE1_content.text) != None and parent_tracker.index(parent) == 0: #FIXME potential problem: if the current node is a grouping and it is the first item of the tracker
                        OE1_front = "".join(("<ul>\n<li><span style='font-weight:bold'>%s</span>\n" % getConceptStem(parent), OE1_front, "\n</li>\n</ul>"));
                    else:
                        if getConceptStem(parent) != None:
                            OE1_front = "".join(("<ul>\n<li><span style='font-weight:bold;color:#BEBEBE'>%s</span>\n" % getConceptStem(parent), OE1_front, "\n</li>\n</ul>"));
                        else: # Assume that it is a grouping instead
                            OE1_front = "".join(("<ul>\n<li><span style='text-decoration:underline;color:#BEBEBE'>%s</span>\n" % getGroupingStem(parent), OE1_front, "\n</li>\n</ul>"));
                OE1_front = "".join(("<span style='color:#BEBEBE'>%s</span>\n\n" % header_tracker, OE1_front));
                OE1_back = listItemsFull(OEChildren1, OE1_ind, OE_header_imgstem);
                for parent in parent_tracker: # Wraps info of parent nodes around returned HTML list 
                    if getGroupingStem(OE1_content.text) != None and parent_tracker.index(parent) == 0: #FIXME potential problem: if the current node is a grouping and it is the first item of the tracker
                        OE1_back = "".join(("<ul>\n<li>%s\n" % parent, OE1_back, "\n</li>\n</ul>"));
                    else:
                        OE1_back = "".join(("<ul>\n<li><span style='color:#BEBEBE'>%s</span>\n" % parent, OE1_back, "\n</li>\n</ul>"));
                # Instantiate new note
                note = col.new_note(card_model); # New new_note() method requires a card model to be passed as a parameter
                note.note_type()['did'] = deck['id']; # Need to set deck ID since it doesn't come with the model
                # Populate note, using strings to identify fields rather than strict indices in case field order changes
                note.fields[note._field_index("Front")] = OE1_front;
                note.fields[note._field_index("Back")] = OE1_back;
                # Set the tags (and add the new ones to the deck configuration
                tags = "test1 test2";
                note.tags = col.tags.canonify(col.tags.split(tags));
                m = note.note_type();
                m['tags'] = note.tags;
                col.models.save(m);
                # Add note to DB
                col.addNote(note);
                if OE1.find("one:OEChildren", namespace) != None: # Children concepts and groupings should not be nested under plain text, otherwise there would be concept stem for front
                    parent_tracker.insert(0, OE1_content.text); # Add tracker before jumping into more local scope, insert item at beginning since it will be the first item parsed 
                    iterOE(OE1);
                    parent_tracker.pop(0); # Pop off tracker after leaving local scope 
        return None;
    try:
        # Initialize model
        col = Collection(cpath, log=True); # NOTE that this changes the directory
        card_model = col.models.by_name("Basic"); # Search for card model
        deck = col.decks.by_name("Test"); # Set current deck
    
        for OE_header in OEChildren_outline:
            header_tracker = "No header"
            parent_tracker = []
            indent_tracker = 0; # Not used. Levels {0: root points, 1: sub points, 2: sub-sub points,...}
            if notNone(OE_header.find("one:T", namespace)): 
                header_tracker = OE_header.find("one:T", namespace).text;
            iterOE(OE_header);
        col.save(); # Save changes to DB
    finally: # Should have this always run, otherwise, anki will get stuck        
        col.close(); # Need this function, otherwise instance stays open
        return None;

#%% Execution

list_OE_headers = getHeaders(file_path);
iterHeaders(list_OE_headers);

