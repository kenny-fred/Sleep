from datetime import datetime

from PySide6.QtCore import QThread, Signal

from . import lid_monitor


def diagnostic_time():
    """
    Retourne l'heure actuelle avec les millisecondes.

    Exemple :
        13:42:15.237
    """
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


class LidWorker(QThread):
    """
    Thread Qt chargé de surveiller le capot.

    MODE DIAGNOSTIC :
    On affiche l'heure exacte à laquelle
    Windows transmet l'événement au worker.
    """

    lid_changed = Signal(int)
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False

    def start_monitor(self):
        if self.running:
            return

        self.running = True
        self.start()

    def run(self):
        try:

            def on_lid_change(lid_state):
                timestamp = diagnostic_time()

                print(
                    f"[{timestamp}] "
                    f"[LID WORKER] Événement capot reçu : {lid_state}"
                )

                if lid_state == 0:
                    print(
                        f"[{timestamp}] "
                        "[LID WORKER] → CAPOT FERMÉ"
                    )

                elif lid_state == 1:
                    print(
                        f"[{timestamp}] "
                        "[LID WORKER] → CAPOT OUVERT"
                    )

                self.lid_changed.emit(lid_state)

            lid_monitor.start(on_lid_change)

        except Exception as error:
            self.error.emit(str(error))

        finally:
            self.running = False

    def stop_monitor(self):
        if not self.running:
            return

        try:
            lid_monitor.stop()

        except Exception as error:
            self.error.emit(str(error))

        self.wait()
        self.running = False