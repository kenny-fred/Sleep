import json

from datetime import datetime, timedelta

from backend import config
from backend.controller import SleepController
from backend.lid_worker import LidWorker

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QSpinBox,
    QMessageBox,
)


class Dashboard(QWidget):

    protection_changed = Signal(bool)

    def __init__(self):
        super().__init__()

        # =================================================
        # BACKEND
        # =================================================

        self.controller = SleepController()

        self.lid_worker = LidWorker()

        self.lid_worker.lid_changed.connect(
            self.on_lid_changed
        )

        self.lid_worker.error.connect(
            self.on_lid_error
        )

        self.app_config = (
            self.controller.refresh_config()
        )

        self.history = self.load_history()

        statistics = self.calculate_statistics()

        # =================================================
        # LAYOUT PRINCIPAL
        # =================================================

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(
            16
        )

        # =================================================
        # TITRE
        # =================================================

        title = QLabel(
            "Tableau de bord"
        )

        title.setObjectName(
            "dashboard_title"
        )

        main_layout.addWidget(
            title
        )

        # =================================================
        # PREMIÈRE LIGNE
        # =================================================

        first_row = QHBoxLayout()

        first_row.setSpacing(
            14
        )

        # -------------------------------------------------
        # CARTE PROTECTION
        # -------------------------------------------------

        protection_card = QFrame()

        protection_card.setObjectName(
            "card"
        )

        protection_layout = QVBoxLayout(
            protection_card
        )

        protection_layout.setContentsMargins(
            20,
            16,
            20,
            16
        )

        protection_layout.setSpacing(
            7
        )

        protection_title = QLabel(
            "PROTECTION"
        )

        protection_title.setObjectName(
            "card_title"
        )

        protection_layout.addWidget(
            protection_title
        )

        protection_enabled = (
            self.controller.is_enabled()
        )

        self.protection_value = QLabel()

        self.protection_value.setObjectName(
            "big_value"
        )

        protection_layout.addWidget(
            self.protection_value
        )

        self.protection_button = QPushButton()

        self.protection_button.setFixedHeight(
            34
        )

        self.protection_button.clicked.connect(
            self.toggle_protection
        )

        protection_layout.addWidget(
            self.protection_button
        )

        self.update_protection_card(
            protection_enabled
        )

        first_row.addWidget(
            protection_card
        )

        # -------------------------------------------------
        # CARTE CAPOT
        # -------------------------------------------------

        lid_card = QFrame()

        lid_card.setObjectName(
            "card"
        )

        lid_layout = QVBoxLayout(
            lid_card
        )

        lid_layout.setContentsMargins(
            20,
            16,
            20,
            16
        )

        lid_layout.setSpacing(
            7
        )

        lid_title = QLabel(
            "CAPOT"
        )

        lid_title.setObjectName(
            "card_title"
        )

        lid_layout.addWidget(
            lid_title
        )

        self.lid_state = QLabel(
            "Ouvert"
        )

        self.lid_state.setObjectName(
            "big_value"
        )

        lid_layout.addWidget(
            self.lid_state
        )

        lid_description = QLabel(
            "État actuel du capot"
        )

        lid_description.setObjectName(
            "card_text"
        )

        lid_layout.addWidget(
            lid_description
        )

        first_row.addWidget(
            lid_card
        )

        # -------------------------------------------------
        # CARTE DERNIÈRE FERMETURE
        # -------------------------------------------------

        last_close_card = QFrame()

        last_close_card.setObjectName(
            "card"
        )

        last_close_layout = QVBoxLayout(
            last_close_card
        )

        last_close_layout.setContentsMargins(
            20,
            16,
            20,
            16
        )

        last_close_layout.setSpacing(
            7
        )

        last_close_title = QLabel(
            "DERNIÈRE FERMETURE"
        )

        last_close_title.setObjectName(
            "card_title"
        )

        last_close_layout.addWidget(
            last_close_title
        )

        self.last_close_value = QLabel(
            statistics["last_close"]
        )

        self.last_close_value.setObjectName(
            "big_value"
        )

        last_close_layout.addWidget(
            self.last_close_value
        )

        last_close_description = QLabel(
            "Dernier événement détecté"
        )

        last_close_description.setObjectName(
            "card_text"
        )

        last_close_layout.addWidget(
            last_close_description
        )

        first_row.addWidget(
            last_close_card
        )

        main_layout.addLayout(
            first_row
        )

        # =================================================
        # DEUXIÈME LIGNE
        # =================================================

        second_row = QHBoxLayout()

        second_row.setSpacing(
            14
        )

        # -------------------------------------------------
        # CARTE DÉLAI
        # -------------------------------------------------

        delay_card = QFrame()

        delay_card.setObjectName(
            "card"
        )

        delay_layout = QVBoxLayout(
            delay_card
        )

        delay_layout.setContentsMargins(
            20,
            16,
            20,
            16
        )

        delay_layout.setSpacing(
            8
        )

        delay_title = QLabel(
            "DÉLAI D'EXTINCTION"
        )

        delay_title.setObjectName(
            "card_title"
        )

        delay_layout.addWidget(
            delay_title
        )

        delay_controls = QHBoxLayout()

        delay_controls.setSpacing(
            10
        )

        self.delay_spinbox = QSpinBox()

        self.delay_spinbox.setRange(
            1,
            3600
        )

        self.delay_spinbox.setValue(
            self.controller.get_delay()
        )

        self.delay_spinbox.setSuffix(
            " secondes"
        )

        self.delay_spinbox.setFixedHeight(
            36
        )

        delay_controls.addWidget(
            self.delay_spinbox
        )

        delay_controls.addStretch()

        self.save_delay_button = QPushButton(
            "Sauvegarder"
        )

        self.save_delay_button.setFixedHeight(
            36
        )

        self.save_delay_button.clicked.connect(
            self.save_delay
        )

        delay_controls.addWidget(
            self.save_delay_button
        )

        delay_layout.addLayout(
            delay_controls
        )

        delay_description = QLabel(
            "Délai avant l'extinction automatique."
        )

        delay_description.setObjectName(
            "card_text"
        )

        delay_layout.addWidget(
            delay_description
        )

        second_row.addWidget(
            delay_card,
            3
        )

        # -------------------------------------------------
        # CARTE FERMETURES NON TRAITÉES
        # -------------------------------------------------

        missed_card = QFrame()

        missed_card.setObjectName(
            "card"
        )

        missed_layout = QVBoxLayout(
            missed_card
        )

        missed_layout.setContentsMargins(
            20,
            16,
            20,
            16
        )

        missed_layout.setSpacing(
            7
        )

        missed_title = QLabel(
            "FERMETURES NON TRAITÉES"
        )

        missed_title.setObjectName(
            "card_title"
        )

        missed_layout.addWidget(
            missed_title
        )

        self.missed_value = QLabel(
            str(statistics["missed"])
        )

        self.missed_value.setObjectName(
            "big_value"
        )

        missed_layout.addWidget(
            self.missed_value
        )

        missed_description = QLabel(
            "Capot fermé sans extinction du PC."
        )

        missed_description.setObjectName(
            "card_text"
        )

        missed_layout.addWidget(
            missed_description
        )

        second_row.addWidget(
            missed_card,
            1
        )

        main_layout.addLayout(
            second_row
        )

        # =================================================
        # GRAPHIQUE
        # =================================================

        graph_card = QFrame()

        graph_card.setObjectName(
            "card"
        )

        graph_layout = QVBoxLayout(
            graph_card
        )

        graph_layout.setContentsMargins(
            20,
            14,
            20,
            12
        )

        graph_layout.setSpacing(
            5
        )

        graph_title = QLabel(
            "ACTIVITÉ - 7 DERNIERS JOURS"
        )

        graph_title.setObjectName(
            "card_title"
        )

        graph_layout.addWidget(
            graph_title
        )

        self.graph = ActivityGraph(
            statistics["daily_counts"]
        )

        # Hauteur raisonnable pour que le graphique
        # soit visible directement dans le Dashboard.
        self.graph.setMinimumHeight(
            145
        )

        self.graph.setMaximumHeight(
            170
        )

        graph_layout.addWidget(
            self.graph
        )

        main_layout.addWidget(
            graph_card,
            1
        )

        # =================================================
        # DÉMARRAGE DU MONITEUR
        # =================================================

        self.lid_worker.start_monitor()

    # =====================================================
    # CAPOT
    # =====================================================

    def on_lid_changed(
        self,
        lid_state
    ):

        print(
            f"[DASHBOARD] État du capot reçu : {lid_state}"
        )

        if lid_state == 1:

            self.lid_state.setText(
                "Ouvert"
            )

        elif lid_state == 0:

            self.lid_state.setText(
                "Fermé"
            )

        result = (
            self.controller.handle_lid_change(
                lid_state
            )
        )

        print(
            f"[DASHBOARD] Résultat : {result}"
        )

        if "history_event" in result:

            self.refresh_statistics()

    def on_lid_error(
        self,
        error_message
    ):

        print(
            "[LID WORKER] ❌",
            error_message
        )

    # =====================================================
    # STATISTIQUES
    # =====================================================

    def refresh_statistics(self):

        self.history = (
            self.load_history()
        )

        statistics = (
            self.calculate_statistics()
        )

        self.last_close_value.setText(
            statistics["last_close"]
        )

        self.missed_value.setText(
            str(
                statistics["missed"]
            )
        )

        self.graph.daily_counts = (
            statistics["daily_counts"]
        )

        self.graph.update()

    def load_history(self):

        if not config.HISTORY_FILE.exists():

            return []

        try:

            with open(
                config.HISTORY_FILE,
                "r",
                encoding="utf-8-sig"
            ) as file:

                history = json.load(
                    file
                )

        except (
            json.JSONDecodeError,
            OSError
        ):

            return []

        if not isinstance(
            history,
            list
        ):

            return []

        return history

    def calculate_statistics(self):

        total = 0

        missed = 0

        now = datetime.now()

        week_start = (
            now - timedelta(
                days=7
            )
        )

        daily_counts = [0] * 7

        last_close = "Aucune"

        latest_close_timestamp = None

        for event in self.history:

            reason = event.get(
                "reason"
            )

            if reason not in (
                "lid_closed",
                "lid_closed_while_disabled",
            ):

                continue

            try:

                timestamp = (
                    datetime.fromisoformat(
                        event["timestamp"]
                    )
                )

            except (
                KeyError,
                ValueError,
                TypeError
            ):

                continue

            # ---------------------------------------------
            # DERNIÈRE FERMETURE
            # ---------------------------------------------

            if (
                latest_close_timestamp is None
                or timestamp > latest_close_timestamp
            ):

                latest_close_timestamp = (
                    timestamp
                )

                last_close = (
                    timestamp.strftime(
                        "%d/%m à %H:%M"
                    )
                )

            # ---------------------------------------------
            # COMPTEURS
            # ---------------------------------------------

            if reason == "lid_closed":

                total += 1

            elif reason == "lid_closed_while_disabled":

                missed += 1

            # ---------------------------------------------
            # ACTIVITÉ DES 7 DERNIERS JOURS
            # ---------------------------------------------

            if timestamp >= week_start:

                days_ago = (
                    now.date()
                    - timestamp.date()
                ).days

                if 0 <= days_ago < 7:

                    index = (
                        6 - days_ago
                    )

                    daily_counts[index] += 1

        return {
            "total": total,
            "missed": missed,
            "last_close": last_close,
            "daily_counts": daily_counts,
        }

    # =====================================================
    # PROTECTION
    # =====================================================

    def update_protection_card(
        self,
        enabled
    ):

        if enabled:

            self.protection_value.setText(
                "Active"
            )

            self.protection_button.setText(
                "Désactiver"
            )

        else:

            self.protection_value.setText(
                "Désactivée"
            )

            self.protection_button.setText(
                "Activer"
            )

    def toggle_protection(self):

        print("========== TEST BOUTON ACTIVER ==========")
        print("[DASHBOARD] toggle_protection() APPELE")

        try:

            print(
                "[DASHBOARD] AVANT toggle_enabled()"
            )

            new_value = (
                self.controller.toggle_enabled()
            )

            print(
                "[DASHBOARD] APRES toggle_enabled()"
            )

            print(
                "[DASHBOARD] new_value =",
                new_value
            )

        except Exception as error:

            import traceback

            print(
                "========== ERREUR =========="
            )

            print(
                type(error).__name__
            )

            print(
                str(error)
            )

            traceback.print_exc()

            print(
                "============================"
            )

            QMessageBox.critical(
                self,
                "ERREUR",
                f"{type(error).__name__}\n\n{error}"
            )

            return

        # -------------------------------------------------
        # RAFRAÎCHISSEMENT CONFIGURATION
        # -------------------------------------------------

        self.app_config = (
            self.controller.refresh_config()
        )

        self.update_protection_card(
            new_value
        )

        # -------------------------------------------------
        # INFORME LA FENÊTRE PRINCIPALE
        # -------------------------------------------------

        self.protection_changed.emit(
            bool(new_value)
        )

    # =====================================================
    # DÉLAI
    # =====================================================

    def save_delay(self):
        delay = (
            self.delay_spinbox.value()
        )

        try:

            self.controller.set_delay(
                delay
            )

        except ValueError:

            return

        self.app_config = (
            self.controller.refresh_config()
        )

        self.save_delay_button.setText(
            "Sauvegardé ✓"
        )
    # =====================================================
    # ARRÊT
    # =====================================================

    def stop(self):

        if self.lid_worker is not None:

            self.lid_worker.stop_monitor()

        self.controller.stop()


