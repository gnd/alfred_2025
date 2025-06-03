#!/usr/bin/env python
# pip3 install fire openai google-cloud-speech google-cloud-texttospeech google-cloud-translate pyaudio six pygame-ce screeninfo

from __future__ import division

import re
import os
import sys
import fire
import time
import socket
import threading
import subprocess
import configparser

from google.cloud import speech
from google.cloud import translate_v2 as translate

from stt_loop import processMicrophoneStream
from utils import pblue, pred, pgreen, pcyan, pyellow, concat, sanitize_translation, elapsed_time, normalize_text

from display_sender import DisplaySender
from display_manager import DisplayManager

# Load variables from config
settings = os.path.join(sys.path[0], 'config.ini')
config = configparser.ConfigParser()
config.read(settings)

# Assign config variables
TRANSCRIPTION_HOST = config.get('display', 'DISPLAY_HOST')
TRANSCRIPTION_PORT = int(config.get('display', 'DISPLAY_PORT'))
DEFAULT_PADDING_TOP = config.get('display', 'PADDING_TOP')
DEFAULT_PADDING_LEFT = config.get('display', 'PADDING_LEFT')
FONT_FILE = config.get('display', 'FONT')
MAX_WORDS = config.get('display', 'MAX_WORDS')
PAUSE_LENGTH = config.get('display', 'PAUSE_LENGTH')

# Define some language codes
SPEECH_LANG = "en-US"
TRANSLATE_TO = "cs"

class App:
    def __init__(self, speech_lang=SPEECH_LANG, reset_pause=int(PAUSE_LENGTH)):
        self.text_buffer = ""
        self.prev_text_buffer = ""
        self.text_buffer_window = ""

        self.max_words = int(MAX_WORDS)
        self.window_wiped_flag = False

        self.trans_buffer = ""
        self.trans_buffer_window = ""

        self.speech_lang = speech_lang

        self.display = DisplaySender(
            TRANSCRIPTION_HOST,
            TRANSCRIPTION_PORT,
            FONT_FILE
        )
        self.dm = DisplayManager(self, self.display, padding=(DEFAULT_PADDING_TOP, DEFAULT_PADDING_LEFT))

        self.last_sent_time = 0
        self.reset_pause = reset_pause

        # Translation client
        self.translate_client = translate.Client()

        
    def run(self):
        while True:
            if self.text_buffer == "":
                pcyan("Listening :)\n")

            # Blocks to process audio from the mic. This function continues
            # once the end of the utterance has been recognized.        
            text = processMicrophoneStream(
                self.speech_lang,
                self.handle_stt_response
            )
        
            # Print "complete utterance" as recognized by the STT service.
            pgreen(text)

            self.push_to_buffer(text)
            self.dm.display()
            # translate new text and display buffered translation
            self.display_translation_async()

    def handle_stt_response(self, responses):
        num_chars_printed = 0
        for response in responses:
            if not response.results:
                continue
            result = response.results[0]
            if not result.alternatives:
                continue
            transcript = result.alternatives[0].transcript
            overwrite_chars = " " * (num_chars_printed - len(transcript))

            time.sleep(0.001)

            if not result.is_final:
                pcyan("Result not final\n")
                sys.stdout.write(transcript + overwrite_chars + "\r")    
                self.dm.display_intermediate(transcript)

                sys.stdout.flush()
                num_chars_printed = len(transcript)
            else:
                pcyan("Result final\n")
                self.dm.display_intermediate(transcript)
                return (transcript + overwrite_chars + "\n")          

    def push_to_buffer(self, text):
        self.text_buffer = (concat(self.text_buffer, text)).strip()
        if len(self.text_buffer_window.split(" ")) > self.max_words:
            self.text_buffer_window = text.strip()
            self.window_wiped_flag = True
        else:
            self.text_buffer_window = (concat(self.text_buffer_window, text)).strip()

    def reset_buffer(self):
        self.prev_text_buffer = self.text_buffer
        self.text_buffer = ""
        self.text_buffer_window = ""

    def push_to_trans_buffer(self, text):
        self.trans_buffer = (concat(self.trans_buffer, text)).strip()

    def reset_trans_buffer(self):
        self.trans_buffer = ""
        self.trans_buffer_window = ""

    def translate(self):
        pyellow(f"Translating text: {self.text_buffer_window}")
        self.text_buffer_window,
        target_language = TRANSLATE_TO
        translation = self.translate_client.translate(
            self.text_buffer_window,
            target_language
        )["translatedText"]
        pyellow(f"Received: {translation}")
        translation = sanitize_translation(translation)
        pyellow(f"After sanitization: {translation}")

        self.trans_buffer_window = translation
        self.trans_buffer = translation
        self.dm.display_translation()

    def display_translation_async(self):
        t = threading.Thread(target=self.translate)
        t.start()


# Ai Calls
if __name__ == "__main__":
    App(speech_lang=SPEECH_LANG).run()
