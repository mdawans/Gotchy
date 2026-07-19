import hashlib
import os
from supabase import create_client
import config

# Systeme de comptes avec mots de passe.
# REGLE D'OR : on ne stocke JAMAIS le mot de passe en clair dans la base !
# On stocke seulement son "hash" (une empreinte impossible a inverser) + un "sel" (grain de hasard).

_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def _hacher(mot_de_passe, sel_hex):
    """Transforme le mot de passe + le sel en une empreinte (hash) impossible a inverser.
    On utilise pbkdf2 (200 000 tours) : meme un hacker avec le hash ne retrouve pas le mot de passe."""
    sel = bytes.fromhex(sel_hex)
    empreinte = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), sel, 200000)
    return empreinte.hex()


def creer_compte(pseudo, mot_de_passe):
    """Cree un nouveau compte. Renvoie True si OK, False si le pseudo est deja pris."""
    deja = _client.table("users").select("pseudo").eq("pseudo", pseudo).execute()
    if deja.data:
        return False  # pseudo deja utilise

    sel_hex = os.urandom(16).hex()  # un grain de hasard unique pour ce compte
    hash_hex = _hacher(mot_de_passe, sel_hex)
    _client.table("users").insert(
        {"pseudo": pseudo, "hash": hash_hex, "sel": sel_hex}
    ).execute()
    return True


def verifier(pseudo, mot_de_passe):
    """Verifie le mot de passe. Renvoie True si c'est le bon, False sinon."""
    res = _client.table("users").select("hash, sel").eq("pseudo", pseudo).execute()
    if not res.data:
        return False  # ce pseudo n'existe pas
    compte = res.data[0]
    # On recalcule le hash avec le sel stocke, et on compare a celui de la base
    return _hacher(mot_de_passe, compte["sel"]) == compte["hash"]
