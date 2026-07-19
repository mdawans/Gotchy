import streamlit as st
from core.llm import demander_llm
from core import memory

st.set_page_config(page_title="Gotchy", page_icon="🤖", layout="wide")

# --- Le "caractere" de Gotchy (message systeme, invisible pour l'utilisateur) ---
SYSTEME = {
    "role": "system",
    "content": (
        "Tu es Gotchy, l'assistant personnel UNIVERSEL de Morgan (13 ans, francais, tres motive). "
        "Tu l'aides sur TOUT dans sa vie : ses devoirs et questions d'ecole (maths, francais, "
        "sciences, histoire...), ses idees, sa creativite, les demarches du quotidien, la culture "
        "generale, et AUSSI le code et ses jeux (Godot, Roblox) quand il en parle. "
        "Tu n'es PAS limite a l'informatique : tu es un assistant a tout faire. "
        "Reponds toujours en francais, de facon claire, simple et encourageante. "
        "Tu te souviens des conversations precedentes (au-dessus) : NE re-explique PAS en detail "
        "ce que tu as deja explique a Morgan, reference-le juste brievement (anti-radotage)."
    ),
}

# --- Barre laterale : les modules de Gotchy ---
with st.sidebar:
    st.title("🤖 Gotchy")
    st.caption("Ton assistant perso — par D3toxx")
    st.markdown("### Modules")
    st.markdown("💬 **Copilote** ✅")
    st.markdown("🎨 Studio Media *(bientot)*")
    st.markdown("🛡️ Securite *(bientot)*")
    st.markdown("🖥️ Controle Systeme *(bientot)*")

    st.divider()
    if st.button("🗑️ Nouvelle conversation"):
        memory.effacer()
        st.session_state.memoire = {"messages": []}
        st.rerun()

st.header("💬 Copilote")

# --- Memoire : on charge les conversations passees (une fois par session) ---
if "memoire" not in st.session_state:
    st.session_state.memoire = memory.charger()
messages = st.session_state.memoire["messages"]

# Afficher tout l'historique (meme celui d'avant, grace a la memoire !)
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Zone de saisie en bas ---
if question := st.chat_input("Pose ta question a Gotchy..."):
    # 1) On ajoute et affiche le message de Morgan
    messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # 2) On demande a l'IA (systeme + 20 derniers messages pour ne pas surcharger)
    with st.chat_message("assistant"):
        with st.spinner("Gotchy reflechit..."):
            reponse = demander_llm([SYSTEME] + messages[-20:])
        st.markdown(reponse)
    messages.append({"role": "assistant", "content": reponse})

    # 3) On SAUVEGARDE tout -> Gotchy s'en souviendra meme apres fermeture ! 💾
    memory.sauver(st.session_state.memoire)
