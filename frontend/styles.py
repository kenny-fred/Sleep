APP_STYLE = """
/* =========================================================
   GLOBAL
   ========================================================= */

QMainWindow {
    background-color: #1e1e1e;
}

QWidget#centralWidget {
    background-color: #1e1e1e;
}

QWidget {
    color: #f2f2f2;
    font-family: "Segoe UI";
    font-size: 14px;
}


/* =========================================================
   TEXTES
   ========================================================= */

#subtitle {
    color: #cfcfcf;
    font-size: 15px;
}

#dashboard_title {
    font-size: 18px;
    font-weight: 600;
}

#section_title {
    font-size: 15px;
    font-weight: 600;
}

#card_title {
    color: #d0d0d0;
    font-size: 13px;
}

#card_text {
    color: #c8c8c8;
    font-size: 14px;
}

#big_value {
    font-size: 18px;
    font-weight: 500;
}

#status {
    color: #ffffff;
    font-size: 16px;
    font-weight: 600;
}


/* =========================================================
   CARDS
   ========================================================= */

#card,
#stat_card {
    background-color: #202020;

    /* LE BORDER QUE TU VOULAIS */
    border: 1px solid #555555;

    border-radius: 8px;
}


/* =========================================================
   STATISTIQUES
   ========================================================= */

#stat_title {
    color: #cfcfcf;
    font-size: 13px;
}

#stat_value {
    color: #ffffff;
    font-size: 20px;
    font-weight: 600;
}


/* =========================================================
   GRAPHIQUE
   ========================================================= */

#graph_placeholder {
    color: #a8a8a8;
    background-color: #202020;

    border: 1px solid #555555;
    border-radius: 8px;
}


/* =========================================================
   BOUTONS
   ========================================================= */

QPushButton {
    background-color: #292929;
    color: #eeeeee;

    border: 1px solid #4a4a4a;
    border-radius: 7px;

    padding: 8px 16px;
}

QPushButton:hover {
    background-color: #333333;
}

QPushButton:pressed {
    background-color: #252525;
}


/* =========================================================
   CONTRÔLES NATIFS
   ========================================================= */

QSpinBox {
    background-color: #202020;
    color: #f2f2f2;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    padding: 4px 8px;
}

QSpinBox:focus {
    border-color: #777777;
}

QMenu {
    background-color: #202020;
    color: #f2f2f2;
    border: 1px solid #555555;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px;
}

QMenu::item:selected {
    background-color: #333333;
}

QMenu::item:disabled {
    color: #888888;
}

QToolTip {
    background-color: #202020;
    color: #f2f2f2;
    border: 1px solid #555555;
    padding: 4px;
}
"""