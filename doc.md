# 📘 Rapport définitif — Projet **Sleep**

## 1. Résumé du projet

**Sleep** est une application Windows développée en Python dont l'objectif est simple :

> **Protéger l'utilisateur contre une extinction accidentelle ou un oubli lors de la fermeture du capot de son ordinateur portable.**

L'application fonctionne uniquement lorsque l'utilisateur la lance volontairement.

Lorsqu'elle est active :

```text
Utilisateur lance Sleep
        ↓
Sleep surveille le capot
        ↓
Capot fermé
        ↓
Windows reçoit l'ordre d'extinction
        ↓
Compte à rebours configurable
        ↓
    ┌───────────────┐
    │               │
Capot rouvert    Capot reste fermé
    │               │
shutdown /a      Windows éteint
    │               │
Annulation       Protection exécutée
```

Le projet est donc à la fois un **projet logiciel**, un **projet d'intégration avec Windows**, un **projet d'interface utilisateur** et un petit exercice d'architecture système.

---

# 2. L'intention initiale

L'idée de départ était née d'un problème très concret :

> **Que se passe-t-il lorsqu'on ferme le capot d'un PC portable sans forcément vouloir le laisser fonctionner ?**

Sur un ordinateur portable, fermer le capot déclenche normalement une politique Windows : veille, hibernation, extinction, etc., selon la configuration.

Mais le projet cherchait à apporter une couche supplémentaire de protection :

> Si l'utilisateur lance volontairement Sleep, la fermeture du capot devient un signal permettant de programmer automatiquement l'extinction du PC.

L'idée n'était donc **pas** de remplacer Windows.

Au contraire, le principe retenu est :

> **Sleep observe Windows et utilise les mécanismes de Windows plutôt que de les contourner.**

---

# 3. La vision

La vision du projet a progressivement évolué.

Au départ, on cherchait surtout à faire fonctionner :

> « Fermer le capot → éteindre le PC. »

Mais le projet est devenu plus intéressant lorsque nous avons ajouté la notion de **protection volontaire et réversible**.

L'utilisateur garde toujours le contrôle.

### Sleep lancé

```text
Je veux être protégé
        ↓
Je lance Sleep
        ↓
Sleep surveille
```

### Sleep non lancé

```text
Sleep n'est pas lancé
        ↓
Windows fonctionne normalement
```

Cela a conduit à une décision importante :

## ❌ Pas d'auto-démarrage

Sleep ne s'impose pas au système.

Il ne démarre pas automatiquement avec Windows.

Il n'intercepte pas les fermetures de capot lorsque l'utilisateur ne l'a pas demandé.

Cette décision rend le comportement beaucoup plus prévisible.

---

# 4. Le fonctionnement réel

Le cœur du système repose sur trois acteurs :

```text
┌─────────────┐
│   Windows   │
└──────┬──────┘
       │
       │ événement capot
       ↓
┌─────────────┐
│    Sleep    │
└──────┬──────┘
       │
       │ commande shutdown
       ↓
┌─────────────┐
│   Windows   │
│ shutdown.exe │
└─────────────┘
```

Sleep n'effectue donc pas lui-même le compte à rebours.

Lorsqu'il reçoit :

```text
CAPOT FERMÉ
```

il exécute conceptuellement :

```powershell
shutdown /s /t 20
```

si le délai configuré est de 20 secondes.

Windows devient alors responsable du compte à rebours.

---

# 5. La découverte importante : le capot

Une des difficultés majeures du projet a été de détecter correctement le capot.

Nous avons d'abord exploré les mécanismes classiques de Windows et les événements système.

Une piste importante était l'Event ID 42 et les mécanismes liés à la veille.

Mais elle n'était pas suffisamment fiable pour notre objectif.

La machine utilise :

> **Modern Standby / S0 Low Power Idle**

et non les anciens états S1/S2/S3.

On obtenait notamment :

```text
Veille (Mode faible consommation S0) Connecté au réseau
Mettre en veille prolongée
Démarrage rapide
```

Cela change beaucoup de choses dans le comportement du système.

---

# 6. La solution technique de détection

Nous avons finalement utilisé les notifications natives Windows de changement d'état du capot.

Le mécanisme repose notamment sur :

```text
GUID_LIDSWITCH_STATE_CHANGE
```

avec le GUID :

```text
BA3E0F4D-B817-4094-A2D1-D56379E6A0F3
```

Sleep enregistre une notification auprès de Windows grâce à :

```text
RegisterPowerSettingNotification
```

puis écoute :

```text
WM_POWERBROADCAST
```

et :

