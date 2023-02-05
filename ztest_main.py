import os

from anki.collection import Collection
from anki.decks import DeckManager
from anki.models import ModelManager
from anki.tags import TagManager


PROFILE_HOME = os.path.expanduser(R"~\AppData\Roaming\Anki2\User 1")
CPATH = os.path.join(PROFILE_HOME, "collection.anki2")
col = Collection(CPATH)

deck = col.decks.add_normal_deck_with_name("TestDeck::Test2")
model = col.models.by_name("Basic")


print(deck.id)
print(F"Notes: {col.note_count()} | Cards: {col.card_count()}")
print(F"{col.decks.all_names_and_ids()}")

col.models
col.tags.clear_unused_tags()


# a = DeckManager(col)
# a.add_normal_deck_with_name("TEST_DECK")
# col.save() # Save changes to DB

col.close()
