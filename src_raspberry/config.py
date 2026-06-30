"""!
@file config.py
@brief Configuration du banc de test : adresses I2C, broches matérielles et
       description des actionneurs / capteurs.

Chaque Raspberry possède son propre banc de test : ce fichier est l'unique endroit
à adapter pour décrire le matériel présent. Les couches transport / gestion des
requêtes / communication composants ne changent pas d'un banc à l'autre.

Ce fichier décrit le banc par défaut (actionneurs pilotés en PWM). Des exemples de
configurations pour d'autres bancs sont fournis dans le dossier `config_examples/`
(ex. `config_pizero.py` pour un banc tout-ou-rien avec sonde PT100) : il suffit de
copier le contenu voulu ici.
"""
#region Constantes I2C
## @brief ID du bus I2C matériel
I2C_BUS_ID = 1
#endregion

#region Broches matérielles
## @brief Broche matérielle contrôlant le ventilateur
VENTILATEUR_PIN     = 18

## @brief Broche matérielle contrôlant la résistance chauffante
RESISTANCE_PIN      = 23
#endregion

#region Adresses I2C des capteurs
## @brief Adresse I2C du capteur de température et d'humidité AHT10
CAPTEUR_AHT10      = 0x38

## @brief Adresse I2C du capteur de température principal TMP102
CAPTEUR_TMP102     = 0x48

## @brief Adresse I2C du contrôleur de ventilateur / capteur EMC2101
CAPTEUR_EMC2101    = 0x4C
#endregion

#region Configuration Actionneurs
## @brief Configuration des actionneurs (ventilateurs, résistances, etc.)
ACTUATORS_CONFIG = [
    {
        'pin':           VENTILATEUR_PIN,
        'title':         'Ventilateur',
        'name':          'ventilateur',
        'driver':        'PWM',          # mode de pilotage : 'PWM' ou 'DIGITAL'
        'units':         '%',
        'min':           0,
        'max':           255,
        'address':       None,
        'pwm_frequency': 25000,
    },
    {
        'pin':           RESISTANCE_PIN,
        'title':         'Resistance',
        'name':          'resistance',
        'driver':        'PWM',
        'units':         '%',
        'min':           0,
        'max':           255,
        'address':       None,
        'pwm_frequency': 100,
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
    CAPTEUR_TMP102: {
        'driver': 'TMP102',
        'title': 'tmp102',
        'name': 't_resistance',
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
