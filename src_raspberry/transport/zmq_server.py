#region Imports
import logging
import socket as sys_socket
import threading

import zmq
from zmq.utils.monitor import recv_monitor_message

from .base import ITransport
#endregion

#region Logger
## @brief Logger du module de transport ZeroMQ
logger = logging.getLogger(__name__)
#endregion


#region Surveillance des connexions
def monitor_connections(monitor_socket) -> None:
    """!
    @brief Surveille les connexions/déconnexions TCP dans un thread séparé.
    @param monitor_socket Socket de monitoring ZMQ.
    """
    logger.info("Surveillance des connexions activée.")
    try:
        while True:
            if not monitor_socket.poll(timeout=500):
                continue
            try:
                evt = recv_monitor_message(monitor_socket)
                if evt['event'] == zmq.EVENT_ACCEPTED:
                    try:
                        s  = sys_socket.fromfd(evt['value'], sys_socket.AF_INET, sys_socket.SOCK_STREAM)
                        ip = s.getpeername()[0]
                        s.close()
                    except Exception:
                        ip = evt['endpoint']
                    logger.info("NOUVEAU CLIENT : %s", ip)
                elif evt['event'] == zmq.EVENT_DISCONNECTED:
                    logger.info("DÉCONNEXION : %s", evt['endpoint'])
            except zmq.error.ContextTerminated:
                break
            except Exception as exc:
                logger.error("Erreur moniteur : %s", exc)
    except zmq.error.ContextTerminated:
        pass
    logger.info("Fin de la surveillance des connexions.")
#endregion


#region Serveur ZMQ
class ZmqServer(ITransport):
    """!
    @brief Transport gérant la communication avec le client PyMoDAQ via ZeroMQ.

    Ce transport ne s'occupe que du réseau et du framing des messages. Le contenu
    de chaque requête est délégué à un IRequestHandler, ce qui le rend totalement
    indépendant du protocole applicatif et du matériel.
    """

    def __init__(self, requestHandler, listenPort: int = 5555):
        """!
        @brief Constructeur d'initialisation.
        @param requestHandler Instance de IRequestHandler à qui déléguer les requêtes.
        @param listenPort Port d'écoute TCP.
        """
        ## @brief Gestionnaire de requêtes délégué
        self.handler = requestHandler
        ## @brief Port d'écoute
        self.port = listenPort
        self.context = None
        self.zmq_socket = None
        self.monitor_socket = None

    def start(self) -> None:
        """!
        @brief Initialise les sockets et lance la boucle d'écoute (bloquant).
        """
        self.context = zmq.Context()
        self.zmq_socket = self.context.socket(zmq.ROUTER)
        self.zmq_socket.bind(f"tcp://*:{self.port}")
        logger.info("Serveur ZMQ ROUTER démarré sur le port %d.", self.port)

        # Thread de surveillance des connexions
        self.monitor_socket = self.zmq_socket.get_monitor_socket()
        threading.Thread(
            target=monitor_connections,
            args=(self.monitor_socket,),
            daemon=True,
        ).start()

        logger.info("SERVEUR PRÊT (Ctrl+C pour arrêter)")
        self._run_loop()

    def _run_loop(self) -> None:
        """!
        @brief Boucle principale de réception et de traitement des messages.
        """
        while True:
            frames = self.zmq_socket.recv_multipart()

            # Détection du format (REQ = 3 frames avec délimiteur vide, DEALER = 2 frames)
            client_id = frames[0]
            if len(frames) == 3 and frames[1] == b'':
                use_delimiter = True
                message_bytes = frames[2]
            elif len(frames) == 2:
                use_delimiter = False
                message_bytes = frames[1]
            else:
                logger.warning("Paquet malformé reçu (%d frames) — ignoré.", len(frames))
                continue

            try:
                command_str = message_bytes.decode('utf-8')
            except UnicodeDecodeError:
                logger.error("Paquet non UTF-8 reçu — ignoré.")
                continue

            logger.info("← (%s) %s", client_id.hex()[:8], command_str)

            # Délégation à la couche de gestion des requêtes
            response_str = self.handler.handle(command_str)

            logger.info("→ %s", response_str)

            reply_frames = [client_id]
            if use_delimiter:
                reply_frames.append(b'')
            reply_frames.append(response_str.encode('utf-8'))
            self.zmq_socket.send_multipart(reply_frames)

    def stop(self) -> None:
        """!
        @brief Ferme proprement les connexions ZMQ.
        """
        logger.info("Arrêt du serveur ZMQ...")
        for sock in (self.zmq_socket, self.monitor_socket):
            try:
                if sock:
                    sock.setsockopt(zmq.LINGER, 0)
                    sock.close()
            except Exception:
                pass
        if self.context:
            self.context.term()
#endregion
