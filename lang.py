import os
import json

LANG_FILE = "./locale/languages.json"


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
    return langs.get(str(id), "en")  # Defaults to English


LOCALES_DIR = "locale"
TRANSLATIONS = {}

for filename in os.listdir(LOCALES_DIR):
    if filename.endswith(".json"):
        lang_code = filename.split(".")[0]
        with open(os.path.join(LOCALES_DIR, filename), "r", encoding="utf-8") as f:
            TRANSLATIONS[lang_code] = json.load(f)


def get_msg(lang: str, key: str, default_lang: str = "en") -> str:
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS.get(default_lang))

    try:
        keys = key.split(".")
        result = lang_dict
        for k in keys:
            result = result[k]
        return result
    except (KeyError, TypeError):
        return f"Missing translation: {key}"
