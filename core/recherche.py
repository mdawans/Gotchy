import datetime
from core.llm import demander_llm

# Recherche web GRATUITE (DuckDuckGo, aucune cle) : Gotchy cherche quand il n'est pas sur,
# puis repond en s'appuyant sur des sources fiables (qu'il cite).


def _aujourdhui():
    """La date d'aujourd'hui en francais (pour comprendre 'hier', 'la veille', etc.)."""
    return datetime.date.today().strftime("%d/%m/%Y")


def besoin_de_chercher(question):
    """Demande a l'IA si la question necessite une recherche web. Renvoie True/False."""
    messages = [
        {
            "role": "system",
            "content": (
                "Reponds UNIQUEMENT par OUI ou NON. OUI si repondre demande une info RECENTE, "
                "changeante ou incertaine (actualite, meteo, prix, dernieres versions, evenements, "
                "resultats sportifs). NON si c'est une connaissance stable (cours, definitions, "
                "calcul, code, traduction, creativite, discussion)."
            ),
        },
        {"role": "user", "content": question},
    ]
    return demander_llm(messages).strip().upper().startswith("OUI")


def formuler_requete(question):
    """Transforme la question (avec dates relatives type 'hier') en une bonne requete de recherche."""
    messages = [
        {
            "role": "system",
            "content": (
                f"Nous sommes le {_aujourdhui()}. Transforme la question de l'utilisateur en UNE requete "
                "de recherche web courte et efficace (mots-cles), en resolvant les dates relatives "
                "('hier', 'la veille', 'cette semaine'...) en dates PRECISES. "
                "Reponds avec SEULEMENT la requete, rien d'autre."
            ),
        },
        {"role": "user", "content": question},
    ]
    return demander_llm(messages).strip()


def chercher(requete, n=5):
    """Cherche sur le web (DuckDuckGo, gratuit, sans cle). Renvoie une liste de resultats."""
    from ddgs import DDGS

    with DDGS() as ddgs:
        return list(ddgs.text(requete, max_results=n))


def repondre_avec_web(question):
    """Cherche sur le web puis repond. Renvoie (texte_reponse, liste_de_sources).
    Les sources sont renvoyees a part pour etre affichees dans un bouton (pas dans le texte)."""
    requete = formuler_requete(question)
    try:
        resultats = chercher(requete)
    except Exception:
        resultats = []

    # Si la recherche echoue -> l'IA repond de sa memoire, en le precisant honnetement (aucune source)
    if not resultats:
        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es Gotchy. Reponds en francais, de facon concise. Precise honnetement que tu "
                    "n'as pas pu chercher sur le web et que tu reponds de memoire (donc a verifier)."
                ),
            },
            {"role": "user", "content": question},
        ]
        return demander_llm(messages), []

    # On met les resultats en forme pour l'IA
    lignes = []
    for r in resultats:
        titre = r.get("title", "")
        lien = r.get("href") or r.get("link") or r.get("url") or ""
        extrait = r.get("body") or r.get("snippet") or ""
        lignes.append(f"- {titre} ({lien}) : {extrait}")
    sources = "\n".join(lignes)

    messages = [
        {
            "role": "system",
            "content": (
                f"Nous sommes le {_aujourdhui()}. Tu es Gotchy, assistant francais. Reponds a la question "
                "de facon CONCISE, en t'appuyant sur les resultats fournis. Privilegie les sources FIABLES "
                "(sites officiels, Wikipedia, medias reconnus). NE mentionne AUCUNE source dans ton texte : "
                "ni lien, ni nom de site, ni '(Sources: ...)'. Donne JUSTE l'information directement "
                "(les sources sont affichees separement dans un bouton). Si les resultats ne suffisent pas, "
                "dis-le honnetement (et si la question est vague, demande une precision)."
            ),
        },
        {
            "role": "user",
            "content": f"Question : {question}\n(Recherche effectuee : {requete})\n\nResultats web :\n{sources}",
        },
    ]
    return demander_llm(messages), resultats
