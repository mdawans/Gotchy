import os
import re
import difflib
import config
from core.llm import demander_llm

# Auto-amelioration : Gotchy PROPOSE des changements sur son propre code.
# SECURITE : liste blanche stricte, verif syntaxe, 2e IA testeuse, et RIEN n'est ecrit sans que
# l'humain clique "Appliquer". Tout est dans git = annulable.

_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# LISTE BLANCHE : SEULS ces fichiers peuvent etre lus/modifies. JAMAIS .env, config secrets, etc.
FICHIERS_AUTORISES = [
    "app.py",
    "core/llm.py",
    "core/memory.py",
    "core/media.py",
    "core/security.py",
    "core/auth.py",
    "core/evolution.py",
]


def lire(nom):
    """Lit un fichier autorise."""
    if nom not in FICHIERS_AUTORISES:
        raise ValueError("Fichier non autorise !")
    with open(os.path.join(_RACINE, nom), encoding="utf-8") as f:
        return f.read()


def _nettoyer(code):
    """Enleve d'eventuelles balises markdown ``` que l'IA pourrait ajouter autour du code."""
    code = code.strip()
    if code.startswith("```"):
        lignes = code.split("\n")[1:]  # enleve la 1ere ligne ```python
        if lignes and lignes[-1].strip() == "```":
            lignes = lignes[:-1]
        code = "\n".join(lignes)
    return code.strip() + "\n"


def _sans_reflexion(texte):
    """Enleve le bloc <think>...</think> que certaines IA (comme qwen) ajoutent avant leur reponse."""
    return re.sub(r"<think>.*?</think>", "", texte, flags=re.DOTALL).strip()


def proposer(nom, demande):
    """Gotchy propose une nouvelle version du fichier. Renvoie (code_avant, code_apres)."""
    avant = lire(nom)
    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un dev Python expert qui ameliore l'app Gotchy (Streamlit). On te donne le contenu "
                "ACTUEL d'un fichier + une demande. Renvoie UNIQUEMENT le contenu COMPLET du nouveau fichier "
                "Python, sans aucun texte autour et SANS balises markdown. Garde le meme style, ne casse RIEN "
                "d'existant, applique seulement la demande. Ne touche JAMAIS aux cles/secrets/.env."
            ),
        },
        {
            "role": "user",
            "content": f"FICHIER: {nom}\n\n--- CODE ACTUEL ---\n{avant}\n\n--- DEMANDE ---\n{demande}",
        },
    ]
    apres = _nettoyer(demander_llm(messages, modele=config.MODELE_CODE))
    return avant, apres


def diff_texte(avant, apres):
    """Renvoie les changements ligne par ligne (format diff)."""
    lignes = difflib.unified_diff(
        avant.splitlines(), apres.splitlines(), fromfile="avant", tofile="apres", lineterm=""
    )
    return "\n".join(lignes)


def verifier_syntaxe(code):
    """Verifie que le nouveau code Python est valide. Renvoie (True, None) ou (False, message)."""
    try:
        compile(code, "<proposition>", "exec")
        return True, None
    except SyntaxError as e:
        return False, f"Erreur de syntaxe ligne {e.lineno} : {e.msg}"


def reviewer(nom, avant, apres, demande):
    """Le 2e IA 'testeur' verifie la proposition (l'idee de Morgan)."""
    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un reviewer de code Python STRICT et paranoiaque (le 'testeur' de Gotchy). On te donne "
                "l'ancien et le nouveau code d'un fichier, plus la demande. Verifie : est-ce que ca repond a la "
                "demande ? est-ce que ca casse un truc existant ? y a-t-il un bug ? un comportement DANGEREUX "
                "(supprimer des fichiers, exposer des cles, boucle infinie, acces reseau louche) ? "
                "Commence ta reponse par 'VERDICT: OK' ou 'VERDICT: DANGER', puis explique en francais simple. "
                "Dans le moindre doute -> DANGER."
            ),
        },
        {
            "role": "user",
            "content": f"DEMANDE: {demande}\n\n--- AVANT ---\n{avant}\n\n--- APRES ---\n{apres}",
        },
    ]
    return _sans_reflexion(demander_llm(messages, modele=config.MODELE_REVIEWER))


def expliquer(nom, avant, apres, demande):
    """Explique en francais TRES SIMPLE ce que le changement fait (pour Morgan, debutant)."""
    messages = [
        {
            "role": "system",
            "content": (
                "Tu expliques a un debutant de 13 ans, en francais TRES simple, ce qu'un changement de code "
                "va faire. NE montre PAS le code, pas de jargon. Dis en 2 a 4 phrases : ce que ca change "
                "concretement dans l'app, pourquoi c'est utile, et si ca risque de casser autre chose. "
                "Sois clair et rassurant."
            ),
        },
        {
            "role": "user",
            "content": f"Fichier: {nom}\nDemande: {demande}\n\n--- AVANT ---\n{avant}\n\n--- APRES ---\n{apres}",
        },
    ]
    return demander_llm(messages).strip()


def appliquer(nom, nouveau_code):
    """Ecrit le nouveau code SUR le fichier. Appele UNIQUEMENT apres validation humaine."""
    if nom not in FICHIERS_AUTORISES:
        raise ValueError("Fichier non autorise !")
    ok, err = verifier_syntaxe(nouveau_code)
    if not ok:
        raise ValueError(f"Refuse : {err}")
    with open(os.path.join(_RACINE, nom), "w", encoding="utf-8") as f:
        f.write(nouveau_code)
