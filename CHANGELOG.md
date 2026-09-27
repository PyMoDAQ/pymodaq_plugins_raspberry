# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Versioning Sémantique](https://semver.org/lang/fr/) :
`MAJEUR.MINEUR.CORRECTIF`.

- **MAJEUR** : refonte ou rupture de compatibilité
- **MINEUR** : nouvelle fonctionnalité
- **CORRECTIF** : correction de bug ou ajustement mineur

La version courante est également disponible dans [`version.json`](version.json).

## [5.5.10] - 2026-09-27

### Corrigé
- `src_raspberry/main.py` : le port d'écoute, jusqu'ici codé en dur à 5555, se
  choisit avec `python main.py --port <port>` (5555 par défaut). README mis à jour.

## [5.5.9] - 2026-09-27

### Corrigé
- `DAQ_0DViewer_ViewRasp.grab_data` : les listes d'adresses et de broches étaient
  prises par position (`access_variables[0]`, `[1]`) et suivaient donc l'ordre
  des clés du TOML. Si `pin` était écrit avant `address`, les broches partaient
  comme des adresses et toutes les voies valaient `nan`. Une clé d'accès
  supplémentaire décalait aussi les libellés. Les adresses et les broches sont
  désormais lues par leur nom, dans l'ordre de réponse de la carte (adresses puis
  broches).

## [5.5.8] - 2026-09-27

### Corrigé
- `DAQ_Move_MoveRasp` : suppression de l'import inutilisé
  `from pint.facets.numpy import quantity`, qui visait un module interne de pint,
  susceptible de disparaître d'une version à l'autre. `ini_attributes` appelait
  `update_move_settings` une fois par actionneur avec le même axe : un seul appel
  suffit.

## [5.5.7] - 2026-09-27

### Corrigé
- Compatibilité avec Python 3.8 et 3.9, déclarés par `pyproject.toml` et par
  PyMoDAQ 5 (`requires-python >= 3.8`) :
  - `hardware/link_zmq.py` : `from __future__ import annotations`. Les annotations
    `list[str] | list[int]` et `str | int` étaient évaluées à la définition des
    méthodes et levaient une `TypeError` à l'import avant Python 3.10.
  - `hardware/config_components.py` : l'union de dictionnaires `a | b` (Python 3.9+)
    est remplacée par `{**a, ...}`.

## [5.5.6] - 2026-09-27

### Corrigé
- `hardware/link_zmq.py` : le bloc `__main__` contenait l'adresse de développement
  `172.17.50.41` et pilotait une broche. Il devient une vérification de connexion
  en lecture seule, qui prend l'adresse en argument :
  `python -m pymodaq_plugins_raspberry.hardware.link_zmq <ip> [port]`.

## [5.5.5] - 2026-09-27

### Corrigé
- `hardware/link_zmq.py` : les validations d'entrée d'`open()` (adresse IP absente)
  et de `multi_acquisition()` (ni adresse ni broche) lèvent une `ValueError`
  explicite. Les `assert` utilisés jusqu'ici disparaissent sous `python -O`.

## [5.5.4] - 2026-09-27

### Corrigé
- `config_template.toml` : `address_Rasp` passe de `192.158.235.2`, adresse
  publique issue d'une coquille, à `192.168.235.2`, adresse de réseau privé.

## [5.5.3] - 2026-09-27

### Ajouté
- `tests/test_link_zmq.py` : quatre tests de la chaîne sans matériel. Un faux
  serveur ROUTER tourne dans un thread, et un vrai `ZMQLink` y est branché. Les
  tests couvrent une acquisition, un pilotage, une réponse d'erreur (lecture ratée
  en `nan`, pilotage refusé) et un timeout (carte muette : erreur en moins de 2 s,
  sans gel). Écrits avec `unittest`, ils ne demandent aucun paquet supplémentaire :
  `python -m unittest discover -s tests -p "test_link_zmq.py"`. Ils sont aussi
  exécutés par pytest en CI. Un appel bloqué fait échouer le test au bout de 5 s
  au lieu de figer la suite. Vérifié : réintroduire la sentinelle `-1` ou retirer
  `RCVTIMEO` fait échouer les tests.

## [5.5.2] - 2026-09-27

### Ajouté
- `src_raspberry/README.md` : section « Démonstration sans Raspberry » en cinq
  étapes (lancer le serveur en simulation, installer la configuration de démo,
  initialiser les plugins, piloter la résistance et le ventilateur, montrer la
  réaction à un serveur arrêté).

