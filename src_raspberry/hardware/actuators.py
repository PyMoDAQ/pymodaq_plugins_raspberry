#region Imports
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from unittest.mock import MagicMock

import pigpio
#endregion

#region Logger
## @brief Logger du module actuators
logger = logging.getLogger(__name__)
#endregion

#region Classes de Configuration et Exceptions
@dataclass
class CActuatorConfig:
    """!
    @brief Représente la configuration d'un actionneur.
    """
    title:         str
    name:          str
    pin:           int
    driver:        str = 'PWM'
    pwmFrequency:  int = 0
    units:         str = ''
    minVal:        int = 0
    maxVal:        int = 255
    address:       Optional[int] = None

    @classmethod
    def FromDict(cls, data: dict) -> "CActuatorConfig":
        """!
        @brief Construit un objet de configuration à partir d'un dictionnaire.
        @param data Dictionnaire contenant les paramètres.
        @return CActuatorConfig
        """
        return cls(
            title        = data["title"],
            name         = data["name"],
            pin          = data["pin"],
            driver       = data.get("driver", "PWM"),
            pwmFrequency = data.get("pwm_frequency", 0),
            units        = data.get("units", ''),
            minVal       = data.get("min", 0),
            maxVal       = data.get("max", 255),
            address      = data.get("address"),
        )

class CPigpioNotConnectedError(RuntimeError):
    """! @brief Exception levée quand pigpiod n'est pas joignable. """
    pass

class CPinNotFoundError(KeyError):
    """! @brief Exception levée quand le pin demandé n'existe pas. """
    pass
#endregion

#region Pilotes d'actionneurs (classes interchangeables)
class CActuatorDriver(ABC):
    """!
    @brief Classe de base abstraite pour tous les pilotes d'actionneurs.

    Chaque mode de pilotage (PWM, tout-ou-rien, ...) est une classe interchangeable
    enregistrée dans ACTUATOR_DRIVER_REGISTRY et sélectionnée par le champ 'driver'
    de la configuration de l'actionneur. C'est ce qui permet d'adapter le serveur
    au type de pilotage utilisé par chaque banc de test.
    """

    def __init__(self, piClient, actuatorConfig: CActuatorConfig):
        """!
        @brief Constructeur d'initialisation.
        @param piClient Interface pigpio (ou mock en simulation).
        @param actuatorConfig Configuration de l'actionneur piloté.
        """
        ## @brief Interface pigpio
        self.pi = piClient
        ## @brief Configuration de l'actionneur
        self.cfg = actuatorConfig

    @abstractmethod
    def setup(self) -> None:
        """! @brief Initialise la broche matérielle. """
        pass

    @abstractmethod
    def set_value(self, value: int) -> None:
        """! @brief Applique une consigne à l'actionneur. """
        pass

    @abstractmethod
    def get_value(self) -> int:
        """! @brief Retourne la valeur/état courant de l'actionneur. """
        pass

    def reset(self) -> None:
        """! @brief Remet l'actionneur dans son état de repos (éteint). """
        self.set_value(0)


class CPwmActuator(CActuatorDriver):
    """!
    @brief Actionneur piloté en PWM (rapport cyclique 0-255), via pigpio.
    """

    def setup(self) -> None:
        self.pi.set_PWM_frequency(self.cfg.pin, self.cfg.pwmFrequency)
        self.pi.set_PWM_dutycycle(self.cfg.pin, 0)
        logger.debug("PWM configuré : %s (pin %s, %d Hz)", self.cfg.title, self.cfg.pin, self.cfg.pwmFrequency)

    def set_value(self, value: int) -> None:
        clampedValue = max(self.cfg.minVal, min(self.cfg.maxVal, value))
        if clampedValue != value:
            logger.warning("Valeur %s hors plage pour %s → bornée à %d.", value, self.cfg.title, clampedValue)
        self.pi.set_PWM_dutycycle(self.cfg.pin, clampedValue)

    def get_value(self) -> int:
        return int(self.pi.get_PWM_dutycycle(self.cfg.pin))


class CDigitalActuator(CActuatorDriver):
    """!
    @brief Actionneur tout-ou-rien (TOR), piloté en sortie logique 0/1 via pigpio.
    """

    def setup(self) -> None:
        self.pi.set_mode(self.cfg.pin, pigpio.OUTPUT)
        self.pi.write(self.cfg.pin, 0)
        logger.debug("TOR configuré : %s (pin %s)", self.cfg.title, self.cfg.pin)

    def set_value(self, value: int) -> None:
        state = 1 if value >= 1 else 0
        self.pi.write(self.cfg.pin, state)
        logger.info("Changement d'état : %s (pin %s) → %d", self.cfg.title, self.cfg.pin, state)

    def get_value(self) -> int:
        return int(self.pi.read(self.cfg.pin))


