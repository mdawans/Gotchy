import urllib.parse
from core.llm import demander_llm

# Studio Media : generation d'images GRATUITE avec Pollinations.ai (aucune cle necessaire !).
# Le principe : on transforme la description en une adresse web speciale qui renvoie une image.

_BASE = "https://image.pollinations.ai/prompt/"


def ameliorer_description(description):
    """Utilise le cerveau de Groq pour transformer la phrase de Morgan (souvent en francais,
    parfois bizarre) en une VRAIE description anglaise, precise et detaillee, que l'IA d'images
    comprend beaucoup mieux. On garde bien TOUS les details voulus (meme les plus fous)."""
    consigne = [
        {
            "role": "system",
            "content": (
                "You are a prompt engineer for an AI image generator. "
                "Turn the user's idea (often in French, sometimes strange or surreal) into ONE "
                "detailed English image prompt. Keep EVERY detail the user asked for, even weird "
                "combinations (describe them explicitly so the image AI cannot ignore them). "
                "Add style, lighting and quality words. Answer with ONLY the prompt, no quotes, "
                "no explanation."
            ),
        },
        {"role": "user", "content": description},
    ]
    return demander_llm(consigne).strip()


def image_depuis_texte(description, largeur=1024, hauteur=1024, graine=None):
    """Transforme une description (texte) en URL d'image Pollinations.

    On utilise le modele 'flux' (le plus fort) et on 'encode' la description pour qu'elle rentre
    proprement dans une adresse web (espaces, accents... deviennent du code que le web comprend).
    La 'graine' (seed) change l'image : meme texte + graine differente = image differente.
    """
    texte_propre = urllib.parse.quote(description)
    url = f"{_BASE}{texte_propre}?width={largeur}&height={hauteur}&nologo=true&model=flux"
    if graine is not None:
        url += f"&seed={graine}"
    return url