## [5.5.1] - 2026-09-27

### Ajouté
- `resources/config_demo.toml` : configuration de démonstration côté PC, alignée
  sur le banc par défaut de `src_raspberry/config.py`. Adresse `127.0.0.1`,
  ventilateur (broche 18) et résistance (broche 23), cinq capteurs I2C (0x48,
  0x49, 0x4B, 0x4A, 0x38). À copier vers `~/.pymodaq/config_raspberry.toml`. Avec
  la configuration du modèle, les composants n'existent pas sur la carte simulée
  et toutes les voies valent `nan`.

## [5.5.0] - 2026-09-27

### Ajouté
- `src_raspberry/hardware/sensors.py` : `CThermalModel`, un modèle thermique du
  premier ordre utilisé **uniquement en simulation**. La résistance chauffe le banc
  (+40 °C à pleine chauffe, constante de temps de 60 s), le ventilateur accélère
  les pertes (plateau ramené vers +12 °C), l'ambiance dérive lentement
  (22 °C ± 0,5 °C) et chaque mesure porte un léger bruit. L'humidité relative
  baisse quand l'air se réchauffe.
- `CDriverSimule` : relié au modèle, il renvoie des valeurs qui évoluent et
  réagissent aux actionneurs, au lieu de tirages aléatoires indépendants. Sans
  modèle, il garde l'ancien comportement.
- `src_raspberry/hardware/backend.py` : en simulation, les capteurs simulés
  partagent ce modèle, alimenté par les consignes des actionneurs (repérés par leur
  nom : `resistance`, `ventilateur`). Le chemin matériel réel n'est pas modifié.
- `src_raspberry/config.py` : clé optionnelle `sim_coupling` par capteur, qui règle
  sa proximité avec la résistance (0 : air ambiant, 1 : au contact).

## [5.4.24] - 2026-09-27

### Supprimé
- `src_raspberry/handlers/json_handler.py` : suppression de `PI-MULTI` (P1.4). Aucun
  appelant côté plugin, pas d'exemple documenté, et le pilotage d'un seul
  actionneur par déplacement PyMoDAQ n'en a pas l'usage. Une requête `PI-MULTI`
  reçoit désormais « Type de requête inconnu ».
- `src_raspberry/README.md` : section protocole mise à jour. Elle décrit quatre types
  de requêtes (`scan`, `AQ`, `AQ-MULTI`, `PI`) et une forme de réponse unique, le
  pilotage par broche uniquement, et la place d'une erreur dans une réponse
  `AQ-MULTI`.

## [5.4.23] - 2026-09-27

### Corrigé
- Pilotage par adresse I2C (P1.1) : le plugin savait construire une requête
  `PI` par adresse, mais la carte l'ignorait et répondait « Format invalide pour
  'pin' ». La carte n'a en effet aucun pilote d'actionneur I2C :
  `CActuatorManager` indexe les actionneurs par broche GPIO, et le champ `address`
  de `CActuatorConfig` n'est jamais utilisé.
  - `src_raspberry/handlers/json_handler.py` : un `PI` avec `register: "add"`
    reçoit une erreur explicite (« Pilotage par adresse I2C non supporté »).
  - `hardware/link_zmq.py` : `pilotage(value, pin)` ne pilote plus que par broche,
    la branche adresse est retirée.
  - `DAQ_Move_MoveRasp.move_value` : pilote l'actionneur par sa broche. Un
    actionneur sans broche produit une erreur visible au lieu d'une requête vouée
    à l'échec. L'attribut devenu inutile `name_access_variables` est retiré.
  - `config_template.toml` : le commentaire indique qu'un actionneur est piloté
    par sa broche (`address = "None"`).

## [5.4.22] - 2026-09-27

### Corrigé
- `DAQ_Move_MoveRasp.move_value` : un pilotage refusé ou sans réponse (broche
  inconnue, timeout) n'apparaissait que dans le journal. Il s'affiche désormais
  aussi en statut dans PyMoDAQ, comme pour le viewer.

## [5.4.21] - 2026-09-27

### Corrigé
- `DAQ_0DViewer_ViewRasp.grab_data` : une acquisition sans aucun composant coché
  levait `TypeError: Data should be an non-empty list` (PyMoDAQ refuse les données
  vides). Le viewer émet désormais une voie `nan` intitulée
  « no component selected » et affiche un statut invitant à cocher un composant.