## @brief Registre des pilotes d'actionneurs.
#  Pour ajouter un mode de pilotage : créer une classe héritant de CActuatorDriver
#  puis l'enregistrer ici sous le nom utilisé dans le champ 'driver' de la config.
ACTUATOR_DRIVER_REGISTRY: dict = {
    'PWM':     CPwmActuator,
    'DIGITAL': CDigitalActuator,
}
#endregion

#region Gestionnaire Actionneurs
class CActuatorManager:
    """!
    @brief Gestionnaire des actionneurs via GPIO.

    Instancie pour chaque actionneur le pilote indiqué par sa configuration
    (champ 'driver'), ce qui permet de mélanger des modes de pilotage différents
    sur un même banc sans changer cette classe.
    """

    def __init__(self, actuatorsConfig: list):
        """!
        @brief Initialise la connexion au démon pigpio et charge la configuration.
        @param actuatorsConfig Liste des dictionnaires de configuration des actionneurs.
        """
        ## @brief Interface de communication avec la librairie pigpio
        self.piClient = pigpio.pi()

        if not self.piClient.connected:
            logger.info("pigpio non connecté : passage en mode simulation")
            self.piClient = MagicMock()
            self.piClient.connected = True
            self.piClient.read_value = 1

        ## @brief Dictionnaire des pilotes d'actionneurs indexé par PIN
        self._actuators: dict = {}

        self._CheckConnected()
        self._LoadConfig(actuatorsConfig)

    def _CheckConnected(self) -> None:
        """!
        @brief Vérifie la connexion matérielle.
        @raises CPigpioNotConnectedError Si non connecté.
        """
        if not self.piClient.connected:
            raise CPigpioNotConnectedError("Impossible de se connecter à pigpiod.")
        logger.info("Connexion à pigpio établie.")

    def _LoadConfig(self, actuatorsConfig: list) -> None:
        """!
        @brief Instancie le pilote adapté à chaque actionneur configuré.
        @param actuatorsConfig Liste des dictionnaires de configuration.
        """
        for rawConfig in actuatorsConfig:
            actuatorDef = CActuatorConfig.FromDict(rawConfig)
            driverClass = ACTUATOR_DRIVER_REGISTRY.get(actuatorDef.driver)
            if driverClass is None:
                logger.warning("Driver actionneur '%s' inconnu (pin %s) — ignoré.",
                                actuatorDef.driver, actuatorDef.pin)
                continue
            actuator = driverClass(self.piClient, actuatorDef)
            actuator.setup()
            self._actuators[actuatorDef.pin] = actuator
        logger.info(f"{len(self._actuators)} actionneur(s) configuré(s).")

    def GetActuatorsInfo(self) -> list:
        """!
        @brief Retourne la liste des configurations d'actionneurs.
        @return list de CActuatorConfig
        """
        return [actuator.cfg for actuator in self._actuators.values()]

    def SetPin(self, pinTarget: int, powerValue: int) -> None:
        """!
        @brief Applique une consigne à un actionneur.
        @param pinTarget Numéro GPIO BCM.
        @param powerValue Consigne souhaitée.
        """
        self._CheckConnected()
        self._GetActuator(pinTarget).set_value(powerValue)

    def GetPinValue(self, pinTarget: int) -> int:
        """!
        @brief Retourne la valeur/état actuel du pin.
        @param pinTarget Numéro GPIO.
        @return int Valeur courante.
        """
        self._CheckConnected()
        actuator = self._GetActuator(pinTarget)
        try:
            return actuator.get_value()
        except Exception as exc:
            raise RuntimeError(f"Impossible de lire la valeur du pin {pinTarget}.") from exc

    def Cleanup(self) -> None:
        """!
        @brief Éteint tous les actionneurs et ferme la connexion.
        """
        if not self.piClient.connected:
            return
        logger.info("Arrêt des actionneurs...")
        for actuator in self._actuators.values():
            actuator.reset()
        self.piClient.stop()
        logger.info("Connexion pigpio fermée.")

    def __enter__(self) -> "CActuatorManager":
        return self

    def __exit__(self, *_) -> None:
        self.Cleanup()

    def _GetActuator(self, pinTarget: int) -> CActuatorDriver:
        """!
        @brief Récupère le pilote d'un actionneur selon son PIN.
        @param pinTarget Numéro de broche.
        @return CActuatorDriver
        """
        try:
            return self._actuators[pinTarget]
        except KeyError:
            raise CPinNotFoundError(f"Pin {pinTarget} introuvable.")
#endregion
