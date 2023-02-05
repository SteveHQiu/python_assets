#%% Collection manipulation
import os
from anki.collection import Collection
from anki.notes import Note

from anki.decks import DeckManager
from anki.models import ModelManager
from anki.tags import TagManager


PROFILE_HOME = os.path.expanduser(R"~\AppData\Roaming\Anki2\User 1")
CPATH = os.path.join(PROFILE_HOME, "collection.anki2")
col = Collection(CPATH)


#%%
model = col.models.by_name("Basic") # Returns a NoteType dict which is needed to specify new note
note = col.new_note(model) # Create new note instance **Doesn't add note to collection

note.fields[note._field_index("Front")] = "TEst" # Note fields are stored in list of strings, need method to find index of labeled field
note.fields[note._field_index("Back")] = "TEST"
note.add_tag("test3") # Tag strings with spaces will be treated as separate tags 


deck = col.decks.add_normal_deck_with_name("TestDeck::Test2") # Returns a container with the deck id
col.add_note(note, deck.id) # Adds note to database
col.save() # Save DB, mostly redundant but added just in case 
#%%
print(F"Notes: {col.note_count()} | Cards: {col.card_count()}")
for deck_cont in col.decks.all_names_and_ids():
    print(F"{deck_cont.name}: {col.decks.card_count(deck_cont.id, include_subdecks=False)}")
    

#%%

col.close()

#%% HTML URL encoding
import urllib.parse
print(urllib.parse.quote("1 Resp _ Cardio/1 Respirology/Physiology.one"))
print(urllib.parse.quote("#General&section-id={3609411B-5EDC-483B-A4F2-A60FE8A914A4}"))

#%%
a = R"https://ualbertaca-my.sharepoint.com/personal/hqiu1_ualberta_ca/Documents/OneNote/1 Resp _ Cardio/1 Respirology/Physiology.one#General&section-id={3609411B-5EDC-483B-A4F2-A60FE8A914A4}"

onenote_dir = R"Documents/OneNote/"
b = a.split(onenote_dir)
base_url = b[0] + onenote_dir
section_url = "".join(b[1:]) # Join rest of results in case onenote_dir occurs later on in path
section_url = urllib.parse.quote(section_url) # Encode second part as a URL
print(base_url+section_url)


#%% MathML processing
import lxml.etree as ET
import re

def convertMath(math_str: str, inline: bool = False) -> str:
    """
    Takes a string with 
    Modified from: https://dev.to/furkan_kalkan1/quick-hack-converting-mathml-to-latex-159c
    """
    # Formatting specific to OneNote MathML output
    math_objects: list[str] = re.findall(R"<!\-\-\[if mathML\]>.*?<!\[endif\]\-\->", math_str)
    for original_math in math_objects:
        math_mml = original_math.replace("<!--[if mathML]>", "").replace("<![endif]-->", "") # Extract mathmml component but leave original 
        html_tags: list[str] = re.findall("<.*?>", math_mml) # Finds all HTML tags
        for tag in html_tags: # Iterate through matches to replace namespace component (no easy regex way to do it)
            new_tag = tag.replace("mml:", "")
            new_tag = new_tag.replace(":mml", "") # Still need xmlns attribute to use XSLT to parse
            math_mml = math_mml.replace(tag, new_tag, 1) # Replace first instance of the match with new tag
    
        # Exception parsing: For errors due to undefined symbols, can probably find a reference here http://zvon.org/comp/r/ref-MathML_2.html#intro
        math_mml = math_mml.replace("&nbsp;", "&#x02004;") # nbsp not in XSLT entities, replace with code for 1/3emspace http://zvon.org/comp/r/ref-MathML_2.html#Entities~emsp
    
        print(math_mml)
        math_xml = ET.fromstring(math_mml)
        xslt_table = ET.parse("mml2tex/mmltex.xsl") # This XSL file links to the other other XSL files in the folder
        transformer = ET.XSLT(xslt_table)
        math_tex = str(transformer(math_xml)) # Convert transformed output to string
        if inline: # Format for inline rendering:
            math_tex = math_tex.replace("\n\\[", "\\(") # Can replace square brackets with regular for inline display https://docs.ankiweb.net/math.html
            math_tex = math_tex.replace("\n\\]", "\\)")
            math_tex = re.sub(R"^\$ ?", R"\(", math_tex) # Inline tends to replace with $ signs at beginning and end, will replace these with inline rendering indicators
            math_tex = re.sub(R" ?\$$", R"\)", math_tex)
        print(math_tex)
        math_str = math_str.replace(original_math, math_tex) # Replace original found math object with converted tex object


    return math_str

