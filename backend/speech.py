from faster_whisper import WhisperModel
import os, tempfile

# Small/medium models also support many languages; change as needed
WHISPER_MODEL = os.getenv("WHISPER_MODEL","small")
DEVICE = "cpu"  # set to "cuda" if GPU available

_model = None
def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(WHISPER_MODEL, device=DEVICE, compute_type="int8")
    return _model

def transcribe(file_path):
    model=get_model()
    segments, info = model.transcribe(file_path, beam_size=1)
    text="".join([s.text for s in segments]).strip()
    return {"text": text, "language": info.language}
