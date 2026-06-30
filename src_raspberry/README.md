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
python main.py
```

> **Mode simulation** : si le bus I2C ou le démon pigpio sont inaccessibles
> (ex. exécution sur un PC), le serveur bascule automatiquement en simulation
> (objets `MagicMock`) pour tester la communication réseau sans la Raspberry Pi.

## 📡 Protocole de communication (JSON)

Le serveur écoute des trames JSON sur un socket ZeroMQ (ROUTER) port `5555`.

### Scan du matériel
```json
{"type": "scan"}
```

### Acquisition (`AQ`)
```json
{"type": "AQ", "register": "add", "add": "0x38", "channel": "temp"}
{"type": "AQ", "register": "pin", "pin": 18}
```

### Pilotage (`PI`)
```json
{"type": "PI", "register": "pin", "pin": 18, "value": 128}
```

### Modes multiples (`AQ-MULTI`, `PI-MULTI`)
```json
{
  "type": "AQ-MULTI",
  "components": [
    {"register": "add", "add": "0x38", "channel": "hum"},
    {"register": "pin", "pin": 18}
  ]
}
```