math_str = '<math><munderover><mo stretchy="false">∑</mo><mrow><mi>i</mi><mo>=</mo><mi>s</mi><mi>t</mi><mi>a</mi><mi>r</mi><mi>t</mi></mrow><mrow><mi>s</mi><mi>t</mi><mi>o</mi><mi>p</mi></mrow></munderover><mrow><mo fence="false">(</mo><mi>expression</mi><mo>&nbsp;</mo><mi>involving</mi><mo>&nbsp;</mo><mi>i</mi><mo fence="false">)</mo></mrow></math>'
math_str = '<math><munderover><mo stretchy="false">∑</mo><mrow><mi>i</mi><mo>=</mo><mi>s</mi><mi>t</mi><mi>a</mi><mi>r</mi><mi>t</mi></mrow><mrow><mi>s</mi><mi>t</mi><mi>o</mi><mi>p</mi></mrow></munderover><mrow><mo fence="false">(</mo><mi>expression</mi><mo>&#x2003;</mo><mi>involving</mi><mo>&#x2003;</mo><mi>i</mi><mo fence="false">)</mo></mrow></math>'
math_str = '<mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="block"><mml:mi>x</mml:mi><mml:mo>=</mml:mo><mml:mfrac><mml:mrow><mml:mo>−</mml:mo><mml:mi>b</mml:mi><mml:mo>±</mml:mo><mml:msqrt><mml:mrow><mml:msup><mml:mi>b</mml:mi><mml:mn>2</mml:mn></mml:msup><mml:mo>−</mml:mo><mml:mn>4</mml:mn><mml:mi>a</mml:mi><mml:mi>c</mml:mi></mml:mrow></mml:msqrt></mml:mrow><mml:mrow><mml:mn>2</mml:mn><mml:mi>a</mml:mi></mml:mrow></mml:mfrac></mml:math>'
math_str = '<!--[if mathML]><mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="block"><mml:mi>x</mml:mi><mml:mo>=</mml:mo><mml:mfrac><mml:mrow><mml:mo>−</mml:mo><mml:mi>b</mml:mi><mml:mo>±</mml:mo><mml:msqrt><mml:mrow><mml:msup><mml:mi>b</mml:mi><mml:mn>2</mml:mn></mml:msup><mml:mo>−</mml:mo><mml:mn>4</mml:mn><mml:mi>a</mml:mi><mml:mi>c</mml:mi></mml:mrow></mml:msqrt></mml:mrow><mml:mrow><mml:mn>2</mml:mn><mml:mi>a</mml:mi></mml:mrow></mml:mfrac></mml:math><![endif]-->'
math_str = """<span style='font-weight:bold;font-family:Calibri' lang=en-CA>Level 1 node</span><span style='font-family:Calibri' lang=en-CA>: description with </span><!--[if mathML]><mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML"><mml:mi>E</mml:mi><mml:mi>q</mml:mi><mml:mi>u</mml:mi><mml:mi>a</mml:mi><mml:mi>t</mml:mi><mml:mi>i</mml:mi><mml:mi>o</mml:mi><mml:mi>n</mml:mi><mml:mo>&nbsp;</mml:mo><mml:mn>1</mml:mn><mml:mo>=</mml:mo><mml:mi>a</mml:mi><mml:mo>+</mml:mo><mml:mi>b</mml:mi></mml:math><![endif]--><span style='font-family:Calibri' lang=en-CA> rest of description</span>"""

# print(processMath(math_str))
convertMath(math_str, inline=True)
#%% MathML Processing 2
import re
import lxml.etree as ET

def to_latex(text):

    """ Remove TeX codes in text"""
    text = re.sub(r"(\$\$.*?\$\$)", " ", text) 

    """ Find MathML codes and replace it with its LaTeX representations."""
    mml_codes = re.findall(r"(<math.*?<\/math>)", text)
    for mml_code in mml_codes:
        mml_ns = mml_code.replace('<math>', '<math xmlns="http://www.w3.org/1998/Math/MathML">') #Required.
        mml_dom = ET.fromstring(mml_ns)
        xslt = ET.parse("mml2tex/mmltex.xsl")
        transform = ET.XSLT(xslt)
        mmldom = transform(mml_dom)
        latex_code = str(mmldom)
        text = text.replace(mml_code, latex_code)
    return text
