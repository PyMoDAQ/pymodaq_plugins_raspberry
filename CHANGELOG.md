# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Versioning Sémantique](https://semver.org/lang/fr/) :
`MAJEUR.MINEUR.CORRECTIF`.

- **MAJEUR** : refonte ou rupture de compatibilité
- **MINEUR** : nouvelle fonctionnalité
- **CORRECTIF** : correction de bug ou ajustement mineur

La version courante est également disponible dans [`version.json`](version.json).

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
