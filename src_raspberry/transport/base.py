#region Imports
from abc import ABC, abstractmethod
#endregion


#region Interface Transport
class ITransport(ABC):
    """!
    @brief Couche de communication avec le client PyMoDAQ.

    Un transport reçoit des requêtes brutes (chaînes de caractères) depuis le
    réseau, délègue leur traitement à un IRequestHandler, puis renvoie la réponse
    au client. Cette interface permet de remplacer ZeroMQ par un autre moyen de
    communication (série, HTTP, ...) sans toucher au reste de l'application.
    """

    @abstractmethod
    def start(self) -> None:
        """!
        @brief Démarre le transport et bloque sur la boucle d'écoute.
        """
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """!
        @brief Ferme proprement le transport et libère les ressources réseau.
        """
        raise NotImplementedError
#endregion
