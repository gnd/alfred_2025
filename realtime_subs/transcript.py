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

from math import floor

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
MAX_CHARACTERS = config.get('display', 'MAX_CHARACTERS')
SUB_DURATION = config.get('display', 'SUB_DURATION')
SUB_REFRESH = config.get('display', 'SUB_REFRESH')
PAUSE_LENGTH = config.get('display', 'PAUSE_LENGTH')

# Define some language codes
ORIGIN_LANG = "en-US"
TARGET_LANG = "cs"

class App:
    def __init__(self, speech_lang=ORIGIN_LANG, reset_pause=int(PAUSE_LENGTH)):
        self.text_buffer = ""
        self.prev_text_buffer = ""
        self.text_buffer_window = ""
        self.trans_buffer = ""
        self.trans_buffer_window = ""
        self.window_wiped_flag = False
        self.max_characters = int(MAX_CHARACTERS)
        self.sub_duration = int(SUB_DURATION)
        self.sub_refresh = float(SUB_REFRESH)
        self.speech_lang = speech_lang

        # Display
        self.display = DisplaySender(TRANSCRIPTION_HOST, TRANSCRIPTION_PORT)
        self.dm = DisplayManager(self, self.display)
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
            processMicrophoneStream(self.speech_lang, self.handle_stt_response)

            # translate and display new utterances
            #self.display_translation_async()

    def handle_stt_response(self, responses):
        num_chars_printed = 0
        start = time.time()
        last_change = start
        for response in responses:
            time.sleep(0.001)
            if not response.results:
                continue
            result = response.results[0]
            if not result.alternatives:
                continue

            print(f"Alternatives: {result.alternatives[0]}")
            transcript = result.alternatives[0].transcript
            utterances = self.chop_utterance(self.translate_intermediate(transcript))
            #print(f"Utterances: {utterances}")
            ideal_utterance_number = int(floor((time.time() - start) / self.sub_duration))
            #print(f"Ideal utterance: {ideal_utterance_number}")
            if (len(utterances) > ideal_utterance_number):
                if (time.time() - last_change > self.sub_refresh):
                    last_change = time.time()
                    #print(f"Displaying: {utterances[ideal_utterance_number]} (ideal)")
                    self.dm.display_intermediate_translation(utterances[ideal_utterance_number])
            else:
                if (time.time() - last_change > self.sub_refresh):
                    last_change = time.time()
                    self.dm.display_intermediate_translation(utterances[-1])
                    #print(f"Displaying: {utterances[-1]} (intermediate)")

            if result.is_final:
                self.dm.display_intermediate_translation(utterances[-1])


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

    def chop_utterance(self, utterance):
        chopped_utterances = []
        timed_utterances = []
        while len(utterance) > self.max_characters:
            # search for the closest "." or ","" before max_characters
            best_location = 0
            for element in ['.', ',']:
                candidate_location = 0
                location = 0
                while location >= 0:
                    location = utterance.find(element, location+1)
                    if (location < self.max_characters and location != -1):
                        candidate_location = location
                if candidate_location > best_location:
                    best_location = candidate_location
            # best_location is where we chop utterance
            chopped_utterances.append(utterance[:best_location+1])
            utterance = utterance[best_location+1:].strip()
        chopped_utterances.append(utterance)
        return chopped_utterances

    def translate_intermediate(self, transcript):
        translation = self.translate_client.translate(transcript, TARGET_LANG)["translatedText"]
        translation = sanitize_translation(translation)
        return translation

# Ai Calls
if __name__ == "__main__":
    App(speech_lang=ORIGIN_LANG).run()
