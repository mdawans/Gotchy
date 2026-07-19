import json
import os

# Le fichier de memoire est dans KAIZEN/data/memory.json
_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DOSSIER = os.path.join(_RACINE, "data")
_FICHIER = os.path.join(_DOSSIER, "memory.json")


def charger():
    """Charge la memoire (les messages passes). Renvoie un dict {'messages': [...]}."""
    if os.path.exists(_FICHIER):
        try:
            with open(_FICHIER, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"messages": []}


def sauver(memoire):
    """Ecrit la memoire dans data/memory.json (cree le dossier si besoin)."""
    os.makedirs(_DOSSIER, exist_ok=True)
    with open(_FICHIER, "w", encoding="utf-8") as f:
        json.dump(memoire, f, ensure_ascii=False, indent=2)


def effacer():
    """Vide la memoire (pour repartir sur une nouvelle conversation)."""
    sauver({"messages": []})
