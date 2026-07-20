import random
import streamlit as st
from streamlit_local_storage import LocalStorage
import config
from core.llm import demander_llm
from core import memory
from core import media
from core import security
from core import auth
from core import evolution
from core import recherche

st.set_page_config(page_title="Gotchy", page_icon="🤖", layout="wide")

# Petits emojis sympa ajoutes UNIQUEMENT aux reponses du chat (pas ailleurs).
EMOJIS = ["😊", "🚀", "👍", "💡", "✨", "🤖", "🎉", "🧠", "📚", "🌟"]

# Separateur invisible pour ranger les sources web dans un bouton depliable (comme Gemini).
SEP_SOURCES = "\n\n[[SOURCES]]\n"


def afficher_message(contenu):
    """Affiche un message. S'il contient des sources web, les cache dans un bouton depliable."""
    if SEP_SOURCES in contenu:
        texte, liens = contenu.split(SEP_SOURCES, 1)
        st.markdown(texte)
        with st.expander("🔗 Sources"):
            st.markdown(liens)
    else:
        st.markdown(contenu)

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
        "ce que tu as deja explique a Morgan, reference-le juste brievement (anti-radotage). "
        "Reponds de facon CONCISE et courte, qui donne envie de lire."
    ),
}

# --- Barre laterale : navigation entre les modules de Gotchy ---
with st.sidebar:
    st.title("🤖 Gotchy")
    st.caption(f"Connecte : **{pseudo}** 👤")
    st.markdown("### Modules")
    # Les modules de base pour tout le monde
    modules_dispo = ["💬 Copilote", "🎨 Studio Media", "🛡️ Securite"]
    # Le module Auto-amelioration : reserve a l'ADMIN uniquement
    est_admin = config.ADMIN_PSEUDO and pseudo == config.ADMIN_PSEUDO
    if est_admin:
        modules_dispo.append("🧠 Evolution")

    module = st.radio(
        "Choisis un module :",
        modules_dispo,
        label_visibility="collapsed",
    )
    if not est_admin:
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
            afficher_message(msg["content"])

    # Zone de saisie en bas (avec bouton 📎 pour joindre une image / prendre une photo)
    saisie = st.chat_input(
        "Pose ta question a Gotchy...",
        accept_file=True,
        file_type=["png", "jpg", "jpeg"],
    )
    if saisie:
        texte = saisie.text or ""
        image = saisie.files[0] if saisie.files else None

        # 1) Message de Morgan (affichage + memoire ; si image, on le note dans l'historique)
        if image and texte:
            contenu = f"{texte}  🖼️"
        elif image:
            contenu = "🖼️ (image envoyee)"
        else:
            contenu = texte
        messages.append({"role": "user", "content": contenu})
        memory.ajouter_message(pseudo, "user", contenu)
        with st.chat_message("user"):
            st.markdown(contenu)
            if image:
                st.image(image)

        # 2) Reponse : si une image est jointe -> VISION (Qwen), sinon -> chat texte
        with st.chat_message("assistant"):
            sources_web = []
            with st.spinner("Gotchy reflechit..."):
                if image:
                    question = texte or (
                        "Analyse cette image. Si c'est un exercice, resous-le et explique etape "
                        "par etape en francais simple. Sinon, decris-la clairement."
                    )
                    reponse = media.analyser_image(image.getvalue(), question, image.type)
                else:
                    # D'abord Gotchy se demande s'il a besoin de chercher sur le web (info recente ?)
                    if recherche.besoin_de_chercher(texte):
                        reponse, sources_web = recherche.repondre_avec_web(texte)  # cherche
                    else:
                        reponse = demander_llm([SYSTEME] + messages[-20:])  # repond de memoire
                    reponse = f"{reponse} {random.choice(EMOJIS)}"  # emoji sympa (chat texte)

            # Si des sources web -> on les range dans le bouton depliable (separateur invisible)
            if sources_web:
                liens = "\n".join(
                    f"- [{r.get('title', '(lien)')}]"
                    f"({r.get('href') or r.get('link') or r.get('url')})"
                    for r in sources_web
                    if (r.get("href") or r.get("link") or r.get("url"))
                )
                contenu = f"{reponse}{SEP_SOURCES}{liens}"
            else:
                contenu = reponse

            afficher_message(contenu)

        messages.append({"role": "assistant", "content": contenu})
        memory.ajouter_message(pseudo, "assistant", contenu)


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
    verifier = st.checkbox(
        "🔁 Verifier et corriger l'image (Gotchy la REGARDE et recommence si besoin — plus lent)",
        value=False,
    )

    if st.button("✨ Generer l'image", type="primary"):
        if description.strip() == "":
            st.warning("Ecris d'abord une description ! ✍️")

        elif verifier:
            # MODE INTELLIGENT : genere -> regarde -> corrige (boucle vision)
            with st.spinner("Gotchy dessine, regarde, et corrige si besoin... 👁️🖌️"):
                url, historique = media.generer_intelligent(description)
            st.image(url, caption=description, use_container_width=True)
            dernier = historique[-1]
            if dernier["bon"]:
                st.success(f"✅ Validee par la vision en {len(historique)} essai(s) ! 🎉")
            else:
                st.warning(f"⚠️ Meilleure version apres {len(historique)} essais (pas parfaite).")
            with st.expander("👁️ Voir ce que Gotchy a verifie a chaque essai"):
                for h in historique:
                    st.markdown(f"**Essai {h['essai']}** — {'✅ OK' if h['bon'] else '❌ a corriger'}")
                    st.caption(h["avis"])

        else:
            # MODE SIMPLE : une seule generation
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


