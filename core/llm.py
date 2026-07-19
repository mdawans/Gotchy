from groq import Groq
import config

# On cree le client Groq une seule fois, avec la cle lue dans le .env.
client = Groq(api_key=config.GROQ_API_KEY)


def demander_llm(messages, modele=None):
    """Envoie la liste des messages a l'IA (Groq / Llama) et renvoie sa reponse (texte).

    'messages' est une liste comme :
        [{"role": "system", "content": "..."},
         {"role": "user", "content": "Salut !"}]
    'modele' : par defaut le modele texte ; on peut passer le modele VISION pour analyser une image.
    """
    reponse = client.chat.completions.create(
        model=modele or config.MODELE,
        messages=messages,
    )
    return reponse.choices[0].message.content
