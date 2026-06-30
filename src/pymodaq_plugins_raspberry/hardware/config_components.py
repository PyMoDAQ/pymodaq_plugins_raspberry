from pymodaq_utils import Config

from pymodaq.utils.logger import set_logger, get_module_name
logger = set_logger(get_module_name(__file__))

def get_actuators_hardware(config : Config) -> list:
    """
    Scan the TOML file for actuators hardware and
    return a list of dictionary of the elements of each actuators hardware

    :param config: The TOML file scanned in a dictionary
    :return: list of actuators hardware
    """

    temp_tab = []

    for component in config("Raspberry", "ACTUATOR"):
        if 'COMPONENT' in component:
            try:
                temp_tab.append(config("Raspberry", "ACTUATOR", component) | {'type': 'bool', 'default': False, 'value': False})
            except Exception as e:
                logger.info(str(e))
    return temp_tab


def get_detectors_hardware(config: Config) -> list:
    """
    Scan the TOML file for detectors hardware and
    return a list of dictionary of the elements of each detectors hardware

    :param config: The TOML file scanned in a dictionary
    :return: list of detectors hardware
    """

    temp_tab = []

    for component in config("Raspberry", "DETECTOR"):
        if 'COMPONENT' in component:
            try:
                temp_tab.append(config("Raspberry", "DETECTOR", component) | {'type': 'bool', 'default': False, 'value': False})
            except Exception as e:
                logger.info(str(e))

    return temp_tab

def get_access_variables(config : Config) -> dict :
    """
    Take every access variables that are not basics variables and put them in a dictionary

    :param config: The TOML file scanned in a dictionary
    :return: dictionary of each access variables
    """
    base_elems = ["title", "name", "units", "min", "max"]
    temp_tab = {}

    for component in config("Raspberry", "ACTUATOR"):
        for elem in config("Raspberry", "ACTUATOR", component):
            if elem not in base_elems and elem not in temp_tab:
                temp_tab[elem] = []


    for component in config("Raspberry", "DETECTOR"):
        for elem in config("Raspberry", "DETECTOR", component):
            if elem not in base_elems and elem not in temp_tab:
                temp_tab[elem] = []

    return temp_tab
