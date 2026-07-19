from supabase import create_client
import config

# On se connecte a la base de donnees Supabase (memoire CLOUD, partagee PC <-> telephone).
_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def charger():
    """Charge TOUS les messages passes depuis Supabase, dans l'ordre. Renvoie une liste."""
    res = _client.table("messages").select("role, content").order("id").execute()
    return res.data or []


def ajouter_message(role, content):
    """Sauve UN message (role = 'user' ou 'assistant') dans la memoire cloud."""
    _client.table("messages").insert({"role": role, "content": content}).execute()


def effacer():
    """Vide toute la memoire (nouvelle conversation)."""
    _client.table("messages").delete().neq("id", 0).execute()
