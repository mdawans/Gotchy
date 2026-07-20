import urllib.parse
import base64
import re
import time
import requests
import config
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


def _telecharger_image(url, essais=5):
    """Recupere les octets de l'image depuis son URL Pollinations.
    Si le service repond 429 (trop de requetes), on attend et on reessaie (patience)."""
    rep = None
    for i in range(essais):
        rep = requests.get(url, timeout=90)
        if rep.status_code == 200:
            return rep.content
        if rep.status_code == 429:
            time.sleep(3 * (i + 1))  # on attend de plus en plus longtemps a chaque essai
            continue
        rep.raise_for_status()
    rep.raise_for_status()  # toujours pas bon apres tous les essais -> on leve l'erreur
    return rep.content


def analyser_image(image_bytes, question, mime="image/jpeg"):
    """Envoie une image + une question au modele VISION (Qwen) et renvoie sa reponse texte.
    Reutilisable : verification d'image, lecture d'un exercice de devoirs, etc."""
    b64 = base64.b64encode(image_bytes).decode()
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ],
        },
    ]
    reponse = demander_llm(messages, modele=config.MODELE_VISION)
    # Qwen "reflechit a voix haute" avec un bloc <think>...</think> -> on l'enleve pour une reponse propre
    propre = re.sub(r"<think>.*?</think>", "", reponse, flags=re.DOTALL).strip()
    return propre or reponse.strip()


def verifier_image(image_bytes, demande):
    """Un modele VISION regarde l'image et dit si elle correspond a la demande.
    Renvoie (est_bon: bool, avis: str). On juge la FIDELITE a la demande, pas le realisme."""
    question = (
        f"Regarde cette image. La demande etait : \"{demande}\". Est-ce que l'image "
        "correspond FIDELEMENT a la demande (on juge la fidelite a la demande, PAS le "
        "realisme du monde reel) ? Reponds en commencant STRICTEMENT par 'OUI' ou 'NON', "
        "puis si NON explique en UNE phrase ce qui cloche et doit etre corrige."
    )
    avis = analyser_image(image_bytes, question)
    est_bon = avis.strip().upper().startswith("OUI")
    return est_bon, avis


def _ameliorer_avec_retour(demande, prompt_actuel, retour):
    """Corrige le prompt en anglais en tenant compte de ce que le verificateur a signale."""
    messages = [
        {
            "role": "system",
            "content": (
                "Tu es prompt engineer pour un generateur d'images. Le prompt precedent n'a pas donne le "
                "bon resultat. Corrige-le (en anglais, detaille) pour regler le probleme signale, en gardant "
                "la demande d'origine. Reponds avec SEULEMENT le nouveau prompt, sans rien autour."
            ),
        },
        {
            "role": "user",
            "content": f"Demande d'origine: {demande}\nPrompt precedent: {prompt_actuel}\nProbleme a corriger: {retour}",
        },
    ]
    return demander_llm(messages).strip()


def _ajouter_qualite(prompt):
    """Ajoute des mots-clés de haute qualité au prompt s'ils ne sont pas déjà présents.
    Inclut également des termes spécifiques pour améliorer les petits détails (yeux, visage, etc.)."""
    mots_qualite = [
        "4k",
        "ultra detailed",
        "sharp focus",
        "highly detailed",
        "photo realistic",
        "studio lighting",
        "close-up",
        "eye detail",
        "portrait",
        "depth of field",
    ]
    prompt_lower = prompt.lower()
    for mot in mots_qualite:
        if mot not in prompt_lower:
            prompt = f"{prompt}, {mot}"
            # Met à jour la version en minuscules pour les vérifications suivantes
            prompt_lower = prompt.lower()
    # Nettoie les éventuelles virgules en trop
    return prompt.strip().strip(",")


def generer_intelligent(demande, max_essais=3):
    """Genere une image, la VERIFIE avec la vision, et CORRIGE jusqu'a max_essais fois.
    Renvoie (url_finale, historique) ou historique est la liste des essais."""
    historique = []
    prompt = ameliorer_description(demande)
    prompt = _ajouter_qualite(prompt)
    url = None
    for essai in range(1, max_essais + 1):
        url = image_depuis_texte(prompt, graine=essai)
        image_bytes = _telecharger_image(url)
        est_bon, avis = verifier_image(image_bytes, demande)
        historique.append({"essai": essai, "prompt": prompt, "url": url, "bon": est_bon, "avis": avis})
        if est_bon:
            break
        # sinon on corrige le prompt avec le retour et on retente
        prompt = _ameliorer_avec_retour(demande, prompt, avis)
        prompt = _ajouter_qualite(prompt)
    return url, historique
