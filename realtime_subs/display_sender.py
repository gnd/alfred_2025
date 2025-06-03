import socket

from utils import pblue, pred, pgreen, pcyan, pmagenta, pyellow

class DisplaySender:
    def __init__(self, host, port, font=None, fill_color=None):
        self.host = host
        self.port = port
        self.font = font
        self.fill_color = fill_color

    def _send(self, msg):
        sock = socket.socket()
        try:
            pgreen("connecting ..")
            sock.connect((self.host, self.port))
            pgreen("connected ..")
            pgreen("encoding message ..")
            sock.send(msg.encode())
        except:
            pred(f"Cannot connect to {self.host}:{self.port}")
        finally:
            sock.close()

    def send(
        self,
        original="",
        translation=None,
        fill=True,
        align=None,
        padding_left=None,
        padding_top=None,
        font=None):
        key_vals = []
        # Serialize all parameters
        if original:
            original = _sanitize_text(original)
            key_vals.append(_get_key_val("original", original))
        if translation:
            translation = _sanitize_text(translation)
            key_vals.append(_get_key_val("translation", translation))
        if fill:
            key_vals.append(_get_key_val("fill", fill))
        if align:
            key_vals.append(_get_key_val("align", align))
        if padding_top:
            key_vals.append(_get_key_val("padding_top", padding_top))
        if padding_left:
            key_vals.append(_get_key_val("padding_left", padding_left))
        if font or self.font:
            f = font if font else self.font
            key_vals.append(_get_key_val("font", f))
        
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