## [5.4.20] - 2026-09-27

### Corrigé
- `DAQ_0DViewer_ViewRasp.grab_data` : quand toute l'acquisition échoue (carte
  injoignable, timeout, réponse `ERROR`), le viewer émettait une seule valeur `0`,
  quel que soit le nombre de voies affichées. Il émet désormais une valeur `nan`
  par voie, et le message d'erreur s'affiche en statut dans PyMoDAQ
  (`Update_Status`), en plus du journal.

## [5.4.19] - 2026-09-27

### Corrigé
- `hardware/link_zmq.py`, `multi_acquisition()` : le message d'erreur renvoyé par la
  carte était écrasé par `-1` avant d'être journalisé (le journal affichait toujours
  `READ ERROR - -1`) (P0.3). Il est désormais journalisé avec le composant concerné,
  par exemple `READ ERROR - add 0x99 : Capteur introuvable`.
- Une lecture ratée vaut `nan` au lieu de `-1` (une température plausible) : un
  capteur en panne ne ressemble plus à un capteur qui mesure (P1.3). Vérifié :
  `DataFromPlugins` et l'afficheur `Viewer0D` acceptent `nan`.

## [5.4.18] - 2026-09-27

### Corrigé
- `hardware/link_zmq.py` : `get_link_status()` renvoyait toujours vrai, car
  `connect()` est asynchrone en ZeroMQ et n'échoue jamais (P0.2). `open()` envoie
  désormais une requête `scan` : le lien n'est considéré comme établi que si la
  Raspberry répond `ACK` avant le timeout.
- `DAQ_0DViewer_ViewRasp.ini_detector`, `DAQ_Move_MoveRasp.ini_stage` : si la
  carte ne répond pas, l'initialisation échoue en 2 s avec un message citant
  l'adresse et le port tentés, au lieu d'afficher « Initialized » puis de geler à
  la première acquisition.
- `close()` des deux plugins : protégé quand l'initialisation a échoué
  (`controller` à `None`).

## [5.4.17] - 2026-09-27

### Corrigé
- `hardware/link_zmq.py` : le plugin gelait (interface PyMoDAQ figée) quand la
  Raspberry ne répondait pas, car `recv()` bloquait sans limite (P0.1). Le socket
  DEALER reçoit désormais `RCVTIMEO`/`SNDTIMEO` (2000 ms par défaut) et `LINGER=0`.
  Un timeout renvoie `{"state": "ERROR", "value": "TIMEOUT - ..."}` au lieu de
  bloquer, et le socket est recréé : une réponse tardive n'est plus prise pour la
  réponse à la requête suivante.
- `multi_acquisition()` : une réponse `ERROR` de la carte (ou un timeout) est
  renvoyée sous forme de message `"ERROR : ..."`. Elle n'est plus parcourue
  caractère par caractère comme une liste de valeurs.
- `config_template.toml` : nouvelle clé `timeout_ms` dans `[Raspberry]`,
  transmise à `ZMQLink` par `DAQ_0DViewer_ViewRasp` et `DAQ_Move_MoveRasp`.

## [5.4.16] - 2026-09-27

### Corrigé
- `hardware/link_zmq.py` : `close()` ferme le socket sans attente (`linger=0`) et
  termine le contexte ZeroMQ ; `open()` libère le socket et le contexte précédents
  avant d'en créer de nouveaux. Ouvrir et fermer plusieurs fois le lien ne fuit
  plus. `close()` peut être appelé plusieurs fois sans erreur.
- `hardware/link_zmq.py` : `print()` remplacé par le logger PyMoDAQ.

## [5.4.15] - 2026-09-27

### Corrigé
- `src_raspberry/handlers/json_handler.py` : la réponse à `scan` passe par `_Ack`,
  comme toutes les autres : `{"state": "ACK", "value": {"actuator": [...], "detector": [...]}}`.
  Toutes les requêtes ont désormais une seule forme de réponse (P1.2). Aucun code
  du plugin ne consommait `scan` sous l'ancienne forme.

## [5.4.14] - 2026-09-27

### Corrigé
- `src_raspberry/hardware/backend.py`, `actuators.py` : la bascule en simulation est
  journalisée en WARNING avec sa cause (`smbus2` absent, bus I2C introuvable, pigpio
  non installé ou démon injoignable). Sur une vraie Raspberry, une dépendance
  manquante ne passe plus inaperçue derrière des valeurs simulées.

