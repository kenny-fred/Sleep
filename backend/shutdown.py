import subprocess
from datetime import datetime


def diagnostic_time():
    """
    Retourne l'heure actuelle avec les millisecondes.
    """
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def schedule_shutdown(delay_seconds):
    """
    Demande à Windows de programmer l'extinction du PC.

    IMPORTANT :
    Sleep ne fait PAS attendre le délai ici.

    C'est Windows qui possède le compte à rebours
    grâce à :

        shutdown /s /t X
    """

    timestamp = diagnostic_time()

    command = [
        "shutdown",
        "/s",
        "/t",
        str(delay_seconds),
        "/c",
        "AutoShutdownPC : extinction programmée."
    ]

    print(
        f"[{timestamp}] "
        f"[SHUTDOWN] Envoi de la commande : "
        f"shutdown /s /t {delay_seconds}"
    )

    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True
    )

    timestamp_after = diagnostic_time()

    print(
        f"[{timestamp_after}] "
        f"[SHUTDOWN] Code retour Windows : {result.returncode}"
    )

    if result.stdout:
        print(
            f"[{timestamp_after}] "
            f"[SHUTDOWN] stdout : {result.stdout.strip()}"
        )

    if result.stderr:
        print(
            f"[{timestamp_after}] "
            f"[SHUTDOWN] stderr : {result.stderr.strip()}"
        )

    return result.returncode == 0


def cancel_shutdown():
    """
    Annule une extinction Windows actuellement programmée.
    """

    timestamp = diagnostic_time()

    print(
        f"[{timestamp}] "
        "[SHUTDOWN] Envoi de shutdown /a"
    )

    result = subprocess.run(
        [
            "shutdown",
            "/a"
        ],
        check=False,
        capture_output=True,
        text=True
    )

    timestamp_after = diagnostic_time()

    print(
        f"[{timestamp_after}] "
        f"[SHUTDOWN] Annulation - code retour Windows : "
        f"{result.returncode}"
    )

    if result.stdout:
        print(
            f"[{timestamp_after}] "
            f"[SHUTDOWN] stdout : {result.stdout.strip()}"
        )

    if result.stderr:
        print(
            f"[{timestamp_after}] "
            f"[SHUTDOWN] stderr : {result.stderr.strip()}"
        )

    return result.returncode == 0