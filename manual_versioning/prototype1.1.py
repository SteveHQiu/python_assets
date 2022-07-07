# -*- coding: utf-8 -*-
import sys, os, base64;
from anki.storage import Collection;
from xml.etree import ElementTree;
from bs4 import BeautifulSoup;

"""
Changelog 
-Added media to cards 

"""

#%%
PROFILE_HOME = os.path.expanduser(r"~\AppData\Roaming\Anki2\User 1");
cpath = os.path.join(PROFILE_HOME, "collection.anki2");
mpath = os.path.join(PROFILE_HOME, "collection.media");
namespace = {"one": r"http://schemas.microsoft.com/office/onenote/2013/onenote"}; # Namespace to prefix tags 
# Note that elements with children nodes are iterable with the children notes being items of the container 
# Findall returns list format, even if single item, hence need to specify item



#%% Bulk load from XML


def getHeaders(xml_input: "XML file from OneNote") -> "Returns list of XML items of non-empty headers from XML":
    xml_content = ElementTree.parse(xml_input);
    headers = xml_content.find("one:Outline/one:OEChildren", namespace);
    header_list = [];
    for header in headers:
        header_text = header.find("one:T", namespace).text;
        if header.find("one:T", namespace).text != None: # Need to screen out empty lines 
            print(header_text);
        if header.find("one:OEChildren", namespace) != None: # Only for headers that have children
            header_list.append(header.find("one:OEChildren", namespace)); # Loses header text information, may need to create a class for modelling headers
    return header_list;


headers = getHeaders("Export.xml")

#%%
col = Collection(cpath, log=True); # NOTE that this changes the directory 
card_model = col.models.by_name("Basic"); # Search for card model
deck = col.decks.by_name("Test"); # Set current deck

for header in headers:
    for concept in header: # Parse concepts at lowest level of bullets 
        concept_ID = concept.attrib["objectID"];
        print(concept);
        # if concept.find("one:T", namespace) != None and concept.find("one:T", namespace).text != None:
        #     concept_points = [];
        #     concept_strhtml = concept.find("one:T", namespace).text;
        #     soup = BeautifulSoup(concept_strhtml, features="html.parser");
        #     # Parsing concepts 
        #     if soup.find_all("span", style="font-weight:bold") != []: # Search for concept span 
        #         concept_stem = soup.find_all("span", style="font-weight:bold")[0].text; # Only want to capture first bolded span
        #         if concept.find("one:OEChildren", namespace) != None: # Look for children in concept
        #             for point in concept.find("one:OEChildren", namespace):
        #                 if point.find("one:T", namespace).text != None:
        #                     point_strhtml = point.find("one:T", namespace).text;
        #                     concept_points.append(point_strhtml);               
        #         # Instantiate new note 
        #         note = col.new_note(card_model); # New new_note() method requires a card model to be passed as a parameter
        #         note.note_type()['did'] = deck['id']; # Need to set deck ID since it doesn't come with the model
        #         # Populate note, using strings to identify fields rather than strict indices in case field order changes
        #         note.fields[note._field_index("Front")] = concept_stem; 
        #         note.fields[note._field_index("Back")] = concept_strhtml;
        #         # Set the tags (and add the new ones to the deck configuration
        #         tags = "test1 test2";
        #         note.tags = col.tags.canonify(col.tags.split(tags));
        #         m = note.note_type();
        #         m['tags'] = note.tags;
        #         col.models.save(m);
        #         # Add note to DB
        #         col.addNote(note);
        if concept.find("one:Image", namespace) != None:
            img_name = f"{concept_ID}.png"
            img_path = os.path.join(mpath, img_name);
            img_str = concept.find("one:Image/one:Data", namespace).text;
            img_bytes = img_str.encode("utf-8");
            with open(img_path, "wb") as img_file:
                img_file.write(base64.decodebytes(img_bytes)); # Convert bytes format to base64 format which is read by write() function
            # Instantiate new note 
            note = col.new_note(card_model); # New new_note() method requires a card model to be passed as a parameter
            note.note_type()['did'] = deck['id']; # Need to set deck ID since it doesn't come with the model
            # Populate note, using strings to identify fields rather than strict indices in case field order changes
            note.fields[note._field_index("Front")] = "Picture"; 
            note.fields[note._field_index("Back")] = '<img src="%s"style="max-width:600px;width:100%%">' % img_name; # Double % to escape formatting of second %
            # Set the tags (and add the new ones to the deck configuration
            tags = "test1 test2";
            note.tags = col.tags.canonify(col.tags.split(tags));
            m = note.note_type();
            m['tags'] = note.tags;
            col.models.save(m);
            # Add note to DB
            col.addNote(note);
        
col.save(); # Save changes to DB
col.close(); # Need this function, otherwise instance stays open


#%% Parsing only

texts = [];
img_data = [];
for header in headers:
    header_text = header.find("one:T", namespace).text;
    if header.find("one:T", namespace).text != None: # Need to screen out empty lines 
        print(header_text);
    if header.find("one:OEChildren", namespace) != None: # Only for headers that have children 
        for concept in header.find("one:OEChildren", namespace):
            if concept.find("one:T", namespace) != None:
                str_html = concept.find("one:T", namespace).text;
                print(str_html);
                texts.append(str_html);
            if concept.find("one:Image", namespace) != None:
                a = concept.find("one:Image/one:Data", namespace);
                img_str = concept.find("one:Image/one:Data", namespace).text;
                img_data.append(img_str.encode("utf-8")); # Need to encode string into bytes/binary to store 

soup = BeautifulSoup(texts[0], features="html.parser");
# print(soup.find("span").text);
print(soup.find_all("span", style="font-weight:bold")[0].text);
# for node in soup.find_all("span", style="font-weight:bold"): # Attribute name doesn't have to be in string
#     print(''.join(node.find_all(text=True)));
    
#%% Different methods of parsing tree 

a = list(headers.iter());
b = list(headers.iterfind("one:T", namespace));
c = list(headers.itertext());

#%% Archive 1

                    # Instantiate new note 
                    note = col.newNote();
                    note.note_type()['did'] = deck['id'];
                    # Populate note
                    note.fields[note._field_index("Front")] = concept_stem; # Using strings to identify fields rather than strict indices in case field order changes
                    note.fields[note._field_index("Back")] = concept_strhtml;
                    # Set the tags (and add the new ones to the deck configuration
                    tags = "test1 test2";
                    note.tags = col.tags.canonify(col.tags.split(tags));
                    m = note.note_type();
                    m['tags'] = note.tags;
                    col.models.save(m);
                    # Add note to DB
                    col.addNote(note);
