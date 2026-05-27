import os
import json

LANG_FILE = "languages.json"

def load_langs():
    if not os.path.exists(LANG_FILE):
        return {}
    with open(LANG_FILE, "r") as file:
        content = file.read().strip()
        if not content:
            return {}
        return json.loads(content)

def save_langs(id):
    with open(LANG_FILE, "w") as file:
        json.dump(id, file, indent=4)

def get_user_lang(id):
    langs = load_langs()
    return langs.get(str(id), "en") # Defaults to English