math_str = '<math xmlns="http://www.w3.org/1998/Math/MathML"><msub><mrow><mfenced open="‖" close="‖"><mi>&#119857;</mi></mfenced></mrow><mi>p</mi></msub><mo>=</mo><msup><mrow><mfenced open="[" close="]"><mrow><msup><mrow><mfenced open="|" close="|"><mrow><msub><mi>x</mi><mn>1</mn></msub></mrow></mfenced></mrow><mi>p</mi></msup><mo>+</mo><msup><mrow><mfenced open="|" close="|"><mrow><msub><mi>x</mi><mn>2</mn></msub></mrow></mfenced></mrow><mi>p</mi></msup><mo>+</mo><mo>…</mo><mo>+</mo><msup><mrow><mfenced open="|" close="|"><mrow><msub><mi>x</mi><mi>n</mi></msub></mrow></mfenced></mrow><mi>p</mi></msup></mrow></mfenced></mrow><mrow><mfrac><mn>1</mn><mi>p</mi></mfrac></mrow></msup><mo>=</mo><msup><mrow><mfenced open="[" close="]"><mrow><munderover><mo stretchy="false">∑</mo><mrow><mi>i</mi><mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover><mrow><msup><mrow><mfenced open="|" close="|"><mrow><msub><mi>x</mi><mi>i</mi></msub></mrow></mfenced></mrow><mi>p</mi></msup></mrow></mrow></mfenced></mrow><mrow><mfrac><mn>1</mn><mi>p</mi></mfrac></mrow></msup></math>'
math_str = '<math><munderover><mo stretchy="false">∑</mo><mrow><mi>i</mi><mo>=</mo><mi>s</mi><mi>t</mi><mi>a</mi><mi>r</mi><mi>t</mi></mrow><mrow><mi>s</mi><mi>t</mi><mi>o</mi><mi>p</mi></mrow></munderover><mrow><mo fence="false">(</mo><mi>expression</mi><mo>&#x2003;</mo><mi>involving</mi><mo>&#x2003;</mo><mi>i</mi><mo fence="false">)</mo></mrow></math>'
print(to_latex(math_str))


math_str = '<![CDATA[<!--[if mathML]><mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="block"><mml:msub><mml:mrow><mml:mfenced open="‖" close="‖"><mml:mi>&#119857;</mml:mi></mml:mfenced></mml:mrow><mml:mi>p</mml:mi></mml:msub><mml:mo>=</mml:mo><mml:msup><mml:mrow><mml:mfenced open="[" close="]"><mml:mrow><mml:msup><mml:mrow><mml:mfenced open="|" close="|"><mml:mrow><mml:msub><mml:mi>x</mml:mi><mml:mn>1</mml:mn></mml:msub></mml:mrow></mml:mfenced></mml:mrow><mml:mi>p</mml:mi></mml:msup><mml:mo>+</mml:mo><mml:msup><mml:mrow><mml:mfenced open="|" close="|"><mml:mrow><mml:msub><mml:mi>x</mml:mi><mml:mn>2</mml:mn></mml:msub></mml:mrow></mml:mfenced></mml:mrow><mml:mi>p</mml:mi></mml:msup><mml:mo>+</mml:mo><mml:mo>…</mml:mo><mml:mo>+</mml:mo><mml:msup><mml:mrow><mml:mfenced open="|" close="|"><mml:mrow><mml:msub><mml:mi>x</mml:mi><mml:mi>n</mml:mi></mml:msub></mml:mrow></mml:mfenced></mml:mrow><mml:mi>p</mml:mi></mml:msup></mml:mrow></mml:mfenced></mml:mrow><mml:mrow><mml:mfrac><mml:mn>1</mml:mn><mml:mi>p</mml:mi></mml:mfrac></mml:mrow></mml:msup><mml:mo>=</mml:mo><mml:msup><mml:mrow><mml:mfenced open="[" close="]"><mml:mrow><mml:munderover><mml:mo stretchy="false">∑</mml:mo><mml:mrow><mml:mi>i</mml:mi><mml:mo>=</mml:mo><mml:mn>1</mml:mn></mml:mrow><mml:mi>n</mml:mi></mml:munderover><mml:mrow><mml:msup><mml:mrow><mml:mfenced open="|" close="|"><mml:mrow><mml:msub><mml:mi>x</mml:mi><mml:mi>i</mml:mi></mml:msub></mml:mrow></mml:mfenced></mml:mrow><mml:mi>p</mml:mi></mml:msup></mml:mrow></mml:mrow></mml:mfenced></mml:mrow><mml:mrow><mml:mfrac><mml:mn>1</mml:mn><mml:mi>p</mml:mi></mml:mfrac></mml:mrow></mml:msup></mml:math><![endif]-->]]>'
math_str = '<!--[if mathML]><mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="block"><mml:mi>x</mml:mi><mml:mo>=</mml:mo><mml:mfrac><mml:mrow><mml:mo>−</mml:mo><mml:mi>b</mml:mi><mml:mo>±</mml:mo><mml:msqrt><mml:mrow><mml:msup><mml:mi>b</mml:mi><mml:mn>2</mml:mn></mml:msup><mml:mo>−</mml:mo><mml:mn>4</mml:mn><mml:mi>a</mml:mi><mml:mi>c</mml:mi></mml:mrow></mml:msqrt></mml:mrow><mml:mrow><mml:mn>2</mml:mn><mml:mi>a</mml:mi></mml:mrow></mml:mfrac></mml:math><![endif]-->'
math_str = '<mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="block"><mml:mi>x</mml:mi><mml:mo>=</mml:mo><mml:mfrac><mml:mrow><mml:mo>−</mml:mo><mml:mi>b</mml:mi><mml:mo>±</mml:mo><mml:msqrt><mml:mrow><mml:msup><mml:mi>b</mml:mi><mml:mn>2</mml:mn></mml:msup><mml:mo>−</mml:mo><mml:mn>4</mml:mn><mml:mi>a</mml:mi><mml:mi>c</mml:mi></mml:mrow></mml:msqrt></mml:mrow><mml:mrow><mml:mn>2</mml:mn><mml:mi>a</mml:mi></mml:mrow></mml:mfrac></mml:math>'



