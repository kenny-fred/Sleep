import json

from . import config
from . import history
from . import shutdown
from .power_policy import PowerPolicy


class SleepController:
    """
    Cerveau principal de Sleep.

    Le Controller centralise :

        - la configuration
        - l'activation / désactivation
        - le délai d'extinction
        - l'historique
        - la réaction au capot
        - la programmation de l'extinction
        - l'annulation de l'extinction
    """

    def __init__(self):

        self.shutdown_scheduled = False

        self.config = self.load_config()

        # Si Sleep a été interrompu alors qu'une politique Windows était
        # temporairement modifiée, on tente de la restaurer au prochain
        # démarrage avant de laisser l'application continuer.
        if self.config.get("power_policy_active"):
            try:
                self._restore_power_policy()
            except Exception as error:
                print(
                    f"[POWER] ⚠️ Restauration impossible au démarrage : {error}"
                )

    # =====================================================
    # CONFIGURATION
    # =====================================================

    def load_config(self):

        config.DATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        if not config.CONFIG_FILE.exists():

            self._write_config(
                config.DEFAULT_CONFIG.copy()
            )

            return config.DEFAULT_CONFIG.copy()

        try:

            with open(
                config.CONFIG_FILE,
                "r",
                encoding="utf-8-sig"
            ) as file:

                loaded_config = json.load(file)

        except (
            json.JSONDecodeError,
            OSError
        ):

            print(
                "[CONTROLLER] ⚠️ "
                "Impossible de lire config.json."
            )

            return config.DEFAULT_CONFIG.copy()

        if not isinstance(
            loaded_config,
            dict
        ):

            print(
                "[CONTROLLER] ⚠️ "
                "Configuration invalide."
            )

            return config.DEFAULT_CONFIG.copy()

        final_config = (
            config.DEFAULT_CONFIG.copy()
        )

        final_config.update(
            loaded_config
        )

        # Migration des anciennes configurations : avant la gestion de la
        # politique Windows, "enabled=True" pouvait être enregistré sans
        # sauvegarde de la politique. On repart donc désactivé une seule fois.
        if "power_policy_active" not in loaded_config:
            final_config["enabled"] = False
            final_config["power_policy_active"] = False
            final_config["power_policy_backup"] = None
            self._write_config(final_config)

        return final_config

    # =====================================================
    # ÉCRITURE CONFIGURATION
    # =====================================================

    def _write_config(
        self,
        new_config
    ):

        config.DATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            config.CONFIG_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                new_config,
                file,
                indent=4,
                ensure_ascii=False
            )

    # =====================================================
    # ACTUALISER CONFIGURATION
    # =====================================================

    def refresh_config(self):

        self.config = self.load_config()

        return self.config.copy()

    # =====================================================
    # PROTECTION
    # =====================================================

    def is_enabled(self):

        return bool(
            self.config.get(
                "enabled",
                False
            )
        )

    def _enable_power_policy(self):

        if self.config.get("power_policy_active"):
            return True

        backup = PowerPolicy.enable()

        self.config["power_policy_backup"] = backup
        self.config["power_policy_active"] = True

        self._write_config(self.config)

        print("[POWER] Politique capot temporairement désactivée.")

        return True

    def _restore_power_policy(self):

        if not self.config.get("power_policy_active"):
            return True

        backup = self.config.get("power_policy_backup")
        PowerPolicy.restore(backup)

        self.config["power_policy_backup"] = None
        self.config["power_policy_active"] = False

        self._write_config(self.config)

        print("[POWER] Politique capot restaurée.")

        return True

    def set_enabled(
        self,
        enabled
    ):

        enabled = bool(enabled)

        if enabled == self.is_enabled():
            return enabled

        if enabled:
            # On ne passe la protection à ON qu'après avoir réussi à
            # modifier la politique Windows.
            self._enable_power_policy()
            self.config["enabled"] = True
        else:
            # La protection n'est désactivée qu'après restauration réussie.
            self._restore_power_policy()
            self.config["enabled"] = False

        self._write_config(self.config)

        return self.is_enabled()

    def stop(self):

        if self.shutdown_scheduled:
            self.cancel_scheduled_shutdown()

        try:
            self._restore_power_policy()
        except Exception as error:
            print(
                f"[POWER] ⚠️ Impossible de restaurer la configuration : {error}"
            )

    def toggle_enabled(self):

        return self.set_enabled(
            not self.is_enabled()
        )

    # =====================================================
    # DÉLAI
    # =====================================================

    def get_delay(self):

        try:

            delay = int(
                self.config.get(
                    "shutdown_delay_seconds",
                    10
                )
            )

        except (
            TypeError,
            ValueError
        ):

            delay = 10

        if delay < 1:

            delay = 10

        return delay

    def set_delay(
        self,
        delay_seconds
    ):

        try:

            delay = int(
                delay_seconds
            )

        except (
            TypeError,
            ValueError
        ):

            raise ValueError(
                "Le délai doit être "
                "un nombre entier."
            )

        if delay < 1:

            raise ValueError(
                "Le délai doit être "
                "supérieur ou égal à "
                "1 seconde."
            )

        self.config[
            "shutdown_delay_seconds"
        ] = delay

        self._write_config(
            self.config
        )

        return delay

    # =====================================================
    # GESTION DU CAPOT
    # =====================================================

    def handle_lid_change(
        self,
        lid_state
    ):

        # -------------------------------------------------
        # CAPOT OUVERT
        # -------------------------------------------------

        if lid_state == 1:

            print(
                "[LID] 🟢 CAPOT OUVERT"
            )

            # ---------------------------------------------
            # Une extinction était programmée
            # ---------------------------------------------

            if self.shutdown_scheduled:

                print(
                    "[CONTROLLER] "
                    "Extinction programmée détectée."
                )

                print(
                    "[CONTROLLER] "
                    "Annulation de l'extinction."
                )

                self.cancel_scheduled_shutdown()

                return {
                    "event": "lid_opened",
                    "shutdown_scheduled": False,
                    "shutdown_cancelled": True
                }

            return {
                "event": "lid_opened",
                "shutdown_scheduled": False
            }

        # -------------------------------------------------
        # ÉTAT INCONNU
        # -------------------------------------------------

        if lid_state != 0:

            print(
                f"[LID] ⚠️ État inconnu : {lid_state}"
            )

            return {
                "event": "unknown",
                "shutdown_scheduled": False
            }

        # -------------------------------------------------
        # CAPOT FERMÉ
        # -------------------------------------------------

        print(
            "[LID] 🔴 CAPOT FERME"
        )

        # Toujours relire la configuration.
        self.refresh_config()

        # -------------------------------------------------
        # PROTECTION DÉSACTIVÉE
        # -------------------------------------------------

        if not self.is_enabled():

            delay = self.get_delay()

            event = history.add_event(
                "lid_closed_while_disabled",
                delay
            )

            print(
                "[CONTROLLER] "
                "Protection désactivée."
            )

            print(
                "[CONTROLLER] "
                "Aucune extinction."
            )

            return {
                "event":
                    "lid_closed_while_disabled",

                "shutdown_scheduled":
                    False,

                "history_event":
                    event
            }

        # -------------------------------------------------
        # EXTINCTION DÉJÀ PROGRAMMÉE
        # -------------------------------------------------

        if self.shutdown_scheduled:

            print(
                "[CONTROLLER] "
                "Une extinction est déjà programmée."
            )

            return {
                "event":
                    "shutdown_already_scheduled",

                "shutdown_scheduled":
                    True
            }

        # -------------------------------------------------
        # PROGRAMMATION EXTINCTION
        # -------------------------------------------------

        delay = self.get_delay()

        event = history.add_event(
            "lid_closed",
            delay
        )

        print(
            "[HISTORY] "
            "Événement enregistré."
        )

        print(
            f"[HISTORY] "
            f"{event['timestamp']}"
        )

        print(
            f"[SHUTDOWN] "
            f"Extinction dans "
            f"{delay} seconde(s)."
        )

        shutdown.schedule_shutdown(
            delay
        )

        self.shutdown_scheduled = True

        return {
            "event":
                "lid_closed",

            "shutdown_scheduled":
                True,

            "delay":
                delay,

            "history_event":
                event
        }

    # =====================================================
    # ANNULATION EXTINCTION
    # =====================================================

    def cancel_scheduled_shutdown(self):

        if not self.shutdown_scheduled:

            return False

        shutdown.cancel_shutdown()

        self.shutdown_scheduled = False

        print(
            "[CONTROLLER] "
            "Extinction annulée."
        )

        return True

    # =====================================================
    # ÉTAT
    # =====================================================

    def get_status(self):

        return {
            "enabled":
                self.is_enabled(),

            "delay":
                self.get_delay(),

            "shutdown_scheduled":
                self.shutdown_scheduled
        }