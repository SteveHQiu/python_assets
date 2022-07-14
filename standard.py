#%% Imports
# Built-ins
import sys, os, base64, re, string
from typing import Union, Tuple, List
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

# General
from bs4 import BeautifulSoup

# Internal modules



#%% Constants

#%% Functions
def renderConcept(node: Element, front: bool, adjacent: bool) -> str:
    return
def renderGrouping(node: Element, front: bool, adjacent: bool) -> str:
    return
def renderNormalText(node: Element, front: bool, adjacent: bool) -> str:
    return
def renderImage(node: Element, front: bool, adjacent: bool) -> str:
    return
def renderEquation(node: Element, front: bool, adjacent: bool) -> str:
    return
def renderTable(node: Element, front: bool, adjacent: bool) -> str:
    return

# Mapping of node type label to corresponding function 
type_func_mapping = {}


#%% Classes
class StandardRenderer:
    """
    New instance created for each entry point 
    """
    # FIXME - Move this portion to main so that you can type without circular import
    def __init__(self, node):        
        self.node = node
        self.funcmap = {
            "concept": renderConcept,
            "grouping": renderGrouping,
            "standard": renderNormalText,
            "image": renderImage,
            "equation": renderEquation,
            "table": renderTable,
        }
        self.fronthtml = ""
        self.backhtml = ""
        
    def renderHtml(self):
        # Add parent node rendering here or in a separate function
        self.fronthtml = "FRONTHTML"
        self.backhtml = "BACKHTML"
        return 
    
    

