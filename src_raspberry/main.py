#region Imports
import logging
import os
import sys

# Permet de lancer « python main.py » depuis n'importe quel répertoire en
# rendant les sous-paquets (transport, handlers, hardware) importables.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from hardware.backend import HardwareBackend
from handlers.json_handler import JsonRequestHandler
from transport.zmq_server import ZmqServer
#endregion

#region Configuration Log
## @brief Configuration globale du journal des évènements.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)-7s] %(name)s — %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)
#endregion

#region Main Application
def main() -> None:
    """!
    @brief Point d'entrée principal : assemble les trois couches et lance le serveur.

    Topologie :
        ZmqServer (transport) → JsonRequestHandler (requêtes) → HardwareBackend (composants)

    Le main est le seul maillon non interchangeable : il instancie chaque couche
    et les câble entre elles.
    """
    logger.info("Initialisation de la communication composants...")
    hardwareBackend = HardwareBackend(config)

    logger.info("Initialisation de la gestion des requêtes...")
    requestHandler = JsonRequestHandler(hardwareBackend)

    logger.info("Initialisation du serveur réseau...")
    transport = ZmqServer(requestHandler, listenPort=5555)

    try:
        # Le serveur bloque le thread principal en écoutant
        transport.start()

    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur.")
    finally:
        logger.info("Fermeture du serveur...")
        try:
            transport.stop()
        except Exception as exc:
            logger.error(f"Erreur fermeture serveur : {exc}")

        logger.info("Fermeture de la communication composants...")
        try:
            hardwareBackend.cleanup()
        except Exception as exc:
            logger.error(f"Erreur fermeture matériel : {exc}")

if __name__ == "__main__":
    main()
#endregion