# =========================================================
# GRAPHIQUE D'ACTIVITÉ
# =========================================================

class ActivityGraph(QWidget):

    def __init__(
        self,
        daily_counts
    ):

        super().__init__()

        self.daily_counts = (
            daily_counts
        )

        self.setMinimumHeight(
            145
        )

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        width = self.width()

        height = self.height()

        # -------------------------------------------------
        # MARGES
        # -------------------------------------------------

        left = 34

        right = 10

        top = 8

        bottom = 26

        graph_width = (
            width
            - left
            - right
        )

        graph_height = (
            height
            - top
            - bottom
        )

        if graph_width <= 0 or graph_height <= 0:

            painter.end()

            return

        # -------------------------------------------------
        # MAXIMUM
        # -------------------------------------------------

        maximum = (
            max(
                self.daily_counts
            )
            if self.daily_counts
            else 0
        )

        if maximum == 0:

            maximum = 1

        # -------------------------------------------------
        # GRILLE
        # -------------------------------------------------

        pen = QPen(
            Qt.GlobalColor.darkGray
        )

        pen.setWidth(
            1
        )

        painter.setPen(
            pen
        )

        # 4 lignes horizontales
        for i in range(4):

            y = (
                top
                + graph_height
                * i
                / 3
            )

            painter.drawLine(
                left,
                int(y),
                width - right,
                int(y)
            )

        # -------------------------------------------------
        # VALEURS À GAUCHE
        # -------------------------------------------------

        painter.setPen(
            Qt.GlobalColor.lightGray
        )

        for i in range(4):

            value = round(
                maximum
                * (3 - i)
                / 3
            )

            y = (
                top
                + graph_height
                * i
                / 3
            )

            painter.drawText(
                0,
                int(y - 5),
                left - 7,
                15,
                Qt.AlignmentFlag.AlignRight,
                str(value)
            )

        # -------------------------------------------------
        # BARRES
        # -------------------------------------------------

        count = len(
            self.daily_counts
        )

        if count == 0:

            painter.end()

            return

        bar_width = (
            graph_width
            / count
        )

        for i, value in enumerate(
            self.daily_counts
        ):

            bar_height = (
                value
                / maximum
                * graph_height
            )

            x = (
                left
                + i * bar_width
                + bar_width * 0.28
            )

            y = (
                top
                + graph_height
                - bar_height
            )

            # Barre
            painter.drawRect(
                int(x),
                int(y),
                max(
                    2,
                    int(
                        bar_width
                        * 0.44
                    )
                ),
                max(
                    1,
                    int(
                        bar_height
                    )
                )
            )

            # Valeur au-dessus de la barre
            if value > 0:

                painter.drawText(
                    int(x),
                    int(y - 5),
                    max(
                        2,
                        int(
                            bar_width
                            * 0.44
                        )
                    ),
                    15,
                    Qt.AlignmentFlag.AlignCenter,
                    str(value)
                )

        # -------------------------------------------------
        # JOURS
        # -------------------------------------------------

        today = datetime.now()

        day_names = [
            "Lun",
            "Mar",
            "Mer",
            "Jeu",
            "Ven",
            "Sam",
            "Dim",
        ]

        painter.setPen(
            Qt.GlobalColor.lightGray
        )

        for i in range(7):

            date = (
                today
                - timedelta(
                    days=6 - i
                )
            )

            label = (
                day_names[
                    date.weekday()
                ]
            )

            x = (
                left
                + i * bar_width
            )

            painter.drawText(
                int(x),
                height - 18,
                int(bar_width),
                18,
                Qt.AlignmentFlag.AlignCenter,
                label
            )

        painter.end()