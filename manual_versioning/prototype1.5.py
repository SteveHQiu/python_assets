# -*- coding: utf-8 -*-
import sys, os, base64, re;
from anki.storage import Collection;
from xml.etree import ElementTree;
from bs4 import BeautifulSoup;

"""
Changelog
-Added full expansion of child nodes in back display 

"""

#%% Functions and constants
PROFILE_HOME = os.path.expanduser(r"~\AppData\Roaming\Anki2\User 1");
cpath = os.path.join(PROFILE_HOME, "collection.anki2");
mpath = os.path.join(PROFILE_HOME, "collection.media");
namespace = {"one": r"http://schemas.microsoft.com/office/onenote/2013/onenote"}; # Namespace to prefix tags
# Note that elements with children nodes are iterable with the children notes being items of the container
# Findall returns list format, even if single item, hence need to specify item


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
                print(back_html);
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
                                concept_body = OE_subnode_content.text.replace(concept_stem, "", 1);
                                subpoints = "".join((subpoints, "<span style='font-weight:bold'>%s</span>" % concept_stem)); # Start sub-list item
                                subpoints = "".join((subpoints, "<span style='color:#BEBEBE'>%s</span>" % concept_body));
                            elif getGroupingStem(OE_subnode_content.text) != None: # Filters for groupings which will be greyed out
                                subpoints = "".join((subpoints, "<span style='color:#BEBEBE'>%s</span>" % OE_subnode_content.text)); # Start sub-list item
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
                print(OE_node_content.text);
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




#%% Bulk load process

list_OE_headers = getHeaders("Export.xml");

col = Collection(cpath, log=True); # NOTE that this changes the directory
card_model = col.models.by_name("Basic"); # Search for card model
deck = col.decks.by_name("Test"); # Set current deck


for OE_header in list_OE_headers:
    OEChildren1 = OE_header.find("one:OEChildren", namespace);
    OE_header_ind = list_OE_headers.index(OE_header);
    OE_header_text = OE_header.find("one:T", namespace).text;
    OE_header_text = re.sub(r'[^\w\s]', '', OE_header_text);
    # print(OE_header_ind);
    for OE1 in list(OEChildren1): # Parse concepts at lowest level of bullets
        OE1_ind = list(OEChildren1).index(OE1); # Returns the index of the current OE in the OEChildren container
        # print(OE1, list(OEChildren1).index(OE1));
        OE1_content = OE1.find("one:T", namespace)
        if notNone(OE1_content) and getGeneralStem(OE1_content.text) != None:
            OE1_stem = OE1_content.text;
            # print(OE1_stem);
            # print(OE1_content);
            OE1_nodes = [];
            OE1_front = listItemsStem(OEChildren1, OE1_ind);
            OE1_back = listItemsFull(OEChildren1, OE1_ind, OE_header_text);
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
            # Function to wrap ul il OEChildren1 /il /ul around the entire and grey if not concept

        # Image parsing starts here
        # if OE1.find("one:Image", namespace) != None:
        #     img_name = f"{OE1_ID}.png"
        #     img_path = os.path.join(mpath, img_name);
        #     img_str = OE1.find("one:Image/one:Data", namespace).text;
        #     img_bytes = img_str.encode("utf-8");
        #     with open(img_path, "wb") as img_file:
        #         img_file.write(base64.decodebytes(img_bytes)); # Convert bytes format to base64 format which is read by write() function
        #     # Instantiate new note
        #     note = col.new_note(card_model); # New new_note() method requires a card model to be passed as a parameter
        #     note.note_type()['did'] = deck['id']; # Need to set deck ID since it doesn't come with the model
        #     # Populate note, using strings to identify fields rather than strict indices in case field order changes
        #     note.fields[note._field_index("Front")] = "Picture";
        #     note.fields[note._field_index("Back")] = '<img src="%s"style="max-width:600px">' % img_name; # Double % to escape formatting of second %
        #     # Set the tags (and add the new ones to the deck configuration
        #     tags = "test1 test2";
        #     note.tags = col.tags.canonify(col.tags.split(tags));
        #     m = note.note_type();
        #     m['tags'] = note.tags;
        #     col.models.save(m);
        #     # Add note to DB
        #     col.addNote(note);

col.save(); # Save changes to DB
col.close(); # Need this function, otherwise instance stays open