#%% Reference vs copy
a = [1, 2, 3]
b = a
b[2] = 11
a[0] = 144

print("list a:", a)
print("list b:", b)

a = "abcd"
b = a
b[2] = "z"
a[0] = "y"

print("list a:", a)
print("list b:", b)

#%% String slicing
a = "test string 1"
print(a[0:100])

#%% List indices
for i in range(5, 0, -1):
    print(i)
    print(F"Looking at {i-1}")

#%% Unpacking comprehensions 

norm_list = [[[1,2],[1,2]],[[1,2],[1,2]]]
flat_list = [num for list1st in norm_list for list2nd in list1st for num in list2nd]

#%% Getting attributes via string, modifying vs referencing attributes

b = "temp1"
c = ["test"]


class tempClass:
    def __init__(self):
        self.data1 = 'data1 info'
        self.data2 = b
        self.data3 = c

a = tempClass()
print(a.__getattribute__("data1"))
print(a.__getattribute__("data2"))
b = "modified"
print(a.__getattribute__("data2"))
print(a.__getattribute__("data3"))
c.append("new value")
print(a.__getattribute__("data3"))
c = ["new list"]
print(a.__getattribute__("data3"))


#%% Substring search and insert

text = "value=20; style='list-style-type: decimal'"
ind = text.rfind("'")
new_string = text[:ind] + "</li>" + text[ind:]
print(new_string)

#%% HTML Obtaining body via stem
from bs4 import BeautifulSoup

html = "<p>Good, <b>bad</b>, and <i>ug<b>l</b><u>y</u></i></p>"
text = "<span style='font-weight:bold'>Concept</span>: concept definition"
soup = BeautifulSoup(text)
results = soup.select_one('span[style*="font-weight:bold"]')
print(results)
print(soup.text)
results.decompose() # Destroys element 
print(soup.text)
# Can delete tag but keep contents with tag.replaceWithChildren() method - https://stackoverflow.com/questions/1765848/remove-a-tag-using-beautifulsoup-but-keep-its-contents

#%% Timing branchless string computations
import time

cycles = 10000000

def timerDecorator(fx):
    def wrapper():
        start = time.time()
        for i in range(cycles):
            fx()
        print(time.time() - start)
        return
    return wrapper

class tempClass:
    def __init__(self):
        self.data1 = ''
        self.data2 = 'This is a string wwwwwwwwwsadfadfj;alskjflaskdv;lsejg;oserijg;osdb;osemg;osaij;sokdmblxkcmn.,kjn;ogwjipoivj;lxzkcfj;leskjgwiogj;sdlkfnv;slkdfng;klsj;fdoigj;sdkngm;lsdkfjg;sodfjgpoirgj;sdknf;saeiutposeiug'

a = tempClass()

@timerDecorator
def fx1():
    return (R'conditional '*bool(a.data1) + R'constant')

@timerDecorator
def fx2(): 
    if a.data1:
        return R'conditional constant'
    else:
        return R'constant'
    
@timerDecorator
def fx3():    
    return R'conditional '*bool(a.data2) + R'constant'

@timerDecorator
def fx4(): 
    if a.data2:
        return R'conditional constant'
    else:
        return R'constant'
    