# =====================  MODULE 4 : AUTO-AMELIORATION (admin only)  =====================
def page_evolution():
    st.header("🧠 Auto-amelioration")
    st.caption("Gotchy propose d'ameliorer son PROPRE code. Toi, l'admin, tu valides. (a utiliser en LOCAL)")

    # Double verrou : meme si on arrive ici, on re-verifie que c'est bien l'admin
    if not (config.ADMIN_PSEUDO and pseudo == config.ADMIN_PSEUDO):
        st.error("Reserve a l'admin ! 🔒")
        return

    st.info(
        "🔒 Securite : Gotchy PROPOSE seulement. Un 2e IA testeur verifie, la syntaxe est checkee, "
        "et RIEN n'est applique sans ton bouton. Tout est dans git = annulable."
    )

    nom = st.selectbox("Quel fichier ameliorer ?", evolution.FICHIERS_AUTORISES)
    demande = st.text_area(
        "Qu'est-ce que tu veux ameliorer ?",
        placeholder="ex: rends les reponses du Copilote plus droles, ou ameliore la generation d'images",
    )

    if st.button("🤖 Proposer une amelioration", type="primary"):
        if demande.strip() == "":
            st.warning("Ecris d'abord ce que tu veux ameliorer ! ✍️")
        else:
            with st.spinner("Gotchy reflechit a une amelioration..."):
                avant, apres = evolution.proposer(nom, demande)
            with st.spinner("Gotchy explique le changement en francais..."):
                explication = evolution.expliquer(nom, avant, apres, demande)
            with st.spinner("Le testeur IA verifie la proposition..."):
                avis = evolution.reviewer(nom, avant, apres, demande)
            ok_syntaxe, err = evolution.verifier_syntaxe(apres)
            st.session_state.propo = {
                "nom": nom, "avant": avant, "apres": apres,
                "explication": explication,
                "avis": avis, "ok_syntaxe": ok_syntaxe, "err": err,
            }

    # Afficher la proposition en cours (si elle existe)
    propo = st.session_state.get("propo")
    if propo:
        st.divider()
        st.subheader(f"Proposition pour `{propo['nom']}`")

        # 0) L'explication en francais simple (pour comprendre SANS lire le code)
        st.info(f"📖 **En clair :** {propo['explication']}")

        # 1) Verdict du testeur IA
        if "VERDICT: OK" in propo["avis"].upper():
            st.success("🕵️ Testeur IA : OK")
        else:
            st.error("🕵️ Testeur IA : ATTENTION !")
        st.write(propo["avis"])

        # 2) Check syntaxe
        if propo["ok_syntaxe"]:
            st.success("✅ Syntaxe Python valide")
        else:
            st.error(f"❌ {propo['err']} — a NE PAS appliquer")

        # 3) Voir les changements
        with st.expander("🔍 Voir les changements (diff)"):
            st.code(evolution.diff_texte(propo["avant"], propo["apres"]), language="diff")
        with st.expander("📄 Voir le nouveau fichier complet"):
            st.code(propo["apres"], language="python")

        # 4) Decision humaine
        col1, col2 = st.columns(2)
        with col1:
            if propo["ok_syntaxe"]:
                if st.button("✅ Appliquer", type="primary"):
                    evolution.appliquer(propo["nom"], propo["apres"])
                    st.session_state.pop("propo")
                    st.success(
                        f"{propo['nom']} mis a jour ! Verifie que l'app marche, "
                        "puis fais un git commit si tout est bon. 🎉"
                    )
                    st.rerun()
            else:
                st.button("✅ Appliquer", disabled=True)
        with col2:
            if st.button("❌ Refuser"):
                st.session_state.pop("propo")
                st.rerun()


# --- On affiche la page choisie dans le menu ---
if module == "💬 Copilote":
    page_copilote()
elif module == "🎨 Studio Media":
    page_studio()
elif module == "🛡️ Securite":
    page_securite()
else:
    page_evolution()