## [5.4.13] - 2026-09-27

### Corrigé
- `src_raspberry/transport/zmq_server.py` : Ctrl+C n'arrêtait pas le serveur, bloqué
  dans un `recv_multipart()` sans fin. La boucle attend désormais par `poll()` de
  500 ms et rend la main à Python entre deux attentes.
- Le thread de surveillance des connexions se termine sans trace d'erreur quand
  `stop()` ferme son socket (`ZMQError: not a socket`).

## [5.4.12] - 2026-09-27

### Corrigé
- `src_raspberry/hardware/actuators.py` : en simulation, les actionneurs relisaient
  toujours `1` (conversion d'un `MagicMock`). Un `CSimulatedPi` mémorise désormais
  la consigne de chaque broche : régler le ventilateur à 200 relit 200.

## [5.4.11] - 2026-09-27

### Corrigé
- `src_raspberry/hardware/actuators.py` : `pigpio` devient optionnel. Son absence
  (PC, Windows) bascule les actionneurs en simulation au lieu de faire échouer le
  démarrage. `main.py` démarre désormais en simulation sous Windows.

## [5.4.10] - 2026-09-27

### Corrigé
- `src_raspberry/hardware/backend.py`, `scanner.py` : import de `smbus2` rendu local.
  `smbus2` dépend de `fcntl` (Unix uniquement) : sous Windows, l'import échouait au
  chargement du module et `main.py` ne démarrait pas. L'échec d'import déclenche
  désormais le mode simulation, comme un bus I2C absent.

## [5.4.9] - 2026-09-27

### Corrigé
- `version.json` et `CHANGELOG.md` resynchronisés avec l'historique git : les
  versions 5.4.5 à 5.4.8 avaient été commitées sans mise à jour de ces fichiers.

## [5.4.8] - 2026-06-30

### Corrigé
- `DAQ_Move_MoveRasp` : gestion des unités — la mise à l'échelle PyMoDAQ
  (`set_position_with_scaling`) est réactivée, le paramètre `scaling` est masqué,
  et `get_actuator_value` renvoie un `DataActuator` avec l'unité de l'axe.
- `config_template.toml` : unités par défaut corrigées (`""` pour l'actionneur,
  `"V"` pour le détecteur).

## [5.4.7] - 2026-06-30

### Corrigé
- `DAQ_Move_MoveRasp` : les bornes de l'axe sont retrouvées par `title` (nom
  d'axe affiché) au lieu de `name`.

## [5.4.6] - 2026-06-29

### Corrigé
- `move_home` envoie un `DataActuator` au lieu d'un entier nu.
- Texte de retour d'initialisation simplifié (`"Initialized"`).

## [5.4.5] - 2026-06-29

### Modifié
- Retours de relecture de la pull request : modules renommés en `link_zmq.py` et
  `config_components.py`, `DAQ_Move_MoveRasp` passé en multi-axes
  (`is_multiaxes = True`), mise à jour des bornes factorisée dans
  `update_move_settings`.

## [5.4.4] - 2026-06-10

### Modifié
- `README.rst` : ajout d'une note précisant que le viewer PiCamera n'est disponible
  que sur Linux/Raspberry (dépendance `picamera2`).
- Documentation et commentaires nettoyés de références internes peu compréhensibles
  hors du contexte de développement.

## [5.4.3] - 2026-06-10

### Corrigé
- Installation impossible sur Windows/macOS : la dépendance `picamera2` (qui tire
  `python-prctl`, Linux-only) est désormais conditionnée à Linux via un marqueur
  d'environnement (`picamera2; platform_system == "Linux"`). La machine de contrôle
  peut installer le plugin (actionneur/détecteur distants) ; le viewer PiCamera
  reste disponible sur le Raspberry.

## [5.4.2] - 2026-06-10

### Modifié
- `README.rst` réécrit du point de vue de l'utilisateur du plugin (contrôle d'un
  dispositif expérimental via un Raspberry). Mise en avant des trois axes
  d'adaptabilité : communication PyMoDAQ ⇄ Raspberry, communication
  Raspberry ⇄ composants, et ajout de nouvelles requêtes JSON des deux côtés.

## [5.4.1] - 2026-06-10

