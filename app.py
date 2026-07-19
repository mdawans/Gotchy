import streamlit as st
from streamlit_local_storage import LocalStorage
import config
from core.llm import demander_llm
from core import memory
from core import media
from core import security
from core import auth

st.set_page_config(page_title="Gotchy", page_icon="🤖", layout="wide")

# --- CONNEXION : chaque personne entre son pseudo pour avoir SON espace prive ---
# L'appareil se souvient du pseudo grace au "tiroir secret" du navigateur (localStorage).
stockage = LocalStorage()

if "pseudo" not in st.session_state:
    st.session_state.pseudo = None

# Tant qu'on n'est pas connecte dans cette session, on regarde si l'appareil se souvient d'un pseudo
if not st.session_state.pseudo:
    souvenir = stockage.getItem("gotchy_pseudo")
    if souvenir:
        st.session_state.pseudo = souvenir

# Si toujours personne -> on affiche la page de connexion (2 onglets : se connecter / creer un compte)
if not st.session_state.pseudo:
    st.title("🤖 Gotchy")
    st.subheader("Bienvenue ! 👋")
    onglet_connexion, onglet_creation = st.tabs(["🔑 Se connecter", "✨ Creer un compte"])

    # --- Onglet 1 : se connecter a un compte existant ---
    with onglet_connexion:
        nom = st.text_input("Pseudo", key="login_pseudo")
        mdp = st.text_input("Mot de passe", type="password", key="login_mdp")
        if st.button("Se connecter ➡️", type="primary"):
            if auth.verifier(nom.strip(), mdp):
                stockage.setItem("gotchy_pseudo", nom.strip())  # l'appareil s'en souvient
                st.session_state.pseudo = nom.strip()
                st.session_state.pop("messages", None)
                st.rerun()
            else:
                st.error("Pseudo ou mot de passe incorrect ! ❌")

    # --- Onglet 2 : creer un nouveau compte ---
    with onglet_creation:
        nouveau = st.text_input("Choisis un pseudo", key="new_pseudo")
        nouveau_mdp = st.text_input("Choisis un mot de passe", type="password", key="new_mdp")
        if st.button("Creer mon compte ✨"):
            if len(nouveau.strip()) < 2 or len(nouveau_mdp) < 4:
                st.warning("Pseudo (2 lettres min) et mot de passe (4 min) trop courts ! ✍️")
            elif auth.creer_compte(nouveau.strip(), nouveau_mdp):
                stockage.setItem("gotchy_pseudo", nouveau.strip())
                st.session_state.pseudo = nouveau.strip()
                st.session_state.pop("messages", None)
                st.rerun()
            else:
                st.error("Ce pseudo est deja pris, choisis-en un autre ! 🙅")

    st.stop()  # on arrete ici tant que personne n'est connecte

pseudo = st.session_state.pseudo

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

# --- Barre laterale : navigation entre les modules de Gotchy ---
with st.sidebar:
    st.title("🤖 Gotchy")
    st.caption(f"Connecte : **{pseudo}** 👤")
    st.markdown("### Modules")
    module = st.radio(
        "Choisis un module :",
        ["💬 Copilote", "🎨 Studio Media", "🛡️ Securite"],
        label_visibility="collapsed",
    )
    st.markdown("🖥️ Controle Systeme *(bientot)*")

    st.divider()
    if st.button("🗑️ Nouvelle conversation"):
        memory.effacer(pseudo)
        st.session_state.messages = []
        st.rerun()
    if st.button("🚪 Changer d'utilisateur"):
        stockage.deleteItem("gotchy_pseudo")  # l'appareil oublie ce pseudo
        st.session_state.pseudo = None
        st.session_state.pop("messages", None)
        st.rerun()


