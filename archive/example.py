# -*- coding: utf-8 -*-
"""
Created on Mon Aug 16 15:26:31 2021

@author: steve
"""

"""
Load a JSON file saved by the assistant to Anki.
"""

import os, json, shutil, sys

# Add Anki source to path
sys.path.append("../../anki")
from anki.storage import Collection


class Word:
    """
    Wrapper around a single JSON file
    """

    def __init__(self, doc):
        self.doc = doc

    def title(self):
        return self.doc['title']

    def rank(self):
        return self.doc['rank']

    def audio_url(self):
        if "audio" in self.doc and self.doc["audio"]["include"]:
            return self.doc["audio"]["url"]
        else:
            return None

    def definitions_with_samples(self):
        """ Returns the back text for the Card 1 """
        html = ""
        for type in self.doc["types"]:
            if "include" in type and type["include"]:
                subhtml = ""
                if "definitions" in type:
                    for definition in type["definitions"]:
                        if "include" in definition and definition["include"]:
                            subhtml += "<li>" + definition["text"]
                            if "quotations" in definition:
                                first_quotation = True
                                quotation_found = False
                                for quotation in definition["quotations"]:
                                    if "include" in quotation \
                                        and quotation["include"]:
                                        quotation_found = True
                                        if first_quotation:
                                            subhtml += "<ul>"
                                            first_quotation = False
                                        subhtml += "<li>" + \
                                                   quotation["text"] + \
                                                   "</li>"
                                if quotation_found:
                                    subhtml += "</ul>"
                            subhtml += "</li>"
                # Add the definition if at least one definition was included
                if subhtml:
                    html += "<em>" + type["type"] + "</em>" + \
                            "<ul>" + subhtml + "</ul>"

        return html

    def definitions_only(self):
        """ Returns the text for the front Card 7 """
        selected_definitions = []
        for type in self.doc["types"]:
            if "definitions" in type:
                for definition in type["definitions"]:
                    if "include" in definition and definition["include"]:
                        selected_definitions.append(definition["text"])
        if selected_definitions:
            html = "<ul>"
            for definition in selected_definitions:
                html += "<li>" + definition + "</li>"
            html += "</ul>"
            return html
        else:
            return None

    def image(self):
        if "images" in self.doc:
            for image in self.doc["images"]:
                if "include" in image and image["include"]:
                    return image["thumb_url"]
        return None

    def ipa(self):
        if "ipa" in self.doc:
            return self.doc["ipa"]
        return None

    def translation(self):
        """ Returns the translation block text includes in various cards """
        selected_translations = []
        if "translations" in self.doc:
            for translation in self.doc["translations"]:
                if "include" in translation and translation["include"]:
                    selected_translations.append(translation["text"])
        if selected_translations:
            return ", ".join(selected_translations)
        else:
            return None

    def synonyms(self):
        """ Returns the synonym block text includes in various cards """
        selected_synonyms = []
        if "synonyms" in self.doc:
            for synonym in self.doc["synonyms"]:
                if "include" in synonym and synonym["include"]:
                    selected_synonyms.append(synonym["text"])
        if selected_synonyms:
            return ", ".join(selected_synonyms)
        else:
            return None

    def samples(self):
        result = {}
        for type in self.doc["types"]:
            if "definitions" in type:
                for definition in type["definitions"]:
                    if "quotations" in definition:
                        for quotation in definition["quotations"]:
                            if "card_sample" in quotation \
                                and quotation["card_sample"]:
                                answer = quotation["text"]
                                sample = answer.replace(self.title(), "[...]")
                                result[sample] = answer
        return result

    def has_image_card(self):
        return "card_images" in self.doc and self.doc["card_images"]

    def has_definition_card(self):
        for type in self.doc["types"]:
            if "card_definitions" in type and type["card_definitions"]:
                return True
        return None

    def has_translation_card(self):
        return "card_translate" in self.doc and self.doc["card_translate"]