### Corrigé
- `CONTRIBUTING.md` : convention de tags alignée sur l'historique du dépôt
  (`5.0.0`, `5.0.1`) — les tags de production sont au format `MAJEUR.MINEUR.CORRECTIF`
  sans préfixe `v`.

## [5.4.0] - 2026-06-10

### Ajouté
- Documentation du plugin dans `README.rst` : liste des instruments
  (`MoveRasp`, `ViewRasp`, `picamera`) et description du serveur Raspberry
  (`src_raspberry/`).

### Modifié
- `README.rst` : mise à jour des auteurs et de la version PyMoDAQ requise (>= 5).

### Vérifié
- Conformité à `tests/test_plugin_package_structure.py` (conventions de nommage et
  méthodes obligatoires des plugins `DAQ_Move_MoveRasp` et `DAQ_0DViewer_ViewRasp`).

## [5.3.0] - 2026-06-10

### Ajouté
- `hardware/Link_PMQ.py` : client `ZMQLink` (lien ZeroMQ DEALER vers le serveur Raspberry).
- `hardware/Config_Components.py` : lecture des composants (actionneurs/détecteurs)
  depuis le fichier de configuration TOML.
- `daq_move_plugins/daq_move_MoveRasp.py` : plugin actionneur `DAQ_Move_MoveRasp`.
- `daq_viewer_plugins/plugins_0D/daq_0Dviewer_ViewRasp.py` : plugin détecteur
  `DAQ_0DViewer_ViewRasp`.

### Modifié
- `resources/config_template.toml` : section de configuration `[Raspberry]`.
- `pyproject.toml` : ajout de la dépendance `pyzmq` (requise par `ZMQLink`).
- Le plugin `DAQ_2DViewer_PiCamera` n'est pas modifié.

### Corrigé
- Remplacement des f-strings à guillemets imbriqués identiques (`f"{d["k"]}"`),
  valides seulement en Python 3.12+, par une forme compatible Python 3.8+.

## [5.2.0] - 2026-06-10

### Ajouté
- Pilote de capteur `PT-100` (sonde de température via CAN ADS1115), enregistré
  dans `SENSOR_DRIVER_REGISTRY` (import de la dépendance Adafruit isolé localement).
- Pilotes d'actionneurs **interchangeables** derrière l'interface `CActuatorDriver`,
  sélectionnés par le champ `driver` de la configuration, et enregistrés dans
  `ACTUATOR_DRIVER_REGISTRY` :
  - `PWM` — pilotage en rapport cyclique ;
  - `DIGITAL` — pilotage tout-ou-rien.
- `config_examples/config_pizero.py` : configuration d'exemple d'un banc tout-ou-rien
  avec sonde PT100.

### Modifié
- `CActuatorManager` instancie désormais le pilote adapté à chaque actionneur
  (au lieu d'un pilotage PWM codé en dur), permettant de mélanger des modes de
  pilotage différents sur un même banc.
- `CActuatorConfig` accepte un champ `driver` (défaut `PWM`) ; `pwm_frequency`
  devient optionnel (inutile pour les actionneurs tout-ou-rien).
- `config.py` documente le choix du pilote par actionneur.

### Supprimé
- Moniteur de sécurité (`safety_monitor`) : retiré car il lisait des constantes de
  configuration inexistantes et n'était jamais démarré par le `main`.

### Corrigé
- Construction de la cartographie des capteurs unifiée dans `HardwareBackend`
  (suppression d'une fonction morte aux références non importées).

## [5.1.0] - 2026-06-10

### Ajouté
- `version.json` à la racine (version du projet, SemVer).
- `CHANGELOG.md` et `CONTRIBUTING.md` (stratégie de branches/tags, processus de version).
- Serveur Raspberry dans `src_raspberry/` selon une topologie en couches, chaque
  maillon étant une **classe interchangeable** derrière une interface :
  - `ITransport` / `ZmqServer` — communication avec le client PyMoDAQ (ZeroMQ) ;
  - `IRequestHandler` / `JsonRequestHandler` — décodage et routage des requêtes JSON,
    sans aucun accès matériel ;
  - `IHardwareBackend` / `HardwareBackend` — communication avec les capteurs et actionneurs ;
  - `main.py` — boucle principale qui assemble les trois couches.

### Modifié
- La gestion des requêtes et la communication matérielle sont deux entités distinctes
  (`JsonRequestHandler` d'un côté, `HardwareBackend` de l'autre).
- Le transport ZeroMQ est isolé de la logique de framing/décodage des messages.
