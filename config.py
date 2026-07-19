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

# Le modele d'IA gratuit qu'on utilise (Llama 3.3 70B via Groq).
MODELE = "llama-3.3-70b-versatile"

# Supabase (memoire cloud) : adresse + cle secrete.
SUPABASE_URL = _lire_secret("SUPABASE_URL")
SUPABASE_KEY = _lire_secret("SUPABASE_KEY")
