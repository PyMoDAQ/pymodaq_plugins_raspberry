#region Imports
import dataclasses
import logging
from typing import Optional

from smbus2 import SMBus

from .base import IHardwareBackend
from .scanner import CScanner
from .sensors import SENSOR_DRIVER_REGISTRY
from .actuators import CActuatorManager
#endregion

#region Logger
## @brief Logger du module backend
logger = logging.getLogger(__name__)
#endregion


#region Backend matériel
class HardwareBackend(IHardwareBackend):
    """!
    @brief Communication avec les composants d'un banc de test.

    Construit la cartographie des capteurs (via SENSOR_DRIVER_REGISTRY et la
    configuration) et le gestionnaire d'actionneurs. Toute la spécificité du banc
    provient de la configuration injectée ; cette classe ne dépend d'aucun modèle
    de Raspberry particulier.
    """

    def __init__(self, configModule):
        """!
        @brief Constructeur d'initialisation.
        @param configModule Référence au module de configuration du banc.
        """
        isSimulationEnv = False
        try:
            i2cBus = SMBus(configModule.I2C_BUS_ID)
        except (PermissionError, FileNotFoundError, OSError):
            from unittest.mock import MagicMock
            i2cBus = MagicMock()
            isSimulationEnv = True
            logger.info("Mode simulation activé pour l'I2C.")

        ## @brief Module de configuration du banc
        self.config = configModule
        ## @brief Instance de communication sur bus
        self.bus = i2cBus
        ## @brief Gestionnaire des actionneurs
        self.actuatorManager = CActuatorManager(configModule.ACTUATORS_CONFIG)
        ## @brief Dictionnaire des capteurs instanciés indexé par adresse
        self.sensorMap = self._BuildSensorMap(self.bus, isSimulationEnv)

    def _BuildSensorMap(self, targetBus, isSimulation: bool = False) -> dict:
        """!
        @brief Scanne le bus I2C et instancie les drivers des capteurs détectés.
        @param targetBus Objet bus.
        @param isSimulation Flag indiquant si l'on est en simulation.
        @return Dictionnaire de capteurs indexé par adresse.
        """
        instantiatedMap = {}
        detectedList = []

        if not isSimulation:
            detectedList = CScanner.ScanBus(self.config.I2C_BUS_ID)
            if not detectedList:
                logger.warning("Bascule en simulation automatique, aucun matériel.")
                isSimulation = True

        if isSimulation:
            detectedList = [a for a in self.config.SENSORS_CONFIG.keys() if isinstance(a, int)]

        for currentAddr in detectedList:
            sensorConfig = self.config.SENSORS_CONFIG.get(currentAddr)
            if sensorConfig is None:
                continue

            driverName = 'SIMULE' if isSimulation else sensorConfig['driver']
            driverClass = SENSOR_DRIVER_REGISTRY.get(driverName)

            if driverClass:
                instantiatedMap[currentAddr] = driverClass(targetBus, currentAddr)
                logger.info(f"Capteur '{sensorConfig.get('name', '?')}' ({driverName}) instancié @ {hex(currentAddr)}")
            else:
                logger.warning("Driver '%s' inconnu pour %s — ignoré.", driverName, hex(currentAddr))

        return instantiatedMap

    def scan(self) -> dict:
        """!
        @brief Décrit le matériel disponible (actionneurs et capteurs).
        @return Dictionnaire {'actuator': [...], 'detector': [...]}.
        """
        actuatorsInfo = []
        for actuatorObj in self.actuatorManager.GetActuatorsInfo():
            actuatorDict = dataclasses.asdict(actuatorObj)
            actuatorDict['frequency'] = actuatorDict.pop('pwmFrequency')
            actuatorsInfo.append(actuatorDict)

        detectorsInfo = []
        for addr in self.sensorMap:
            sensorCfg = self.config.SENSORS_CONFIG.get(addr)
            if not sensorCfg:
                continue
            detectorsInfo.append({
                "name":    sensorCfg.get('name', 'unknown'),
                "units":   sensorCfg.get('units', ''),
                "address": hex(addr),
                "pin":     None,
            })

        return {"actuator": actuatorsInfo, "detector": detectorsInfo}

    def read_sensor(self, address: int, channel: Optional[str] = None) -> Optional[float]:
        """!
        @brief Lit la valeur d'un capteur par son adresse.
        @param address Adresse du capteur.
        @param channel Canal de mesure optionnel.
        @return La valeur lue, ou None en cas d'échec de lecture.
        @raises KeyError Si aucun capteur n'est connu à cette adresse.
        """
        sensorObj = self.sensorMap.get(address)
        if sensorObj is None:
            raise KeyError(f"Capteur introuvable @ {hex(address)}")
        if channel:
            return sensorObj.ReadValue(channel=channel)
        return sensorObj.ReadValue()

    def read_pin(self, pin: int) -> int:
        """!
        @brief Lit la valeur courante d'un actionneur par sa broche.
        @param pin Numéro GPIO.
        @return Valeur courante.
        """
        return self.actuatorManager.GetPinValue(pin)

    def set_pin(self, pin: int, value: int) -> None:
        """!
        @brief Applique une consigne à un actionneur par sa broche.
        @param pin Numéro GPIO.
        @param value Consigne à appliquer.
        """
        self.actuatorManager.SetPin(pin, value)

    def cleanup(self) -> None:
        """!
        @brief Interrompt proprement la communication matérielle.
        """
        self.actuatorManager.Cleanup()
        self.bus.close()
#endregion