```text
PBT_POWERSETTINGCHANGE
```

L'état reçu est :

```text
0 → capot fermé
1 → capot ouvert
```

Cela nous a permis d'obtenir réellement :

```text
[LID] 🟢 CAPOT OUVERT
[LID] 🔴 CAPOT FERME
```

---

# 7. Une difficulté intéressante : Python ↔ Windows

La détection Windows a également posé des problèmes liés à `ctypes`.

Nous avons notamment rencontré :

```text
OverflowError:
int too long to convert
```

et un problème avec :

```text
ctypes.wintypes.HCURSOR
```

qui n'était pas disponible comme attendu.

Il a donc fallu adapter les déclarations Windows :

- GUID ;
- pointeurs ;
- types `ctypes` ;
- `WNDPROC` ;
- `DefWindowProcW` ;
- création de la fenêtre invisible ;
- boucle de messages Windows.

C'est une partie importante du projet parce qu'elle montre la différence entre :

> « écrire un programme Python »

et

> « faire communiquer Python directement avec une API native du système d'exploitation ».

---

# 8. Architecture finale

L'architecture finale s'est progressivement stabilisée autour de plusieurs couches.

```text
                         SLEEP
                           │
          ┌────────────────┴────────────────┐
          │                                 │
       FRONTEND                         BACKEND
          │                                 │
          │                                 │
    ┌─────┴─────┐              ┌────────────┼─────────────┐
    │           │              │            │             │
MainWindow  Dashboard      Controller   LidMonitor    Shutdown
    │           │              │            │             │
    │           │              │            │             │
    └───────────┘              │        Windows API       │
                               │                          │
                               ├── Config                 │
                               ├── History                │
                               └── LidWorker              │
                                                          │
                                                     shutdown.exe
```

### Structure

```text
Sleep/
│
├── app.py
├── start_sleep.py
│
├── backend/
│   ├── __init__.py
│   ├── config.py
│   ├── history.py
│   ├── shutdown.py
│   ├── lid_monitor.py
│   ├── lid_worker.py
│   └── controller.py
│
├── frontend/
│   ├── __init__.py
│   ├── main_window.py
│   ├── dashboard.py
│   └── styles.py
│
├── assets/
│   ├── zzz.png
│   └── zzz.ico
│
├── installer/
│   └── Sleep.iss
│
└── Sleep.spec
```

---

# 9. Rôle de chaque composant

## `lid_monitor.py`

C'est la couche la plus proche de Windows.

Son rôle :

> écouter le système Windows et détecter le changement d'état du capot.

Il ne décide pas quoi faire.

Il dit simplement :

```text
0 → fermé
1 → ouvert
```

---

## `lid_worker.py`

Le problème ici est que l'interface graphique ne doit pas être bloquée par la surveillance Windows.

Nous avons donc utilisé :

```python
QThread
```

Le `LidWorker` fait le pont entre :

```text
Windows
   ↓
lid_monitor
   ↓
QThread
   ↓
Qt Signals
   ↓
Interface / Controller
```

---

# 10. Le Controller : le cerveau

`controller.py` est le véritable cerveau logique.

Il reçoit :

```text
lid_state
```

et décide :

### Capot ouvert

```text
Si une extinction est programmée :
    annuler
Sinon :
    rien
```

### Capot fermé

```text
Protection désactivée ?
    ↓
    Oui → rien

Protection activée ?
    ↓
    Oui → programmer shutdown
```

Cela permet de séparer :

> **détection**

de

> **décision**

C'est une bonne pratique d'architecture.

---

# 11. Le système d'extinction

`shutdown.py` possède deux responsabilités.

### Programmer

```python
shutdown /s /t X
```

### Annuler

```python
shutdown /a
```

La grande décision architecturale a été de **ne pas créer notre propre timer d'extinction**.

Pourquoi ?

Parce que Windows possède déjà un système fiable pour cela.

Donc :

```text
Sleep
  │
  └── demande à Windows
             │
             ↓
       Windows compte
             │
             ↓
          extinction
```

C'est beaucoup plus propre que :

```text
Sleep
  │
  ├── timer Python
  ├── surveillance
  ├── logique d'extinction
  └── tentative de maintenir le processus actif
```

---

# 12. La configuration

`config.py` définit les paramètres par défaut :

```python
DEFAULT_CONFIG = {
    "enabled": True,
    "shutdown_delay_seconds": 10
}
```

Les paramètres sont stockés dans :

```text
%LOCALAPPDATA%\AutoShutdownPC\
```

avec notamment :

```text
config.json
history.json
```

Le dossier conserve volontairement son ancien nom `AutoShutdownPC`.

