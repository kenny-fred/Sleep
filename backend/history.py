import json

from datetime import datetime

from .config import DATA_DIR, HISTORY_FILE


# ============================================================
# CHARGER L'HISTORIQUE
# ============================================================

def load_history():
    """
    Charge l'historique depuis history.json.
    """

    # On s'assure que le dossier existe.
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Si le fichier n'existe pas encore,
    # il n'y a simplement aucun événement.
    if not HISTORY_FILE.exists():
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            history = json.load(file)

        # L'historique doit être une liste.
        if isinstance(history, list):
            return history

        return []

    except (json.JSONDecodeError, OSError):
        return []


# ============================================================
# SAUVEGARDER L'HISTORIQUE
# ============================================================

def save_history(history):
    """
    Sauvegarde la liste des événements.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(
            history,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# AJOUTER UN ÉVÉNEMENT
# ============================================================

def add_event(reason, shutdown_delay_seconds):
    """
    Ajoute un événement dans l'historique.
    """

    history = load_history()

    event = {
        "timestamp": datetime.now().isoformat(),
        "reason": reason,
        "shutdown_delay_seconds": shutdown_delay_seconds
    }

    history.append(event)

    save_history(history)

    return event