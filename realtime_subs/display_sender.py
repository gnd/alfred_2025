import socket
try:
    from utils import pred
except:
    from .utils import pred

class DisplaySender:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def _send(self, msg):
        sock = socket.socket()
        try:
            sock.connect((self.host, self.port))
            sock.send(msg.encode())
        except:
            pred(f"Cannot connect to {self.host}:{self.port}")
        finally:
            sock.close()

    def send(
        self,
        original="",
        translation=None,
        utterance=None,
        fill=True):
        key_vals = []
        # Serialize all parameters
        if original:
            original = _sanitize_text(original)
            key_vals.append(_get_key_val("original", original))
        if translation:
            translation = _sanitize_text(translation)
            key_vals.append(_get_key_val("translation", translation))
        if utterance:
            utterance = _sanitize_text(utterance)
            key_vals.append(_get_key_val("utterance", utterance))
        if fill:
            key_vals.append(_get_key_val("fill", fill))
        
        msg = _join_key_vals(key_vals)
        
        self._send(msg)
        return

def _get_key_val(key, val):
    return key + "=" + str(val)

def _join_key_vals(key_vals):
    return ":".join(key_vals)

def _sanitize_text(text):
    text = text.replace(":", "").replace("=", "")
    return text