Cela n'empêche pas l'application de s'appeler **Sleep**.

---

# 13. L'historique

Sleep ne se contente pas d'exécuter des commandes.

Il garde également une trace des événements.

Par exemple :

```json
{
    "timestamp": "...",
    "reason": "lid_closed",
    "shutdown_delay_seconds": 20
}
```

Cela permet ensuite au dashboard d'afficher l'activité.

Il existe notamment une distinction entre :

```text
lid_closed
```

et :

```text
lid_closed_while_disabled
```

Cette distinction est utile parce qu'un événement de fermeture n'est pas forcément une extinction.

---

# 14. Le Dashboard

L'interface a également beaucoup évolué.

Le dashboard final permet notamment de voir :

### État de protection

```text
Protection active
```

avec son interrupteur.

### État du capot

```text
Capot ouvert
Capot fermé
```

### Dernière fermeture

Informations sur le dernier événement.

### Délai

L'utilisateur peut modifier :

```text
10 s
20 s
30 s
...
```

### Activité

Un graphique permet de visualiser les événements récents.

---

# 15. Pourquoi une interface graphique ?

Une commande comme :

```powershell
shutdown /s /t 20
```

fonctionne.

Mais ce n'est pas une application utilisable naturellement par tout le monde.

Le dashboard transforme donc une commande système en véritable outil :

```text
commande technique
      ↓
application compréhensible
```

C'est une différence importante dans un projet logiciel.

---

# 16. PySide6

L'interface utilise :

```text
PySide6
```

et Qt.

Cela permet notamment :

- fenêtre native ;
- widgets ;
- boutons ;
- signaux ;
- threads ;
- événements ;
- styles ;
- gestion propre de fermeture.

La version utilisée pendant le développement était :

```text
PySide6 6.11.2
```

---

# 17. Une difficulté importante : le lancement Python

Nous avons également rencontré :

```text
ModuleNotFoundError:
No module named 'frontend'
```

en lançant :

```powershell
python frontend\main_window.py
```

La raison était liée à la manière dont Python définit le chemin des modules lorsqu'un fichier est exécuté directement.

La bonne façon est :

```powershell
python -m frontend.main_window
```

depuis la racine du projet.

Cette difficulté est petite en apparence, mais elle est typique des projets Python structurés en packages.

---

# 18. Le problème Modern Standby

C'est probablement l'une des parties les plus intéressantes du projet.

Nous avons observé un comportement qui semblait parfois contradictoire :

```text
capot fermé
↓
Sleep semble ne pas éteindre
↓
capot rouvert
↓
commande annulée
```

Il fallait déterminer si :

### Hypothèse A

Sleep recevait immédiatement l'événement et Windows exécutait normalement la commande.

ou :

### Hypothèse B

Sleep recevait l'événement avec un délai lié au comportement du système et du Modern Standby.

Pour le déterminer, nous avons ajouté temporairement des timestamps :

```text
18:32:10.123
[LID WORKER] Événement capot reçu : 0

18:32:10.124
[CONTROLLER] handle_lid_change(0)

18:32:10.125
[SHUTDOWN] Envoi de la commande
```

Cela permettait de voir précisément la chronologie.

---

# 19. Le test décisif

Et finalement, nous avons obtenu le test le plus important.

### Test 1

```text
Protection active
Délai = 20 s
Capot fermé
Attente
```

Résultat :

> **Le PC s'est effectivement éteint.** ✅

Puis :

### Test 2

```text
Protection active
Délai = 20 s
Capot fermé
Attente ~5 s
Capot rouvert
```

Résultat :

> **Windows a indiqué que la commande avait été annulée.** ✅

Donc le comportement essentiel de Sleep est maintenant validé dans les deux directions.

---

# 20. Le mécanisme complet validé

On peut maintenant représenter Sleep ainsi :

```text
                   ┌───────────────┐
                   │  SLEEP LANCÉ  │
                   └───────┬───────┘
                           │
                           ▼
                    Surveillance
                      du capot
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
       CAPOT OUVERT                CAPOT FERMÉ
             │                           │
             │                     Protection ?
             │                           │
             │                  ┌────────┴────────┐
             │                  │                 │
             │                 ▼                 ▼
             │              NON                 OUI
             │               │                   │
             │               ▼                   ▼
             │             Rien            shutdown /s /t X
             │                                   │
             │                                   ▼
             │                              Windows timer
             │                                   │
             │                    ┌──────────────┴─────────────┐
             │                    │                            │
             │              Capot rouvert              Capot fermé
             │                    │                            │
             │                    ▼                            ▼
             │              shutdown /a                   extinction
             │                    │
             └────────────────────┘
```

