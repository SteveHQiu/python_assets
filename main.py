#%% Imports
# Internal modules
from globals import getHeaders
from globals import XML_PATH
from cardarbiter import CardArbiter

#### CONSTANTS AND OTHER SETTINGS (e.g., dev mode) stored in globals.py
#%% 
if __name__ == "__main__":
    header_list = getHeaders(XML_PATH)
    crawler = CardArbiter(header_list)
    crawler.genCards()
    crawler.displayCards()

