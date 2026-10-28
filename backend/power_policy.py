import re
import subprocess
import sys
from pathlib import Path


class PowerPolicy:

    @staticmethod
    def _app_dir() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent

        return Path(__file__).resolve().parent.parent

    @classmethod
    def _bat_path(cls, name: str) -> Path:
        path = cls._app_dir() / name

        if not path.exists():
            raise FileNotFoundError(
                f"Fichier BAT introuvable : {path}"
            )

        return path

    @staticmethod
    def _run_command(*args) -> str:
        result = subprocess.run(
            ["powercfg.exe", *args],
            capture_output=True,
            text=True,
            encoding="cp850",
            errors="replace",
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or "La commande powercfg a échoué."
            )

        return result.stdout

    @classmethod
    def _active_scheme(cls) -> str:
        output = cls._run_command(
            "/getactivescheme"
        )

        match = re.search(
            r"([0-9a-fA-F]{8}-"
            r"[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{12})",
            output,
        )

        if not match:
            raise RuntimeError(
                "Impossible de déterminer le plan d'alimentation actif."
            )

        return match.group(1)

    @classmethod
    def read_lid_actions(cls):
        scheme = cls._active_scheme()

        # On demande directement les réglages du sous-groupe
        # correspondant à la fermeture du capot.
        output = cls._run_command(
            "/q",
            scheme,
            "SUB_BUTTONS",
        )

        # On affiche temporairement la sortie complète pour diagnostic.
        print("========== POWERCFG OUTPUT ==========")
        print(output)
        print("=====================================")

        # Windows peut être en français ou en anglais.
        # On cherche simplement les deux valeurs hexadécimales
        # associées aux réglages AC/DC.
        ac_match = re.search(
            r"(?:Current\s+AC\s+Power\s+Setting\s+Index"
            r"|Index\s+du\s+paramètre\s+d'alimentation\s+secteur)"
            r"\s*:\s*0x([0-9a-fA-F]+)",
            output,
            re.IGNORECASE,
        )

        dc_match = re.search(
            r"(?:Current\s+DC\s+Power\s+Setting\s+Index"
            r"|Index\s+du\s+paramètre\s+d'alimentation\s+sur\s+batterie)"
            r"\s*:\s*0x([0-9a-fA-F]+)",
            output,
            re.IGNORECASE,
        )

        # Si Windows utilise une autre traduction, on fait une
        # deuxième tentative basée uniquement sur les lignes.
        if not ac_match or not dc_match:
            lines = output.splitlines()

            values = []

            for line in lines:
                match = re.search(
                    r"0x([0-9a-fA-F]+)",
                    line,
                )

                if match:
                    values.append(
                        int(match.group(1), 16)
                    )

            # Pour SUB_BUTTONS, les valeurs AC/DC apparaissent
            # normalement dans cet ordre.
            if len(values) >= 2:
                ac = values[-2]
                dc = values[-1]
            else:
                raise RuntimeError(
                    "Impossible de lire la configuration "
                    "de fermeture du capot."
                )
        else:
            ac = int(
                ac_match.group(1),
                16,
            )

            dc = int(
                dc_match.group(1),
                16,
            )

        return {
            "scheme": scheme,
            "ac": ac,
            "dc": dc,
        }

    @classmethod
    def _run_bat(
        cls,
        bat_path: Path,
        *arguments,
    ):
        print(
            f"[POWER] Exécution BAT : {bat_path}"
        )

        command = [
            "cmd.exe",
            "/c",
            str(bat_path),
        ]

        command.extend(
            str(argument)
            for argument in arguments
        )

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="cp850",
            errors="replace",
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        print(
            f"[POWER] BAT returncode = {result.returncode}"
        )

        if result.stdout:
            print(
                f"[POWER] BAT stdout = {result.stdout.strip()}"
            )

        if result.stderr:
            print(
                f"[POWER] BAT stderr = {result.stderr.strip()}"
            )

        if result.returncode != 0:
            output = (
                result.stderr.strip()
                or result.stdout.strip()
                or (
                    f"Le fichier {bat_path.name} "
                    f"a retourné le code {result.returncode}."
                )
            )

            raise RuntimeError(
                output
            )

        return result

    @classmethod
    def enable(cls):
        print(
            "========== POWER POLICY ENABLE =========="
        )

        print(
            "[POWER] Lecture de la configuration actuelle..."
        )

        backup = cls.read_lid_actions()

        print(
            f"[POWER] Backup = {backup}"
        )

        bat = cls._bat_path(
            "activation.bat"
        )

        print(
            f"[POWER] BAT = {bat}"
        )

        print(
            f"[POWER] Existe = {bat.exists()}"
        )

        cls._run_bat(
            bat
        )

        print(
            "[POWER] Activation terminée."
        )

        return backup

    @classmethod
    def restore(
        cls,
        backup,
    ):
        print(
            "========== POWER POLICY RESTORE =========="
        )

        if not backup:
            print(
                "[POWER] Aucun backup à restaurer."
            )
            return

        ac = backup.get(
            "ac"
        )

        dc = backup.get(
            "dc"
        )

        if ac is None or dc is None:
            raise RuntimeError(
                "Sauvegarde de la politique d'alimentation invalide."
            )

        bat = cls._bat_path(
            "desactivation.bat"
        )

        print(
            f"[POWER] BAT restauration = {bat}"
        )

        cls._run_bat(
            bat,
            int(ac),
            int(dc),
        )

        print(
            "[POWER] Restauration terminée."
        )