#region Imports
from abc import ABC, abstractmethod
from typing import Optional
#endregion


#region Interface Communication composants
class IHardwareBackend(ABC):
    """!
    @brief Couche de communication avec les composants (capteurs et actionneurs).

    Toute la spécificité d'un banc de test (capteurs présents, mode de pilotage
    des actionneurs : PWM, tout-ou-rien, ...) est encapsulée ici. Le banc est
    décrit par la configuration ; cette interface reste identique quel que soit
    le matériel sous-jacent, ce qui rend le backend interchangeable.
    """

    @abstractmethod
    def scan(self) -> dict:
        """!
        @brief Décrit le matériel disponible.
        @return Dictionnaire {'actuator': [...], 'detector': [...]}.
        """
        raise NotImplementedError

    @abstractmethod
    def read_sensor(self, address: int, channel: Optional[str] = None) -> Optional[float]:
        """!
        @brief Lit la valeur d'un capteur par son adresse.
        @param address Adresse du capteur.
        @param channel Canal de mesure optionnel.
        @return La valeur lue, ou None en cas d'échec de lecture.
        @raises KeyError Si aucun capteur n'est connu à cette adresse.
        """
        raise NotImplementedError

    @abstractmethod
    def read_pin(self, pin: int) -> int:
        """!
        @brief Lit la valeur/état courant d'un actionneur par sa broche.
        @param pin Numéro de broche (GPIO BCM).
        @return La valeur courante de l'actionneur.
        """
        raise NotImplementedError

    @abstractmethod
    def set_pin(self, pin: int, value: int) -> None:
        """!
        @brief Applique une consigne à un actionneur par sa broche.
        @param pin Numéro de broche (GPIO BCM).
        @param value Consigne à appliquer.
        """
        raise NotImplementedError

    @abstractmethod
    def cleanup(self) -> None:
        """!
        @brief Libère proprement les ressources matérielles.
        """
        raise NotImplementedError
#endregion
