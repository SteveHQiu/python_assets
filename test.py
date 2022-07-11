#%% Imports
import sys
import base64

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
        return fx
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