# =====================  MODULE 1 : LE COPILOTE (chat)  =====================
def page_copilote():
    st.header("💬 Copilote")

    # Memoire CLOUD (Supabase) : on charge SEULEMENT l'historique de ce pseudo
    if "messages" not in st.session_state:
        st.session_state.messages = memory.charger(pseudo)
    messages = st.session_state.messages

    # Afficher tout l'historique (meme celui d'avant, et depuis n'importe quel appareil !)
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Zone de saisie en bas
    if question := st.chat_input("Pose ta question a Gotchy..."):
        # 1) On ajoute et affiche le message de Morgan (+ on le sauve dans le cloud)
        messages.append({"role": "user", "content": question})
        memory.ajouter_message(pseudo, "user", question)
        with st.chat_message("user"):
            st.markdown(question)

        # 2) On demande a l'IA (systeme + 20 derniers messages pour ne pas surcharger)
        with st.chat_message("assistant"):
            with st.spinner("Gotchy reflechit..."):
                reponse = demander_llm([SYSTEME] + messages[-20:])
            st.markdown(reponse)
        messages.append({"role": "assistant", "content": reponse})

        # 3) On sauve la reponse dans le cloud (marquee au pseudo de la personne)
        memory.ajouter_message(pseudo, "assistant", reponse)


# =====================  MODULE 2 : LE STUDIO MEDIA (images)  =====================
def page_studio():
    st.header("🎨 Studio Media")
    st.caption("Decris une image, Gotchy la dessine pour toi ! (gratuit, via Pollinations + Flux)")

    description = st.text_input(
        "Ta description :",
        placeholder="une girafe avec une tete de mouton",
    )
    ameliorer = st.checkbox(
        "🧠 Ameliorer ma description avec l'IA (recommande)", value=True
    )

    if st.button("✨ Generer l'image", type="primary"):
        if description.strip() == "":
            st.warning("Ecris d'abord une description ! ✍️")
        else:
            # On change la "graine" a chaque clic -> images differentes si tu regeneres
            st.session_state.graine = st.session_state.get("graine", 0) + 1

            texte_final = description
            if ameliorer:
                with st.spinner("Gotchy reflechit a ta description... 🧠"):
                    texte_final = media.ameliorer_description(description)
                with st.expander("🔎 Voir la description que Gotchy a creee (en anglais)"):
                    st.write(texte_final)

            with st.spinner("Gotchy dessine... 🖌️"):
                url = media.image_depuis_texte(texte_final, graine=st.session_state.graine)
                st.image(url, caption=description, use_container_width=True)
            st.success("Voila ton image ! 🎉 (reclique sur Generer pour une autre version)")


# =====================  MODULE 3 : LA SECURITE (antivirus)  =====================
def page_securite():
    st.header("🛡️ Securite")
    st.caption("Depose un fichier suspect, Gotchy le fait scanner par ~70 antivirus (VirusTotal).")

    if not config.VIRUSTOTAL_KEY:
        st.error("Il manque la cle VIRUSTOTAL_KEY dans le .env ! 🔑")
        return

    fichier = st.file_uploader("Choisis un fichier a scanner :")

    if fichier is not None and st.button("🔍 Scanner le fichier", type="primary"):
        with st.spinner("Gotchy envoie le fichier a ~70 antivirus... 🦠"):
            stats = security.scanner_fichier(fichier.getvalue(), fichier.name)

        if stats is None:
            st.warning("L'analyse a pris trop de temps, reessaie dans un instant. ⏳")
            return

        dangereux = stats.get("malicious", 0)
        suspect = stats.get("suspicious", 0)
        total = sum(stats.values())

        if dangereux == 0 and suspect == 0:
            st.success(f"✅ Fichier PROPRE ! Aucun des {total} antivirus ne l'a trouve dangereux.")
        else:
            st.error(
                f"⚠️ DANGER ! {dangereux} antivirus le trouvent MALVEILLANT "
                f"et {suspect} le trouvent suspect (sur {total}). N'OUVRE PAS ce fichier ! 🚫"
            )
        st.write("Detail :", stats)


# --- On affiche la page choisie dans le menu ---
if module == "💬 Copilote":
    page_copilote()
elif module == "🎨 Studio Media":
    page_studio()
else:
    page_securite()
