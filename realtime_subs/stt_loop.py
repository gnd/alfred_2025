# stt_loop.py
import time, subprocess
from google.cloud import speech
try:
    from microphone_stream import MicrophoneStream
except:
    from .microphone_stream import MicrophoneStream

RATE  = 16_000
CHUNK = RATE // 10           # 100 ms
MAX_STREAM_SEC = 270         # restart well under Google’s 305 s hard limit


def _reconnect_chromium():
    """(Re)link Chromium’s MONO output to the new PyAudio inputs."""
    # tiny delay lets PipeWire expose the new ports
    time.sleep(0.25)

    links = (
        ("Chromium:output_MONO", "ALSA plug-in [python3.12]:input_FL"),
        ("Chromium:output_MONO", "ALSA plug-in [python3.12]:input_FR"),
    )
    for outp, inp in links:
        subprocess.run(["pw-link", outp, inp], check=False)
    print("[stt-loop] Reconnecting to Chromium ...")

def processMicrophoneStream(speech_lang: str, responses_cb=None):
    """Loops forever: open mic → stream to STT → restart just before 5 min."""
    client = speech.SpeechClient()

    cfg = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=speech_lang,
    )
    s_cfg = speech.StreamingRecognitionConfig(config=cfg, interim_results=True)

    while True:                         # self-restarting outer loop
        with MicrophoneStream(RATE, CHUNK) as stream:
            _reconnect_chromium()       # << relink *after* ports appear

            start = time.time()
            audio = stream.generator()

            def req_gen():
                for chunk in audio:
                    if time.time() - start > MAX_STREAM_SEC:
                        break           # cleanly finish this STT call
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)

            try:
                responses = client.streaming_recognize(s_cfg, req_gen())
                (responses_cb or print)(responses)
            except Exception as exc:
                print("[stt] streaming error:", exc)
                # fall through – outer while reopens everything


def main(speech_lang):
    processMicrophoneStream(speech_lang)


if __name__ == "__main__":
    main()