---

# 21. Les difficultés rencontrées

Le projet a été beaucoup plus riche qu'un simple script.

### 1. Détection du capot

Il fallait trouver le bon mécanisme Windows.

### 2. Modern Standby

Le PC ne fonctionnait pas comme les anciens systèmes de veille classiques.

### 3. `ctypes`

Il fallait communiquer avec l'API Windows depuis Python.

### 4. Threading

Il fallait éviter de bloquer l'interface graphique.

### 5. Architecture

Le projet a progressivement été séparé en :

```text
monitor
worker
controller
shutdown
history
config
frontend
```

### 6. Packaging

Il fallait transformer le projet Python en :

```text
Sleep.exe
```

avec :

```text
PyInstaller
```

### 7. Installation

Il fallait ensuite transformer l'EXE en véritable installateur Windows :

```text
Sleep-Setup.exe
```

avec :

```text
Inno Setup
```

---

# 22. Packaging final

Le projet utilise :

```text
PyInstaller
```

pour construire :

```text
dist/Sleep.exe
```

Le fichier `.spec` indique notamment :

```text
frontend/main_window.py
```

comme point d'entrée.

Les packages :

```text
backend
frontend
```

sont inclus comme imports cachés.

Les ressources :

```text
assets/
```

sont également intégrées.

---

# 23. Installation

Le projet utilise ensuite :

```text
Inno Setup
```

pour créer :

```text
Sleep-Setup.exe
```

L'application est installée dans :

```text
%LOCALAPPDATA%\Programs\Sleep
```

et les données utilisateur restent séparées :

```text
%LOCALAPPDATA%\AutoShutdownPC
```

Cette séparation est importante.

Le programme peut donc être réinstallé sans nécessairement détruire les données utilisateur.

---

# 24. Une décision importante : pas de Task Scheduler

Une ancienne piste utilisait :

```text
Task Scheduler
```

avec :

```text
\AutoShutdownOnLidClose
```

Mais cette approche n'était pas retenue dans l'architecture finale.

Le projet s'est finalement orienté vers :

```text
application active
        ↓
notification Windows native
```

plutôt que :

```text
Task Scheduler
        ↓
script externe
```

Cela rend le comportement plus directement contrôlé par Sleep.

---

# 25. Ce que Sleep n'est pas

Il est important de définir clairement le périmètre.

Sleep n'est pas :

- un antivirus ;
- un gestionnaire d'alimentation complet ;
- un remplacement des paramètres Windows ;
- un outil de veille ;
- un logiciel qui force l'extinction en permanence ;
- un programme qui démarre automatiquement ;
- un service système obligatoire.

Sleep est simplement :

> **une couche de protection volontaire autour de la fermeture du capot.**

---

# 26. Pourquoi ce projet est intéressant dans la vie réelle

C'est probablement la partie la plus importante pour présenter le projet.

Le problème paraît petit.

Mais il correspond à une situation réelle :

```text
ordinateur portable
+
travail important
+
transport
+
fatigue
+
fermeture du capot
+
oubli
```

Un utilisateur peut fermer son ordinateur en pensant :

> « Je vais le reprendre plus tard. »

Mais il peut finalement :

- le transporter ;
- oublier qu'il est encore actif ;
- le laisser plusieurs heures ;
- le retrouver avec une batterie fortement déchargée ;
- éventuellement avoir des applications ou tâches encore ouvertes.

Sleep propose une réponse extrêmement simple :

> **Je lance Sleep quand j'en ai besoin, et je laisse l'application me protéger.**

---

# 27. L'intérêt énergétique

Le projet possède également un intérêt énergétique.

Un ordinateur portable qui reste actif inutilement consomme de l'énergie.

À l'échelle d'un individu, cela paraît faible.

Mais le principe est intéressant :

```text
petite économie
×
nombre important d'utilisations
=
réduction de consommation inutile
```

Sleep n'est évidemment pas une solution mondiale à la consommation énergétique informatique.

Mais c'est un exemple concret de la manière dont une petite automatisation peut éviter une consommation inutile.

---

# 28. L'intérêt ergonomique

Il existe également une dimension UX.

Windows possède énormément de paramètres.

Un utilisateur peut configurer :

```text
fermeture du capot → veille
```

mais cela ne correspond pas forcément à toutes les situations.

Sleep ajoute une logique contextuelle :

> **Quand j'ai besoin de protection, j'active Sleep.**

Cela évite de modifier constamment les paramètres Windows.

---

# 29. L'intérêt pédagogique