def load(col, filepath):
    """
    Load a single word into Anki.

    Read the word file.
    Check if a picture or sound is present in the same folder.

    :param filepath: the file path of the JSON document file
    """

    directory = os.path.dirname(filepath)
    basename = os.path.basename(filepath)

    media_directory = os.path.join(os.path.dirname(col.path),
                                  "collection.media")

    print("Opening file %s" % filepath)
    with open(filepath, 'r') as f:
        json_content = f.read()
        doc = json.loads(json_content)
        word = Word(doc)

        # We need to populate each one of the fields
        fields = {}
        fields["Word"] = word.title()

        if word.audio_url():
            filename = "%s-%s" % (word.rank(), word.title())
            possible_extensions = ['ogg', 'mp3']
            for extension in possible_extensions:
                audio_name = filename + '.' + extension
                audio_path = os.path.join(directory, audio_name)
                if os.path.exists(audio_path):
                    source_path = audio_path
                    target_path = os.path.join(media_directory, audio_name)
                    print("Copying media file %s to %s" %
                        (source_path, target_path))
                    col.media.addFile(source_path)
                    #shutil.copyfile(source_path, target_path)
                    fields["Sound"] = "[sound:%s]" % audio_name

        fields["DefinitionsWithSamples"] = word.definitions_with_samples()
        fields["DefinitionsOnly"] = word.definitions_only()

        if word.image():
            image_name = "%s-%s-thumb.jpg" % (word.rank(), word.title())
            image_path = os.path.join(directory, image_name)
            if os.path.exists(image_path):
                source_path = os.path.join(directory, image_name)
                target_path = os.path.join(media_directory, image_name)
                print("Copying media file %s to %s" %
                    (source_path, target_path))
                col.media.addFile(source_path)
                #shutil.copyfile(source_path, target_path)
                fields["Image"] = '<img src="%s">' % image_name

        if word.ipa():
            fields["IPA"] = word.ipa()
        if word.translation():
            fields["Translation"] = word.translation()
        if word.synonyms():
            fields["Synonyms"] = word.synonyms()

        samples = word.samples()
        if samples:
            sample_suffixes = ["A", "B", "C"]
            index = 0
            for sample, answer in samples.items():
                fields["Sample" + sample_suffixes[index]] = sample
                fields["Answer" + sample_suffixes[index]] = answer
                index += 1

        if word.has_image_card():
            fields["HasImageCard"] = str(word.has_image_card())
        if word.has_definition_card():
            fields["HasDefinitionsCard"] = str(word.has_definition_card())
        if word.has_translation_card():
            fields["HasTranslationCard"] = str(word.has_translation_card())

        # Get the deck
        deck = col.decks.byName("English")

        # Instantiate the new note
        note = col.newNote()
        note.model()['did'] = deck['id']

        # Ordered fields as defined in Anki note type
        anki_fields = [
            "Word",
            "Sound",
            "DefinitionsWithSamples",
            "DefinitionsOnly",
            "Image",
            "IPA",
            "Translation",
            "Synonyms",
            "SampleA",
            "SampleB",
            "SampleC",
            "HasImageCard",
            "HasDefinitionsCard",
            "AnswerA",
            "AnswerB",
            "AnswerC",
            "HasTranslationCard"
        ]

        for field, value in fields.items():
            note.fields[anki_fields.index(field)] = value

        # Set the tags (and add the new ones to the deck configuration
        tags = "word"
        note.tags = col.tags.canonify(col.tags.split(tags))
        m = note.model()
        m['tags'] = note.tags
        col.models.save(m)

        # Add the note
        col.addNote(note)


if __name__ == '__main__':

    # We provide a command-line interface with various options
    import argparse, glob

    parser = argparse.ArgumentParser()
    parser.add_argument("anki_home",
        help="Home of your Anki installation")
    parser.add_argument("-f", "--folder",
        help="Input folder where to search files", default="../save")
    parser.add_argument("--rank",
        help="Rank of the word to load", type=int)
    parser.add_argument("--from",
        help="Rank of the first word to load", type=int,
        default=0, dest="start")  # reserved word
    parser.add_argument("--to",
        help="Rank of the last word to load", type=int, default=100000,
        dest="end")  # to be consistent with start
    args = parser.parse_args()

    print("----------------------------------")
    print("Word Loader ----------------------")
    print("----------------------------------")
    print("Anki home: %s\n" % args.anki_home)

    # Load the anki collection
    cpath = os.path.join(args.anki_home, "collection.anki2")
    col = Collection(cpath, log=True)

    # Set the model
    modelBasic = col.models.byName('Word')
    deck = col.decks.byName("English")
    col.decks.select(deck['id'])
    col.decks.current()['mid'] = modelBasic['id']

    if args.rank:

        # Only one word to load
        print("Only rank %d to load" % args.rank)
        glob_pattern = "%d-*.json" % args.rank
        file_pattern = os.path.join(args.folder, glob_pattern)
        print("File pattern: " + file_pattern)
        for filepath in glob.iglob(file_pattern):
            load(col, filepath)

    else:

        # Iterate over input folder
        glob_pattern = '[1-9]*-*.json'

        file_pattern = os.path.join(args.folder, glob_pattern)
        for filepath in glob.iglob(file_pattern):
            filename = os.path.basename(filepath)
            rank = int(filename[:filename.index('-')])
            if rank >= args.start and rank < args.end:
                load(col, filepath)
            else:
                print("Skipped %s" % filename)


    # Save the changes to DB
    col.save()