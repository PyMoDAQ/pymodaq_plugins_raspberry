#region Imports
import logging
from smbus2 import SMBus
#endregion

#region Logger
## @brief Logger du module scanner
logger = logging.getLogger(__name__)
#endregion

#region Classes
class CScanner:
    """!
    @brief Classe utilitaire pour scanner le bus I2C.
    """

    @staticmethod
    def ScanBus(busId: int) -> list:
        """!
        @brief Parcourt toutes les adresses I2C possibles pour identifier les capteurs connectés.
        @param busId Identifiant du bus I2C matériel.
        @return list Liste des adresses (int) qui ont répondu.
        """
        detectedAddresses = []
        logger.info("Scan du bus I2C...")

        try:
            with SMBus(busId) as bus:
                # La plage standard I2C va de 0x03 à 0x77
                for currentAddress in range(0x03, 0x78):
                    try:
                        bus.write_byte(currentAddress, 0)
                        detectedAddresses.append(currentAddress)
                        logger.info("   -> Périphérique détecté à l'adresse : %s", hex(currentAddress))
                    except OSError:
                        pass
        except Exception as exc:
            logger.error("Erreur critique lors du scan du bus : %s", exc)

        return detectedAddresses
#endregion
