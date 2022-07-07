# -*- coding: utf-8 -*-
import sys, os;
from anki.storage import Collection;

#%%

PROFILE_HOME = os.path.expanduser(r"~\AppData\Roaming\Anki2\User 1");
cpath = os.path.join(PROFILE_HOME, "collection.anki2");

try:
    col = Collection(cpath, log=True);
    # for cid in col.findNotes("tag:*"):
    #     note = col.getNote(cid);
    #     front = note.fields[0];
    #     print(front);
    print(col.card_count());
    print(col.card_count() - 153); # Used for debugging C# tool
finally: 
    col.close() # Need this function, otherwise instance stays open
