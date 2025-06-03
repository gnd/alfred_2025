import os
import re
import six
from termcolor import cprint, colored

# Logging functions
pblue = lambda text: cprint(text, "blue")
pred = lambda text: cprint(text, "red")
pgreen = lambda text: cprint(text, "green")
pyellow = lambda text: cprint(text, "yellow")
pcyan = lambda text: cprint(text, "cyan")
pmagenta = lambda text: cprint(text, "magenta")

def elapsed_time(start, end):
    return f'{"{:.3f}".format(end - start)} seconds'

def cut_to_sentence_end(text):
    """Cuts off unfinished sentence."""

    endIdx = max(text.rfind("."), text.rfind("?"), text.rfind("!"))
    endIdx = endIdx if endIdx > -1 else 0
    
    return text[0: endIdx + 1]

def normalize_text(text):
    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")

    text = text.lstrip(". ")               # remove leftover dots and spaces from the beggining
    text = text.replace("&quot;","")       # remove "&quot;"
    text = text.strip()
    return text

def sanitize_translation(text):
    t = text.replace("&#39;", "'")
    t = text.replace("“", "")
    t = text.replace("”", "")
    t = text.replace("’", "")
    t = text.replace("‘", "")
    t = text.replace("\"", "")
    if len(t) > 2:
        t = t[0].upper() + t[1:] # Capitalize; `capitalize` sucks
    elif len(t) == 1:
        t = t.upper()
    return t

def concat(a, b):
    a = a.strip()
    b = b.strip()
    if len(b) > 0:
        if b[0] == "." or b[0] == "?" or b[0] == "!" or b[0] == ",":
            return a + b
        else:
            return a + " " + b
    return a

SPEECH_CODE_TO_LANG_CODE = {
    "cs-CZ": "cs",
    "en-US": "en",
    "fr-FR": "fr",
    "de-DE": "de",
    "ru-RU": "ru",
    "cmn-CN": "zh-CN",
    "sk-SK": "sk"
}

class SpeechCode:
    def __init__(self):
        self.CZECH = "cs-CZ"
        self.ENGLISH = "en-US"
        self.FRENCH = "fr-FR"
        self.GERMAN = "de-DE"
        self.RUSSIAN = "ru-RU"
        self.CHINESE = "cmn-CN"
        self.SLOVAK = "sk-SK"

class LangCode:
    def __init__(self):
        self.CZECH = "cs"
        self.ENGLISH = "en"
        self.FRENCH = "fr"
        self.GERMAN = "de"
        self.RUSSIAN = "ru"
        self.CHINESE = "zh-CN"
        self.SLOVAK = "sk"

def getLangCode(speech_code):
    return SPEECH_CODE_TO_LANG_CODE.get(speech_code)