Pour toi, ce projet est également beaucoup plus important qu'un simple programme terminé.

Il t'a fait traverser plusieurs niveaux.

### Niveau 1 — Python

```text
fonctions
classes
modules
JSON
fichiers
```

### Niveau 2 — architecture

```text
backend
frontend
controller
worker
```

### Niveau 3 — programmation événementielle

```text
événement
   ↓
callback
   ↓
signal
   ↓
traitement
```

### Niveau 4 — multithreading

```text
QThread
```

### Niveau 5 — OS

```text
Windows API
WM_POWERBROADCAST
GUID
shutdown.exe
```

### Niveau 6 — packaging

```text
PyInstaller
```

### Niveau 7 — distribution

```text
Inno Setup
```

C'est donc un véritable petit projet d'ingénierie logicielle.

---

# 30. Ce que le projet démontre techniquement

À la fin, Sleep démontre que tu sais construire une chaîne complète :

```text
PROBLÈME RÉEL
     ↓
CONCEPTION
     ↓
API SYSTÈME
     ↓
BACKEND
     ↓
LOGIQUE MÉTIER
     ↓
THREADING
     ↓
INTERFACE
     ↓
PERSISTANCE
     ↓
TESTS
     ↓
EXÉCUTABLE
     ↓
INSTALLATEUR
```

C'est beaucoup plus intéressant sur un portfolio qu'un simple :

> « J'ai fait une interface Python. »

---

# 31. État final du projet

À ce stade :

| Élément | État |
|---|---|
| Détection du capot | ✅ |
| Capot ouvert | ✅ |
| Capot fermé | ✅ |
| Protection activable/désactivable | ✅ |
| Délai configurable | ✅ |
| Extinction Windows | ✅ |
| Annulation avec réouverture | ✅ |
| Historique | ✅ |
| Graphique | ✅ |
| Dashboard | ✅ |
| Thread de surveillance | ✅ |
| Configuration persistante | ✅ |
| Icône | ✅ |
| PyInstaller | ✅ |
| Installateur Inno Setup | ✅ |
| Auto-start | ❌ volontairement absent |
| Task Scheduler | ❌ abandonné |

---

# 32. Architecture conceptuelle finale

Si tu devais l'expliquer devant un professeur, tu peux résumer l'architecture ainsi :

> **« Sleep est une application événementielle Windows. Elle utilise les notifications natives de changement d'état du capot pour détecter sa fermeture. Un worker Qt transmet l'événement au contrôleur, qui applique la logique métier selon l'état de protection et le délai configuré. Lorsque la protection est active, le contrôleur demande à Windows de programmer une extinction avec `shutdown.exe`. Si le capot est rouvert avant l'expiration du délai, Sleep demande à Windows d'annuler cette extinction. L'interface PySide6 permet de contrôler et visualiser le système, tandis qu'un historique JSON conserve les événements. Le projet est ensuite empaqueté avec PyInstaller et distribué avec Inno Setup. »**

---

# 33. La philosophie du projet

Et finalement, je pense que c'est ça qui donne son identité au projet.

**Sleep ne cherche pas à être compliqué.**

Il part d'une action extrêmement simple :

> fermer un ordinateur portable.

Et transforme cette action en un événement intelligent :

```text
CAPOT
  ↓
ÉVÉNEMENT
  ↓
DÉCISION
  ↓
ACTION
  ↓
PROTECTION
```

C'est une bonne illustration d'une idée importante en ingénierie :

> **Un bon système n'est pas nécessairement celui qui fait le plus de choses. C'est celui qui répond proprement à un problème réel avec le minimum de complexité nécessaire.**

---

# 34. Conclusion

Le projet **Sleep** a commencé comme une idée très simple d'automatisation.

Il est devenu un projet complet mettant en jeu :

**Python + PySide6 + Windows API + événements système + threading + JSON + PyInstaller + Inno Setup.**

La difficulté principale n'était finalement pas d'écrire :

```python
shutdown /s /t 20
```

La vraie difficulté était de construire **tout ce qui se trouve autour** :

```text
Comment détecter correctement le capot ?
Comment communiquer avec Windows ?
Comment éviter de bloquer l'interface ?
Comment gérer l'annulation ?
Comment conserver l'historique ?
Comment rendre le système compréhensible ?
Comment transformer le prototype en application ?
Comment distribuer l'application ?
```

Et c'est précisément ce parcours qui fait de **Sleep** un vrai projet d'ingénierie, et pas simplement un script.

**De l'idée → au prototype → à l'architecture → aux tests → à l'application → à l'installateur.**

C'est ça, le parcours complet de Sleep.