#region Imports
from abc import ABC, abstractmethod
#endregion


#region Interface Gestion des requêtes
class IRequestHandler(ABC):
    """!
    @brief Couche de gestion des requêtes.

    Décode une requête brute, route vers l'action correspondante et renvoie une
    réponse sérialisée. Cette couche ne contient AUCUN accès matériel : toute
    opération sur les composants est déléguée à un IHardwareBackend. Elle peut
    donc être remplacée (autre format de protocole) indépendamment du transport
    et du matériel.
    """

    @abstractmethod
    def handle(self, request: str) -> str:
        """!
        @brief Traite une requête brute et renvoie la réponse sérialisée.
        @param request La requête brute reçue du transport.
        @return La réponse sérialisée (chaîne) à renvoyer au client.
        """
        raise NotImplementedError
#endregion
