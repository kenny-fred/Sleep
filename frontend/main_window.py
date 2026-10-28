import ctypes
import sys
from pathlib import Path

from PySide6.QtGui import QAction, QColor, QIcon, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QSystemTrayIcon,
    QMenu,
)

from frontend.dashboard import Dashboard
from frontend.styles import APP_STYLE


def apply_dark_theme(application):
    application.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#f2f2f2"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#181818"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#202020"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#202020"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f2f2f2"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#f2f2f2"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#292929"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#eeeeee"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#3d6e9e"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    application.setPalette(palette)
    application.setStyleSheet(APP_STYLE)


def apply_windows_dark_title_bar(window):
    if sys.platform != "win32":
        return

    try:
        dwmapi = ctypes.WinDLL("dwmapi")
        set_window_attribute = dwmapi.DwmSetWindowAttribute
        set_window_attribute.argtypes = (
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_uint,
        )
        set_window_attribute.restype = ctypes.c_long

        dark_mode = ctypes.c_int(1)
        hwnd = ctypes.c_void_p(int(window.winId()))

        for attribute in (20, 19):
            result = set_window_attribute(
                hwnd,
                attribute,
                ctypes.byref(dark_mode),
                ctypes.sizeof(dark_mode),
            )

            if result == 0:
                return

        print(
            "[THEME] La barre de titre sombre n'est pas prise en charge "
            f"par cette version de Windows (HRESULT: {result})."
        )

    except (AttributeError, OSError) as error:
        print(
            f"[THEME] Impossible d'activer la barre de titre sombre : {error}"
        )


def resource_path(relative_path):
    """
    Retourne le chemin d'une ressource.

    En développement :
        ressources depuis le dossier du projet.

    Dans le .exe PyInstaller :
        ressources depuis le dossier temporaire
        utilisé par PyInstaller.
    """

    if getattr(sys, "frozen", False):

        base_path = Path(
            sys._MEIPASS
        )

    else:

        base_path = (
            Path(__file__)
            .resolve()
            .parent.parent
        )

    return (
        base_path
        / relative_path
    )


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self._quitting = False

        # -------------------------------------------------
        # FENÊTRE
        # -------------------------------------------------

        self.setWindowTitle(
            "Sleep"
        )

        apply_windows_dark_title_bar(self)

        self.setMinimumSize(
            760,
            560
        )

        # -------------------------------------------------
        # ICÔNE
        # -------------------------------------------------

        icon_path = resource_path(
            "assets/zzz.png"
        )

        self.app_icon = QIcon(
            str(icon_path)
        )

        self.setWindowIcon(
            self.app_icon
        )

        # -------------------------------------------------
        # DASHBOARD
        # -------------------------------------------------

        central_widget = QWidget()
        central_widget.setObjectName(
            "centralWidget"
        )

        self.setCentralWidget(
            central_widget
        )

        main_layout = QVBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            38,
            32,
            38,
            32
        )

        main_layout.setSpacing(
            0
        )

        self.dashboard = Dashboard()

        main_layout.addWidget(
            self.dashboard
        )

        # -------------------------------------------------
        # SYSTEM TRAY
        # -------------------------------------------------

        self.tray_icon = QSystemTrayIcon(
            self.app_icon,
            self
        )

        self.tray_icon.setToolTip(
            "Sleep"
        )

        self.create_tray_menu()

        self.tray_icon.activated.connect(
            self.on_tray_activated
        )

        # -------------------------------------------------
        # SIGNAL PROTECTION
        # -------------------------------------------------

        self.dashboard.protection_changed.connect(
            self.on_protection_changed
        )

        # -------------------------------------------------
        # AFFICHAGE
        # -------------------------------------------------

        if QSystemTrayIcon.isSystemTrayAvailable():

            self.tray_icon.show()

            # Sleep démarre directement dans la zone
            # de notification.
            self.hide()

        else:

            print(
                "[TRAY] ⚠️ Zone de notification indisponible."
            )

            self.showMaximized()

    # =====================================================
    # MENU SYSTEM TRAY
    # =====================================================

    def create_tray_menu(self):

        menu = QMenu()

        # -------------------------------------------------
        # OUVRIR
        # -------------------------------------------------

        open_action = QAction(
            "Ouvrir Sleep",
            self
        )

        open_action.triggered.connect(
            self.show_window
        )

        menu.addAction(
            open_action
        )

        menu.addSeparator()

        # -------------------------------------------------
        # PROTECTION
        # -------------------------------------------------

        self.protection_action = QAction(
            self
        )

        self.protection_action.triggered.connect(
            self.toggle_protection_from_tray
        )

        menu.addAction(
            self.protection_action
        )

        menu.addSeparator()

        # -------------------------------------------------
        # QUITTER
        # -------------------------------------------------

        quit_action = QAction(
            "Quitter",
            self
        )

        quit_action.triggered.connect(
            self.quit_application
        )

        menu.addAction(
            quit_action
        )

        self.tray_icon.setContextMenu(
            menu
        )

        self.update_tray_menu()

    # =====================================================
    # MENU PROTECTION
    # =====================================================

    def update_tray_menu(self):

        if self.dashboard.controller.is_enabled():

            self.protection_action.setText(
                "Désactiver la protection"
            )

        else:

            self.protection_action.setText(
                "Activer la protection"
            )

    # =====================================================
    # CLIC SUR L'ICÔNE TRAY
    # =====================================================

    def on_tray_activated(
        self,
        reason
    ):

        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):

            self.show_window()

    # =====================================================
    # OUVRIR LA FENÊTRE
    # =====================================================

    def show_window(self):

        self.show()

        self.showNormal()

        self.raise_()

        self.activateWindow()

    # =====================================================
    # TOGGLE DEPUIS LE TRAY
    # =====================================================

    def toggle_protection_from_tray(self):

        self.dashboard.toggle_protection()

    # =====================================================
    # CHANGEMENT DE PROTECTION
    # =====================================================

    def on_protection_changed(
        self,
        enabled
    ):

        self.update_tray_menu()

        if enabled:

            self.tray_icon.showMessage(
                "Sleep",
                "Protection activée.",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )

        else:

            self.tray_icon.showMessage(
                "Sleep",
                "Protection désactivée.",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )

    # =====================================================
    # FERMETURE DE LA FENÊTRE
    # =====================================================

    def closeEvent(
        self,
        event
    ):

        # -------------------------------------------------
        # VRAI QUIT
        # -------------------------------------------------

        if self._quitting:

            event.accept()

            return

        # -------------------------------------------------
        # FERMETURE NORMALE DE LA FENÊTRE
        # -------------------------------------------------

        event.ignore()

        self.hide()

    # =====================================================
    # QUITTER COMPLÈTEMENT
    # =====================================================

    def quit_application(self):

        print(
            "[APP] Fermeture de Sleep..."
        )

        self._quitting = True

        # -------------------------------------------------
        # ARRÊT PROPRE
        # -------------------------------------------------

        if self.dashboard is not None:

            self.dashboard.stop()

        # -------------------------------------------------
        # TRAY
        # -------------------------------------------------

        self.tray_icon.hide()

        print(
            "[APP] Sleep arrêté proprement."
        )

        QApplication.quit()


# =========================================================
# PROGRAMME PRINCIPAL
# =========================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    # Important :
    # l'application doit continuer à fonctionner
    # même lorsque la fenêtre est cachée.
    app.setQuitOnLastWindowClosed(
        False
    )

    apply_dark_theme(app)

    window = MainWindow()

    sys.exit(
        app.exec()
    )