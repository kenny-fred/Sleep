from pathlib import Path


# ============================================================
# DOSSIER DE DONNÉES DE L'APPLICATION
# ============================================================

DATA_DIR = Path.home() / "AppData" / "Local" / "AutoShutdownPC"


# ============================================================
# FICHIERS
# ============================================================

HISTORY_FILE = DATA_DIR / "history.json"
CONFIG_FILE = DATA_DIR / "config.json"


# ============================================================
# CONFIGURATION PAR DÉFAUT
# ============================================================

DEFAULT_CONFIG = {
    "enabled": False,
    "shutdown_delay_seconds": 30,
    "power_policy_active": False,
    "power_policy_backup": None
}
