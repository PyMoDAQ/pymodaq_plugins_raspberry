# Serveur d'acquisition et de pilotage Raspberry Pi (PyMoDAQ)

Ce dossier contient le code serveur qui tourne sur la Raspberry Pi. Il fait
l'interface entre le matériel (capteurs I2C, actionneurs) et le réseau via un
serveur ZeroMQ, permettant à un client PyMoDAQ distant de piloter l'ensemble
via des trames JSON.

> Ce dossier est un ajout au plugin et n'est **pas packagé** : il ne fait pas
> partie de la distribution Python du plugin PyMoDAQ et ne le modifie pas.

## 🏗️ Architecture en couches

Le serveur est découpé selon une topologie où **chaque maillon est une classe
interchangeable** derrière une interface, sauf le `main` qui les assemble :

```
   ZmqServer  ──►  JsonRequestHandler  ──►  HardwareBackend
  (transport)        (gestion requêtes)     (comm. composants)
        ▲                   ▲                       ▲
   ITransport        IRequestHandler         IHardwareBackend
                  assemblés par main.py (boucle)
```

- **`transport/`** — communication avec le client PyMoDAQ.
  - `base.py` : interface `ITransport`.
  - `zmq_server.py` : implémentation `ZmqServer` (ZeroMQ ROUTER). Ne gère que le
    réseau et le framing ; remplaçable par un autre transport.
- **`handlers/`** — gestion des requêtes.
  - `base.py` : interface `IRequestHandler`.
  - `json_handler.py` : implémentation `JsonRequestHandler` (décodage + routage
    JSON). **Aucun accès matériel** : tout est délégué au backend.
- **`hardware/`** — communication avec les composants.
  - `base.py` : interface `IHardwareBackend`.
  - `backend.py` : implémentation `HardwareBackend` (capteurs + actionneurs).
  - `sensors.py` : pilotes de capteurs et `SENSOR_DRIVER_REGISTRY`
    (`AHT10`, `TMP102`, `EMC2101`, `PT-100`, `SIMULE`).
  - `actuators.py` : pilotes d'actionneurs et `ACTUATOR_DRIVER_REGISTRY`
    (`PWM`, `DIGITAL`), plus le gestionnaire `CActuatorManager`.
  - `scanner.py` : détection des adresses I2C.
- **`config.py`** — description du banc de test (broches, capteurs, actionneurs).
  C'est le **seul fichier à adapter** d'un banc à l'autre.
- **`config_examples/`** — configurations prêtes à l'emploi pour d'autres bancs
  (ex. `config_pizero.py` : actionneurs tout-ou-rien + sonde PT100).
- **`main.py`** — point d'entrée : instancie et câble les trois couches.

### Adapter le serveur à un banc

Toute la différence entre deux bancs de test tient dans
`config.py` : un capteur choisit son pilote via le champ `driver` (clé de
`SENSOR_DRIVER_REGISTRY`), un actionneur via son propre champ `driver`
(`PWM` ou `DIGITAL`, clé de `ACTUATOR_DRIVER_REGISTRY`). Ajouter un nouveau
matériel = créer une classe de pilote et l'enregistrer dans le registre
correspondant ; ni le transport, ni la gestion des requêtes, ni le `main`
ne changent.

Pour repartir d'un banc existant, copiez le fichier voulu de `config_examples/`
vers `config.py`.

## 🛠️ Prérequis et installation

> **Installation rapide** : le wiki DAP (https://wiki-plugins-dap-pymodaq.github.io/,
> page *Downloads*) fournit un package qui réalise les étapes ci-dessous et installe
> le serveur comme service démarrant avec la carte (`sudo bash install.sh`).

1. **Activer l'I2C** : `sudo raspi-config` → Interfacing Options → I2C.
2. **Démon pigpio** (pilotage matériel des GPIO) :
   ```bash
   sudo apt-get update
   sudo apt-get install pigpio python3-pigpio
   sudo systemctl enable pigpiod
   sudo systemctl start pigpiod
   ```
3. **Dépendances Python** :
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## 🚀 Lancement

```bash
python main.py              # port 5555
python main.py --port 5556  # autre port (à reporter dans le TOML côté PC)
python main.py --verbose    # affiche aussi chaque requête reçue et sa réponse
```

> **Mode simulation** : si le bus I2C ou le démon pigpio sont inaccessibles
> (ex. exécution sur un PC), le serveur bascule automatiquement en simulation
> (bus I2C factice, actionneurs simulés qui mémorisent leur consigne) pour tester
> la communication réseau sans la Raspberry Pi.

### Démonstration sans Raspberry (Windows, macOS, Linux)

1. Sur le PC, avec PyMoDAQ installé : `pip install pyzmq`, puis `python src_raspberry/main.py` (log `Mode simulation activé`).
2. Copier `src/pymodaq_plugins_raspberry/resources/config_demo.toml` vers `~/.pymodaq/config_raspberry.toml`.
3. Dans le Dashboard, ajouter `ViewRasp` et `MoveRasp`, cocher les composants du viewer, puis initialiser.
4. Régler `Resistance` à 255 : les températures montent ; régler `Ventilateur` à 255 : elles redescendent.
5. Arrêter le serveur avec Ctrl+C ; serveur arrêté, les voies passent en `nan` avec un message d'erreur visible.

## 📡 Protocole de communication (JSON)

Le serveur écoute des trames JSON sur un socket ZeroMQ (ROUTER) port `5555`.
Quatre types de requêtes : `scan`, `AQ`, `AQ-MULTI` et `PI`. Toutes les réponses
ont la même forme : `{"state": "ACK" | "ERROR", "value": <valeur ou message>}`.

### Scan du matériel
```json
{"type": "scan"}
```
Réponse : `{"state": "ACK", "value": {"actuator": [...], "detector": [...]}}`.

### Acquisition (`AQ`)
```json
{"type": "AQ", "register": "add", "add": "0x38", "channel": "temp"}
{"type": "AQ", "register": "pin", "pin": 18}
```

### Pilotage (`PI`)
```json
{"type": "PI", "register": "pin", "pin": 18, "value": 128}
```
Les actionneurs sont pilotés par leur broche GPIO. Un pilotage par adresse I2C
(`"register": "add"`) est refusé : aucun pilote d'actionneur I2C n'existe.

### Acquisition multiple (`AQ-MULTI`)
```json
{
  "type": "AQ-MULTI",
  "components": [
    {"register": "add", "add": "0x38", "channel": "hum"},
    {"register": "pin", "pin": 18}
  ]
}
```
Les valeurs sont renvoyées dans l'ordre demandé. Une lecture ratée est remplacée
à sa place par sa propre réponse d'erreur, par exemple :
`{"state": "ACK", "value": [45.2, {"state": "ERROR", "value": "Capteur introuvable"}]}`.
Le plugin la journalise et l'affiche en `nan`.