fx1()
fx2()
fx3()
fx4()



#%% String to set of characters
a = "test string"
b = "abc"
c = "aesdfjgposijdbokwnb4;oijsdpofxldkmn;sejh;sdojfv;lzmn;vljspoejigs"
print(set(a))
print(bool(set(a)))
print(bool(set()))
print(bool(set(a).intersection(set(b))))
"".join(set(a))
"".join(set(b))
"".join(set(c))
print(list(a))
"".join(list(a))

#%% Function name reporting
import inspect
def getFxName(): # Function that will return and print out name of currently calling function
    return inspect.stack()[1].function

def testFunction():
    a = getFxName()
    print(a)
    return

testFunction()
    

#%% Branchless adding of closure tags
def f(x):
    if x:
        return "<li>Contents"
    else:
        return ""

print(bool("")*"<li>Contents"+bool("True")*"</li>")
print("")
print(f(True)+"</li>"*bool(f(True)))
print(f(False)+"</li>"*bool(f(False)))
print(f("Lmao")+"</li>"*bool(f("Lmao")))



#%% Additional test cell
"""
Additional test lines
"""

#%%
print(" f ")
print(" f ".strip())
print("   ")
print("  ".strip())
print("end")



#%% Nested scopes

class A:
    def __init__(self):
        self.a = 1
        self.b = 2
        self.c = 3
    def seta(self):
        def afunction(): # self variable has no special meaning in arguments beyond the root class scope
            self.a = 4
        afunction()
    def geta(self):
        return self.a

cA = A()
print(cA.a)
cA.seta()
print(cA.a)


#%% Function holder
class FuncHolder:
    def __init__(self, funcs):
        self.funcs = [*funcs]
    
    def iterFuncs(self, arg1, arg2, arg3):
        for func in self.funcs:
            print(func(arg1, arg2, arg3))
        return
    

def fa(arg1, arg2, arg3):
    return arg1 + arg2 + arg3
def fb(arg1, arg2, arg3):
    return arg1 * arg2 * arg3
def fc(arg1, arg2, arg3):
    return arg1 - arg2 - arg3
funcs = [fa, fb, fc]

holder = FuncHolder(funcs)
holder.iterFuncs(1, 3, 5)

# %% HTML search
from bs4 import BeautifulSoup
html = R"<span style='font-weight:bold'>Level 2 concept node</span>: description"
html = R'<!--[if mathML]><mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="block"><mml:mi>E</mml:mi><mml:mi>q</mml:mi><mml:mi>u</mml:mi><mml:mi>a</mml:mi><mml:mi>t</mml:mi><mml:mi>i</mml:mi><mml:mi>o</mml:mi><mml:mi>n</mml:mi><mml:mo>:</mml:mo><mml:mi>x</mml:mi><mml:mo>=</mml:mo><mml:mfrac><mml:mrow><mml:msup><mml:mi>y</mml:mi><mml:mn>2</mml:mn></mml:msup></mml:mrow><mml:mrow><mml:mi>a</mml:mi><mml:mi>b</mml:mi></mml:mrow></mml:mfrac></mml:math><![endif]-->'
html = None
soup = BeautifulSoup(html, features="html.parser")
print(soup.find_all())
print(soup.find('mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="block"'))
print(soup.select_one('span[style*="font-weight:bold"]'))

#%% System arguments
import sys
output = sys.argv[1]
print(output)

#%% Images

# img_str = b"""text"""
# # Input needs to be a byte string
# with open("TestImage.png", "wb") as img_file:
#     img_file.write(base64.decodebytes(img_str))


#%% Decorator functions
def decorator(a, b):
    def wrapper(fx):
        print(a, b)
        print("Wrapper executed")
        return fx()
    return wrapper

def test2():
    print("Test2")


@decorator(1, 2)
def test():
    print("Test function")
    return

test()
test()

# %%
def decorator(fx):
    def wrapper():
        print("Wrapper executed")
        return fx()
    return wrapper


@decorator
def test():
    print("Test function")
    return

test()

#%% Anki list cards
import os
PROFILE_HOME = os.path.expanduser(r"~\AppData\Roaming\Anki2\User 1")
cpath = os.path.join(PROFILE_HOME, "collection.anki2")

try:
    col = Collection(cpath, log=True)
    # for cid in col.findNotes("tag:*"):
    #     note = col.getNote(cid);
    #     front = note.fields[0];
    #     print(front);
    print(col.card_count())
    print(col.card_count() - 153) # Used for debugging C# tool
finally: 
    col.close() # Need this function, otherwise instance stays open
