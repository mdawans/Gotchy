from supabase import create_client
import config

# On se connecte a la base de donnees Supabase (memoire CLOUD).
# Chaque message est marque avec le "pseudo" de son proprietaire -> chacun a SON historique.
_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def charger(pseudo):
    """Charge SEULEMENT les messages de cette personne (son pseudo), dans l'ordre."""
    res = (
        _client.table("messages")
        .select("role, content")
        .eq("pseudo", pseudo)
        .order("id")
        .execute()
    )
    return res.data or []


def ajouter_message(pseudo, role, content):
    """Sauve UN message en le marquant avec le pseudo de son proprietaire."""
    _client.table("messages").insert(
        {"pseudo": pseudo, "role": role, "content": content}
    ).execute()


def effacer(pseudo):
    """Vide la memoire de CETTE personne uniquement (pas celle des autres !)."""
    _client.table("messages").delete().eq("pseudo", pseudo).execute()
