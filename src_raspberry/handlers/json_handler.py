#region Imports
import json
import logging

from .base import IRequestHandler
#endregion

#region Logger
## @brief Logger du module de gestion des requêtes
logger = logging.getLogger(__name__)
#endregion


#region Gestion des requêtes JSON
class JsonRequestHandler(IRequestHandler):
    """!
    @brief Décode les requêtes JSON entrantes et les route vers le backend matériel.

    Cette couche ne touche jamais directement au matériel : elle traduit une requête
    en appels sur un IHardwareBackend (injecté), puis formate la réponse. Elle est
    ainsi indépendante du transport (en amont) et du matériel (en aval).
    """

    def __init__(self, hardwareBackend):
        """!
        @brief Constructeur d'initialisation.
        @param hardwareBackend Instance de IHardwareBackend à piloter.
        """
        ## @brief Backend matériel délégué
        self.backend = hardwareBackend

        ## @brief Dictionnaire de routage des requêtes
        self._requestHandlers = {
            "scan":     self._HandleScan,
            "AQ":       self._HandleAcquisition,
            "AQ-MULTI": self._HandleMultiAcquisition,
            "PI":       self._HandlePiloting,
            "PI-MULTI": self._HandleMultiPiloting,
        }

    def handle(self, request: str) -> str:
        """!
        @brief Traite une requête brute et renvoie la réponse sérialisée en JSON.
        @param request La trame JSON reçue.
        @return La réponse JSON sérialisée.
        """
        try:
            responseDict = self._Route(request)
        except Exception as exc:
            logger.exception("Erreur de traitement non gérée.")
            responseDict = {"state": "ERROR", "value": str(exc)}
        return json.dumps(responseDict)

    def _Route(self, jsonString: str) -> dict:
        """!
        @brief Décode et route une trame JSON entrante.
        @param jsonString La trame reçue.
        @return Le dictionnaire de réponse.
        """
        try:
            requestDict = json.loads(jsonString)
        except json.JSONDecodeError:
            return self._Error("Format JSON invalide")

        requestType = requestDict.get("type")
        handlerMethod = self._requestHandlers.get(requestType)

        if handlerMethod is None:
            return self._Error(f"Type de requête inconnu : '{requestType}'")

        try:
            return handlerMethod(requestDict)
        except Exception as exc:
            return self._Error(f"Erreur interne : {exc}")

    def _HandleScan(self, _request: dict) -> dict:
        """!
        @brief Gère la requête de scan des périphériques.
        @param _request Données de la requête (inutilisé).
        @return Dictionnaire listant les périphériques.
        """
        return self.backend.scan()

    def _HandleAcquisition(self, requestData: dict) -> dict:
        """!
        @brief Gère une requête d'acquisition simple.
        @param requestData La requête.
        @return Dict de réponse.
        """
        registerType = requestData.get("register")

        if registerType == "add":
            addressStr = requestData.get("add")
            try:
                numericAddress = int(addressStr, 16)
            except (ValueError, TypeError):
                return self._Error("Format d'adresse invalide")

            channelName = requestData.get("channel")
            try:
                sensorValue = self.backend.read_sensor(numericAddress, channelName)
            except KeyError:
                return self._Error("Capteur introuvable")

            return self._Ack(sensorValue) if sensorValue is not None else self._Error("Échec lecture")

        elif registerType == "pin":
            pinTarget = self._ParseInt(requestData.get("pin"), "pin")
            if isinstance(pinTarget, dict):
                return pinTarget
            try:
                return self._Ack(self.backend.read_pin(pinTarget))
            except Exception as exc:
                return self._Error(str(exc))

        return self._Error("Type de registre invalide")

    def _HandleMultiAcquisition(self, requestData: dict) -> dict:
        """! @brief Gère la requête AQ-MULTI. """
        componentsList = requestData.get("components", [])
        valuesList = []
        for comp in componentsList:
            compResult = self._HandleAcquisition(comp)
            valuesList.append(compResult["value"] if compResult.get("state") == "ACK" else compResult)
        return self._Ack(valuesList)

    def _HandlePiloting(self, requestData: dict) -> dict:
        """! @brief Gère la requête de pilotage. """
        pinTarget = self._ParseInt(requestData.get("pin"), "pin")
        powerValue = self._ParseInt(requestData.get("value"), "value")

        if isinstance(pinTarget, dict):
            return pinTarget
        if isinstance(powerValue, dict):
            return powerValue

        try:
            self.backend.set_pin(pinTarget, powerValue)
            return self._Ack(self.backend.read_pin(pinTarget))
        except Exception as exc:
            return self._Error(str(exc))

    def _HandleMultiPiloting(self, requestData: dict) -> dict:
        """! @brief Gère la requête PI-MULTI. """
        componentsList = requestData.get("components", [])
        return self._Ack([self._HandlePiloting(comp) for comp in componentsList])

    @staticmethod
    def _Ack(valueData) -> dict:
        """! @brief Formate un succès. """
        return {"state": "ACK", "value": valueData}

    @staticmethod
    def _Error(errorMessage: str) -> dict:
        """! @brief Formate une erreur. """
        logger.debug(f"Réponse d'erreur : {errorMessage}")
        return {"state": "ERROR", "value": errorMessage}

    @staticmethod
    def _ParseInt(rawValue, fieldName: str):
        """! @brief Convertit de manière sécurisée en entier. """
        try:
            return int(rawValue)
        except (ValueError, TypeError):
            return JsonRequestHandler._Error(f"Format invalide pour '{fieldName}'")
#endregion
