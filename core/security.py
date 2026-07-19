import time
import requests
import config

# Module Securite : on envoie un fichier a VirusTotal, qui le fait analyser par ~70 antivirus.
# Etape 1 : on envoie le fichier -> VirusTotal renvoie un numero d'analyse.
# Etape 2 : on redemande le resultat de cette analyse jusqu'a ce qu'elle soit finie.

_URL_FICHIERS = "https://www.virustotal.com/api/v3/files"
_URL_GROSSE_PORTE = "https://www.virustotal.com/api/v3/files/upload_url"
_URL_ANALYSES = "https://www.virustotal.com/api/v3/analyses/"

# Au-dela de 32 Mo, VirusTotal exige de passer par une adresse d'envoi speciale.
_LIMITE_ENVOI_DIRECT = 32 * 1024 * 1024  # 32 Mo


def scanner_fichier(donnees_fichier, nom_fichier):
    """Envoie un fichier a VirusTotal et renvoie les statistiques d'analyse.

    Renvoie un dictionnaire genre {'malicious': 3, 'harmless': 60, ...}, ou None si trop long.
    """
    entetes = {"x-apikey": config.VIRUSTOTAL_KEY}

    # 1) On choisit la bonne "porte" selon la taille du fichier
    if len(donnees_fichier) <= _LIMITE_ENVOI_DIRECT:
        url_envoi = _URL_FICHIERS  # petite porte : envoi direct
    else:
        # grande porte : on demande d'abord une adresse d'envoi speciale (fichier jusqu'a 650 Mo)
        rep = requests.get(_URL_GROSSE_PORTE, headers=entetes)
        rep.raise_for_status()
        url_envoi = rep.json()["data"]

    # 2) On envoie le fichier a analyser
    reponse = requests.post(
        url_envoi,
        headers=entetes,
        files={"file": (nom_fichier, donnees_fichier)},
    )
    reponse.raise_for_status()
    analyse_id = reponse.json()["data"]["id"]

    # 2) On attend le resultat (l'analyse prend quelques secondes ; on redemande jusqu'a 30 fois)
    for _ in range(30):
        res = requests.get(_URL_ANALYSES + analyse_id, headers=entetes)
        res.raise_for_status()
        attributs = res.json()["data"]["attributes"]
        if attributs["status"] == "completed":
            return attributs["stats"]
        time.sleep(2)

    return None  # l'analyse a pris trop de temps
