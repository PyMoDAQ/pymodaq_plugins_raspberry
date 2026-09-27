#region Imports
import math
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

class CThermalModel:
    """!
    @brief Modèle thermique grossier du banc, utilisé uniquement en simulation.

    Modèle du premier ordre : la résistance chauffe le banc, les pertes vers
    l'ambiant augmentent avec le ventilateur. L'échauffement est intégré de façon
    exacte entre deux lectures ; chaque capteur simulé le lit avec son propre
    couplage, sur une ambiance qui dérive lentement, avec un léger bruit.
    """

    ## @brief Température ambiante moyenne (°C)
    AMBIENT = 22.0
    ## @brief Amplitude de la dérive lente de l'ambiance (°C)
    DRIFT = 0.5
    ## @brief Période de la dérive de l'ambiance (s)
    DRIFT_PERIOD = 600.0
    ## @brief Échauffement à pleine chauffe sans ventilation (°C)
    HEATER_RISE = 40.0
    ## @brief Multiplicateur des pertes ajouté par le ventilateur à plein régime
    FAN_GAIN = 2.3
    ## @brief Constante de temps sans ventilation (s)
    TIME_CONSTANT = 60.0
    ## @brief Écart-type du bruit de mesure (°C)
    NOISE = 0.05

    def __init__(self, actuatorManager, actuatorsConfig: list):
        """!
        @brief Constructeur d'initialisation.
        @param actuatorManager Gestionnaire d'actionneurs, lu pour connaître les consignes.
        @param actuatorsConfig Configuration des actionneurs (repérés par leur nom).
        """
        self._manager = actuatorManager
        ## @brief Actionneur chauffant et ventilateur (None si absents de la configuration)
        self._heater = self._FindActuator(actuatorsConfig, ('resist', 'chauff', 'heat'))
        self._fan = self._FindActuator(actuatorsConfig, ('ventil', 'fan'))
        self._start = self._last = time.monotonic()
        ## @brief Échauffement courant du banc au-dessus de l'ambiance (°C)
        self._rise = 0.0

    @staticmethod
    def _FindActuator(actuatorsConfig: list, keywords: tuple):
        """! @brief Premier actionneur dont le nom contient un des mots-clés. """
        for actuator in actuatorsConfig:
            if any(k in str(actuator.get('name', '')).lower() for k in keywords):
                return actuator
        return None

    def _Level(self, actuator) -> float:
        """! @brief Consigne courante de l'actionneur, ramenée entre 0 et 1. """
        if actuator is None:
            return 0.0
        try:
            low, high = float(actuator.get('min', 0)), float(actuator.get('max', 1))
            value = float(self._manager.GetPinValue(actuator['pin']))
            return min(1.0, max(0.0, (value - low) / (high - low))) if high > low else 0.0
        except Exception:
            return 0.0

    def _Update(self) -> float:
        """! @brief Fait évoluer l'échauffement jusqu'à maintenant. @return L'instant courant. """
        now = time.monotonic()
        elapsed, self._last = now - self._last, now
        losses = 1.0 + self.FAN_GAIN * self._Level(self._fan)
        target = self.HEATER_RISE * self._Level(self._heater) / losses
        self._rise = target + (self._rise - target) * math.exp(-elapsed * losses / self.TIME_CONSTANT)
        return now

    def _Ambient(self, now: float) -> float:
        """! @brief Ambiance qui dérive lentement autour de AMBIENT. """
        return self.AMBIENT + self.DRIFT * math.sin(2 * math.pi * (now - self._start) / self.DRIFT_PERIOD)

    def Temperature(self, coupling: float) -> float:
        """! @brief Température vue par un capteur plus ou moins proche de la résistance (couplage 0 à 1). """
        now = self._Update()
        return round(self._Ambient(now) + coupling * self._rise + random.gauss(0.0, self.NOISE), 2)

    def Humidity(self, coupling: float) -> float:
        """! @brief Humidité relative : elle baisse quand l'air se réchauffe (environ -1,5 %RH/°C). """
        self._Update()
        humidity = 50.0 - 1.5 * coupling * self._rise + random.gauss(0.0, 0.2)
        return round(min(100.0, max(0.0, humidity)), 2)


## @brief Durée d'une lecture réelle sur Raspberry, par pilote (s), reproduite en simulation.
#  Sans elle, le serveur simulé répond instantanément et une acquisition continue sans
#  temps d'attente enchaîne des milliers de requêtes par seconde, au point de figer
#  l'interface PyMoDAQ ; le vrai banc est naturellement limité par ces durées.
SIMULATED_READ_TIME: dict = {
    'AHT10':   0.080,   # attente de fin de mesure imposée par le capteur (voir CDriverAht10)
    'TMP102':  0.002,   # transaction I2C + surcoût Python sur Raspberry
    'EMC2101': 0.002,
    'PT-100':  0.008,   # conversion de l'ADS1115 à 128 échantillons/s
}


class CDriverSimule(CSensorDriver):
    """!
    @brief Pilote de test pour retourner des valeurs simulées.

    Relié à un CThermalModel, il renvoie des valeurs qui évoluent de façon
    plausible et réagissent aux actionneurs ; sinon, des valeurs aléatoires.
    """

    def __init__(self, bus, addr: int):
        super().__init__(bus, addr)
        ## @brief Modèle thermique partagé (None : valeurs aléatoires indépendantes)
        self.model = None
        ## @brief Couplage du capteur à la résistance (0 : ambiance, 1 : au contact)
        self.coupling = 0.5
        ## @brief Canal lu quand la requête n'en précise pas ('temp' ou 'hum')
        self.defaultChannel = 'temp'
        ## @brief Durée simulée d'une lecture (s)
        self.readTime = 0.002

    def AttachModel(self, model: CThermalModel, coupling: float, defaultChannel: str = 'temp',
                    readTime: float = 0.002) -> None:
        """!
        @brief Relie le capteur simulé au modèle thermique du banc.
        @param model Modèle thermique partagé par les capteurs simulés.
        @param coupling Couplage du capteur à la résistance (0 à 1).
        @param defaultChannel Canal lu par défaut ('hum' pour un capteur d'humidité).
        @param readTime Durée simulée d'une lecture, celle du vrai capteur (s).
        """
        self.model = model
        self.coupling = coupling
        self.defaultChannel = defaultChannel
        self.readTime = readTime

    def ReadValue(self, channel: str = None) -> float:
        """!
        @brief Retourne des valeurs simulées.
        @param channel Canal de mesure souhaité.
        @return Valeur simulée.
        """
        time.sleep(self.readTime)  # durée d'une vraie lecture : le serveur n'est pas plus rapide que le banc
        channel = channel or self.defaultChannel
        if self.model is not None:
            if channel == 'hum':
                return self.model.Humidity(self.coupling)
            return self.model.Temperature(self.coupling)
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
