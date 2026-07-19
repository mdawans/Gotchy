import streamlit as st
from core.llm import demander_llm

st.set_page_config(page_title="KAIZEN", page_icon="🤖", layout="wide")

# --- Le "caractere" de KAIZEN (message systeme, invisible pour l'utilisateur) ---
SYSTEME = {
    "role": "system",
    "content": (
        "Tu es KAIZEN, l'assistant personnel UNIVERSEL de Morgan (13 ans, francais, tres motive). "
        "Tu l'aides sur TOUT dans sa vie : ses devoirs et questions d'ecole (maths, francais, "
        "sciences, histoire...), ses idees, sa creativite, les demarches du quotidien, la culture "
        "generale, et AUSSI le code et ses jeux (Godot, Roblox) quand il en parle. "
        "Tu n'es PAS limite a l'informatique : tu es un assistant a tout faire. "
        "Reponds toujours en francais, de facon claire, simple et encourageante."
    ),
}

# --- Barre laterale : les modules de KAIZEN ---
with st.sidebar:
    st.title("🤖 KAIZEN")
    st.caption("Ton assistant perso")
    st.markdown("### Modules")
    st.markdown("💬 **Copilote** ✅")
    st.markdown("🎨 Studio Media *(bientot)*")
    st.markdown("🛡️ Securite *(bientot)*")
    st.markdown("🖥️ Controle Systeme *(bientot)*")

st.header("💬 Copilote")

# --- Historique de la conversation (garde en memoire pendant la session) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher tout l'historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Zone de saisie en bas ---
if question := st.chat_input("Pose ta question a KAIZEN..."):
    # 1) On ajoute et affiche le message de Morgan
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # 2) On demande a l'IA et on affiche sa reponse
    with st.chat_message("assistant"):
        with st.spinner("KAIZEN reflechit..."):
            reponse = demander_llm([SYSTEME] + st.session_state.messages)
        st.markdown(reponse)
    st.session_state.messages.append({"role": "assistant", "content": reponse})
