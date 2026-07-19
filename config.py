import os
from dotenv import load_dotenv

# Charge le fichier .env qui est a cote de ce fichier (racine du projet KAIZEN).
# On calcule le chemin a partir de l'emplacement de config.py -> marche peu importe
# le dossier depuis lequel on lance le programme.
_ICI = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_ICI, ".env"))

# La cle API Groq : lue dans le .env (sur ton PC), JAMAIS ecrite en dur dans le code.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Sur Streamlit Cloud (en ligne), il n'y a pas de .env : la cle est dans les "Secrets".
if not GROQ_API_KEY:
    try:
        import streamlit as st
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass

# Le modele d'IA gratuit qu'on utilise (Llama 3.3 70B via Groq).
MODELE = "llama-3.3-70b-versatile"
