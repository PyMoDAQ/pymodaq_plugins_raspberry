#region Imports
import random
import time
import logging
from abc import ABC, abstractmethod
#endregion

#region Logger
## @brief Logger pour le module sensors
logger = logging.getLogger(__name__)
#endregion

#region Interfaces
class CSensorDriver(ABC):
    """!
    @brief Classe de base abstraite pour tous les pilotes de capteurs.

    Chaque pilote est une classe interchangeable, enregistrée dans
    SENSOR_DRIVER_REGISTRY et sélectionnée par la configuration du banc.
    """

    def __init__(self, bus, addr: int):
        """!
        @brief Constructeur d'initialisation.
        @param bus Objet bus I2C.
        @param addr Adresse du composant.
        """
        ## @brief Référence vers le bus de communication
        self.bus = bus
        ## @brief Adresse I2C du capteur
        self.addr = addr

    @abstractmethod
    def ReadValue(self, **kwargs):
        """!
        @brief Lit et retourne la valeur du capteur.
        @return Valeur lue ou None en cas d'erreur.
        """
        pass
#endregion

#region Implémentations Drivers
class CDriverAht10(CSensorDriver):
    """!
    @brief Pilote pour le capteur de température et d'humidité AHT10.
    """

    def __init__(self, bus, addr: int):
        super().__init__(bus, addr)
        try:
            self.bus.write_byte(self.addr, 0xBA)
            time.sleep(0.02)
            self.bus.write_i2c_block_data(self.addr, 0xE1, [0x08, 0x00])
            time.sleep(0.05)
            logger.debug("AHT10 @%s initialisé.", hex(addr))
        except Exception as exc:
            logger.error("Erreur init AHT10 @%s : %s", hex(addr), exc)

    def _ReadRawData(self) -> list:
        """!
        @brief Déclenche une mesure et retourne les octets bruts.
        @return Liste des octets lus.
        """
        self.bus.write_i2c_block_data(self.addr, 0xAC, [0x33, 0x00])
        time.sleep(0.08)
        return self.bus.read_i2c_block_data(self.addr, 0x00, 6)

    def ReadValue(self, channel: str = 'hum') -> float:
        """!
        @brief Lit une valeur du capteur AHT10.
        @param channel 'hum' pour l'humidité ou 'temp' pour la température.
        @return Valeur flottante ou None.
        """
        try:
            rawData = self._ReadRawData()
            if channel == 'hum':
                humRaw = (rawData[1] << 12) | (rawData[2] << 4) | (rawData[3] >> 4)
                return round((humRaw / 1_048_576.0) * 100, 2)

            tempRaw = ((rawData[3] & 0x0F) << 16) | (rawData[4] << 8) | rawData[5]
            return round((tempRaw / 1_048_576.0) * 200 - 50, 2)
        except Exception as exc:
            logger.warning("Erreur lecture AHT10 @%s : %s", hex(self.addr), exc)
            return None

class CDriverTmp102(CSensorDriver):
    """!
    @brief Pilote pour le capteur de température de précision TMP102.
    """

    def ReadValue(self, **_) -> float:
        """!
        @brief Lit le registre de température sur 12 bits.
        @return Température en degrés Celsius ou None.
        """
        try:
            rawWord = self.bus.read_word_data(self.addr, 0x00)
            rawWord = ((rawWord << 8) & 0xFF00) | (rawWord >> 8)
            tempRaw = rawWord >> 4
            if tempRaw & 0x800:
                tempRaw -= 4096
            return round(tempRaw * 0.0625, 2)
        except Exception as exc:
            logger.warning("Erreur lecture TMP102 @%s : %s", hex(self.addr), exc)
            return None

class CDriverEmc2101(CSensorDriver):
    """!
    @brief Pilote pour la température interne du contrôleur EMC2101.
    """

    def ReadValue(self, **_) -> float:
        """!
        @brief Retourne la température interne (registre 0x00).
        @return Température en degrés Celsius ou None.
        """
        try:
            tempRaw = self.bus.read_byte_data(self.addr, 0x00)
            if tempRaw > 127:
                tempRaw -= 256
            return float(tempRaw)
        except Exception as exc:
            logger.warning("Erreur lecture EMC2101 @%s : %s", hex(self.addr), exc)
            return None

class CDriverSimule(CSensorDriver):
    """!
    @brief Pilote de test pour retourner des valeurs simulées.
    """

    def ReadValue(self, channel: str = None) -> float:
        """!
        @brief Retourne des valeurs factices.
        @param channel Canal de mesure souhaité.
        @return Valeur simulée.
        """
        if channel == 'hum':
            return round(random.uniform(40.0, 60.0), 2)
        return round(random.uniform(20.0, 25.0), 2)

class CDriverPt100(CSensorDriver):
    """!
    @brief Pilote pour une sonde de température PT100 lue via un CAN ADS1115.

    La PT100 ne communique pas directement sur le bus I2C du serveur : elle est
    lue au travers d'un convertisseur analogique-numérique ADS1115 (librairie
    Adafruit_ADS1x15). L'argument `bus` n'est donc pas utilisé, mais conservé
    pour respecter l'interface commune des pilotes de capteurs.
    """

    def __init__(self, bus, addr: int):
        super().__init__(bus, addr)
        # Import local pour isoler la dépendance optionnelle Adafruit_ADS1x15 :
        # le module sensors reste importable même si la librairie est absente.
        try:
            import Adafruit_ADS1x15
            self._adc = Adafruit_ADS1x15.ADS1115()
            ## @brief Gain de l'amplificateur du CAN
            self.GAIN = 1
            ## @brief Tension d'alimentation du pont (V)
            self.TENSION_VA = 3.29
            ## @brief Valeur brute maximale du CAN
            self.MAXI = 26300.0
            ## @brief Résistance de pont (Ohm)
            self.RP = 97.7
            ## @brief Résistance nominale de la PT100 à 0 °C (Ohm)
            self.R0 = 100.0
            ## @brief Coefficient de température de la platine
            self.ALPHA = 0.00385
        except Exception as exc:
            logger.error("Erreur d'initialisation de l'ADS1115 (PT100) : %s", exc)

    def ReadValue(self, **_) -> float:
        """!
        @brief Lit la température via le CAN et la loi de la platine.
        @return Température en degrés Celsius (0.0 en cas d'échec).
        """
        try:
            rawValue = self._adc.read_adc(0, gain=self.GAIN)            # canal A0
            tensionPT100 = (rawValue / self.MAXI) * self.TENSION_VA
            denominateur = self.TENSION_VA - tensionPT100
            if abs(denominateur) < 0.001:
                return 0.0
            Rpt100 = (tensionPT100 * self.RP) / denominateur            # résistance du pont
            temperature = (Rpt100 - self.R0) / (self.R0 * self.ALPHA)   # loi de la platine
            return round(temperature, 2)
        except Exception as exc:
            logger.warning("Échec de lecture PT100 : %s", exc)
            return 0.0
#endregion

#region Registre
## @brief Dictionnaire regroupant l'ensemble des drivers de capteurs.
#  Pour ajouter un capteur : créer une classe héritant de CSensorDriver puis
#  l'enregistrer ici sous le nom utilisé dans le champ 'driver' de la config.
SENSOR_DRIVER_REGISTRY: dict = {
    'AHT10':   CDriverAht10,
    'TMP102':  CDriverTmp102,
    'EMC2101': CDriverEmc2101,
    'PT-100':  CDriverPt100,
    'SIMULE':  CDriverSimule,
}
#endregion
