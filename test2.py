import os


from anki.collection import Collection
from anki.decks import DeckManager


PROFILE_HOME = os.path.expanduser(R"~\AppData\Roaming\Anki2\User 1")
CPATH = os.path.join(PROFILE_HOME, "collection.anki2")
col = Collection(CPATH, log=True) # NOTE that this changes the directory

a = DeckManager(col)
a.add_normal_deck_with_name("TEST_DECK")
col.save() # Save changes to DB
col.close()
