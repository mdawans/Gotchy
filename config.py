import os
from dotenv import load_dotenv

# Charge le fichier .env qui est a cote de ce fichier (racine du projet).
_ICI = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_ICI, ".env"))


def _lire_secret(cle):
    """Lit une cle : d'abord dans .env (sur le PC), sinon dans les Secrets Streamlit (en ligne)."""
    valeur = os.getenv(cle)
    if valeur:
        return valeur
    try:
        import streamlit as st
        if cle in st.secrets:
            return st.secrets[cle]
    except Exception:
        pass
    return None


# La cle API Groq (l'IA).
GROQ_API_KEY = _lire_secret("GROQ_API_KEY")

# Le modele d'IA principal (gpt-oss-120b = grosse IA de raisonnement, la plus maligne sur Groq).
MODELE = "openai/gpt-oss-120b"

# Le modele VISION de Groq (qui sait REGARDER les images) pour verifier la generation d'images.
MODELE_VISION = "qwen/qwen3.6-27b"

# Le modele "agent" qui cherche sur internet TOUT SEUL quand il n'est pas sur (avec sources fiables).
MODELE_RECHERCHE = "groq/compound"

# Supabase (memoire cloud) : adresse + cle secrete.
SUPABASE_URL = _lire_secret("SUPABASE_URL")
SUPABASE_KEY = _lire_secret("SUPABASE_KEY")

# VirusTotal (module Securite : scan de fichiers par ~70 antivirus).
VIRUSTOTAL_KEY = _lire_secret("VIRUSTOTAL_KEY")

# Pseudo de l'ADMIN (Morgan) : seul lui voit le module Auto-amelioration.
ADMIN_PSEUDO = _lire_secret("ADMIN_PSEUDO")

# Auto-amelioration : le "codeur" (grosse IA de raisonnement, meilleure en code)
MODELE_CODE = "openai/gpt-oss-120b"
# ... et le "testeur" INDEPENDANT qui relit (une AUTRE IA = regard neuf, l'idee de Morgan)
MODELE_REVIEWER = "qwen/qwen3.6-27b"
