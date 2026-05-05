import os
import json

LANG_FILE = "languages.json"

def load_langs():
    if not os.path.exists(LANG_FILE):
        return {}
    with open(LANG_FILE, "r") as f:
        content = f.read().strip()
        if not content:
            return {}
        return json.loads(content)
def save_langs(data):
    with open(LANG_FILE, "w") as f:
        json.dump(data, f, indent=4)
def get_user_lang(user_id):
    langs = load_langs()
    return langs.get(str(user_id), "en")

