"""!
@file config_pizero.py
@brief Exemple de configuration de banc avec actionneurs tout-ou-rien (TOR) et
       sonde PT100.

Pour l'utiliser : copier ce contenu dans `src_raspberry/config.py`.
Aucun autre fichier n'a besoin d'être modifié — seuls les pilotes sélectionnés
par la configuration changent (DIGITAL au lieu de PWM, ajout du capteur PT-100).
"""
#region Constantes I2C
## @brief ID du bus I2C matériel
I2C_BUS_ID = 1
#endregion

#region Broches matérielles
## @brief Broche matérielle contrôlant le ventilateur (tout-ou-rien)
VENTILATEUR_PIN     = 13

## @brief Broche matérielle contrôlant la résistance chauffante (tout-ou-rien)
RESISTANCE_PIN      = 19
#endregion

#region Adresses I2C des capteurs
## @brief Adresse I2C du capteur de température et d'humidité AHT10
CAPTEUR_AHT10      = 0x38

## @brief Adresse I2C de la sonde PT100 (via CAN ADS1115)
CAPTEUR_PT100      = 0x48

## @brief Adresse I2C du contrôleur de ventilateur / capteur EMC2101
CAPTEUR_EMC2101    = 0x4C
#endregion

#region Configuration Actionneurs
## @brief Actionneurs pilotés en tout-ou-rien (driver 'DIGITAL')
ACTUATORS_CONFIG = [
    {
        'pin':       VENTILATEUR_PIN,
        'title':     'Ventilateur',
        'name':      'ventilateur',
        'driver':    'DIGITAL',
        'units':     'Etat',
        'min':       0,
        'max':       1,
        'address':   None,
    },
    {
        'pin':       RESISTANCE_PIN,
        'title':     'Resistance',
        'name':      'resistance',
        'driver':    'DIGITAL',
        'units':     'Etat',
        'min':       0,
        'max':       1,
        'address':   None,
    },
]
#endregion

#region Configuration Capteurs
## @brief Configuration des capteurs détectables sur le bus I2C
SENSORS_CONFIG = {
    CAPTEUR_AHT10: {
        'driver': 'AHT10',
        'title': 'aht10',
        'name': 'rh_sortie',
        'units': 'RH',
    },
    CAPTEUR_PT100: {
        'driver': 'PT-100',
        'title': 'pt-100',
        'name': 'pt100',
        'units': '°C',
    },
    0x49: {
        'driver': 'TMP102',
        'title': 'tmp102',
        'name': 't_dissipateur',
        'units': '°C',
    },
    0x4A: {
        'driver': 'TMP102',
        'title': 'tmp102',
        'name': 't_entree',
        'units': '°C',
    },
    0x4B: {
        'driver': 'TMP102',
        'title': 'tmp102',
        'name': 't_sortie',
        'units': '°C',
    },
    CAPTEUR_EMC2101: {
        'driver': 'EMC2101',
        'title': 'emc2101',
        'name': 'T_emc',
        'units': '°C',
    },
    'default': {
        'driver': 'Unknown',
        'title': 'Unknown Sensor',
        'name': 'unknow_sensor',
        'units': '',
    },
}
#endregion
