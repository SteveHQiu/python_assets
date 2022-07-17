#%% Imports
import sys, os
from anki.storage import Collection
import inspect

#%% Math ML processing
import re
from bs4 import BeautifulSoup
from mathml2latex.mathml import process_mathml

math_str = '<!--[if mathML]><mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="block"><mml:mi>x</mml:mi><mml:mo>=</mml:mo><mml:mfrac><mml:mrow><mml:mo>−</mml:mo><mml:mi>b</mml:mi><mml:mo>±</mml:mo><mml:msqrt><mml:mrow><mml:msup><mml:mi>b</mml:mi><mml:mn>2</mml:mn></mml:msup><mml:mo>−</mml:mo><mml:mn>4</mml:mn><mml:mi>a</mml:mi><mml:mi>c</mml:mi></mml:mrow></mml:msqrt></mml:mrow><mml:mrow><mml:mn>2</mml:mn><mml:mi>a</mml:mi></mml:mrow></mml:mfrac></mml:math><![endif]-->'
math_str = math_str.replace("<!--[if mathML]>", "").replace("<![endif]-->", "") # Replace end tags
print(math_str)
tags: list[str] = re.findall("<.*?>", math_str) # Finds all HTML tags
for tag in tags:
    new_tag = tag.replace("mml:", "")
    math_str = math_str.replace(tag, new_tag, 1) # Replace first instance of the match with new tag
print(math_str)
soup1 = BeautifulSoup(math_str, features="html.parser")
c = process_mathml(soup1)
print(c)

a = """
<![CDATA[<!--[if mathML]><math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="block"><mi>x</mi><mo>=</mo><mfrac><mrow><mo>−</mo><mi>b</mi><mo>±</mo><msqrt><mrow><msup><mi>b</mi><mn>2</mn></msup><mo>−</mo><mn>4</mn><mi>a</mi><mi>c</mi></mrow></msqrt></mrow><mrow><mn>2</mn><mi>a</mi></mrow></mfrac></math><![endif]-->]]
"""
soup2 = BeautifulSoup(a, features="html.parser")
b = process_mathml(soup2)
print(b)

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
