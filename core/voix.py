import io
from gtts import gTTS
from core.llm import client

# Module Voix :
# - ECOUTER : Whisper (Groq) transforme la voix en texte (marche en francais).
# - PARLER : gTTS transforme le texte en audio mp3 francais (gratuit, sans cle).


def transcrire(audio_bytes, nom="audio.wav"):
    """Whisper (Groq) : transforme un enregistrement vocal en texte."""
    resultat = client.audio.transcriptions.create(
        file=(nom, audio_bytes),
        model="whisper-large-v3-turbo",
        language="fr",
    )
    return resultat.text.strip()


def parler(texte):
    """gTTS : transforme le texte en audio mp3 francais. Renvoie les octets du mp3."""
    tts = gTTS(text=texte, lang="fr")
    tampon = io.BytesIO()
    tts.write_to_fp(tampon)
    return tampon.getvalue()
