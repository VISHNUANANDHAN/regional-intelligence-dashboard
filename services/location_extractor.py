import spacy

nlp = spacy.load("en_core_web_sm")


def extract_locations(text):

    doc = nlp(text)

    locations = []

    for ent in doc.ents:

        if ent.label_ in ["GPE", "LOC", "FAC", "ORG"]:
            locations.append({
                "name": ent.text,
                "label": ent.label_
            })

    return locations


def get_primary_location(text):

    locations = extract_locations(text)

    if locations:
        return locations[0]["name"]

    return None