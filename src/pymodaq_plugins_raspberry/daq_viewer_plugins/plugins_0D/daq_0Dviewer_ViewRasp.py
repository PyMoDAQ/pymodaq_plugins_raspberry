import numpy as np

from pymodaq_data.data import DataToExport
from pymodaq.utils.data import DataFromPlugins
from pymodaq_gui.parameter import Parameter

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main

from ...hardware.link_zmq import ZMQLink
from ...hardware.config_components import get_actuators_hardware, get_detectors_hardware, get_access_variables

from pymodaq_plugins_raspberry import config

from pymodaq.utils.logger import set_logger, get_module_name
logger = set_logger(get_module_name(__file__))


class DAQ_0DViewer_ViewRasp(DAQ_Viewer_base):
    """ Plugin class for acquisition of signals through a raspberry

        Before using you need to link the raspberry to your hardware
        and to your local network with a valid ip address

        ==================== ================================
        **Attributes**         **Type**
        *config*               elements put in the TOML file
        *params*               dictionary list
        *task*
        ==================== ================================

        See Also
        --------
        refresh_hardware
    """
    config: config
    controller: ZMQLink # the class that link pymodaq to the raspberry
    selected_components : dict

    # SETUP CONFIGURATION FILE
    ####################################################################################################################

    # list of all the detectors and actuators detected on the raspberry
    compo_group = [
        {'title': 'Actuators',
         'name': 'load_actuator_group',
         'type': 'group',
         'children': get_actuators_hardware(config)
         },

        {'title': 'Detectors',
         'name': 'load_detector_group',
         'type': 'group',
         'children': get_detectors_hardware(config)
         }
    ]

    ####################################################################################################################

    # SETUP SPECIFIC CONFIG FOR PRESET
    ####################################################################################################################
    params = comon_parameters + [
        {
            'title': '--- SELECT COMPONENTS TO LOAD ---',
            'name': 'load_compo_group',
            'type': 'group',
            'expanded': True,
            'children': compo_group
         }
    ]
    ####################################################################################################################

    def ini_attributes(self):
        self.controller: ZMQLink = None
        self.selected_components = get_access_variables(config) # dict of all the selected components, sorted by address and pin

        actuator_settings = self.settings.child('load_compo_group', 'load_actuator_group')
        for elem in actuator_settings:
            for type_access_variables in self.selected_components:

                try:
                    if (elem.opts[type_access_variables] != "None" and elem.value()
                            and elem not in self.selected_components[type_access_variables]):

                        self.selected_components[type_access_variables].append(elem)
                except Exception as e:
                    logger.info(f"ERROR - NO ELEMENTS WITH NAME : {str(e)}")

        detectors_settings = self.settings.child('load_compo_group', 'load_detector_group')
        for elem in detectors_settings:
            for type_access_variables in self.selected_components:

                try:
                    if (elem.opts[type_access_variables] != "None" and elem.value()
                            and elem not in self.selected_components[type_access_variables]):

                        self.selected_components[type_access_variables].append(elem)
                except Exception as e:
                    logger.info(f"ERROR - NO ELEMENTS WITH NAME : {str(e)}")

        logger.info(f"Selected Components : {self.selected_components}")

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (ZMQLink)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """
        if self.is_master:
            self.controller = ZMQLink(config("Raspberry", "address_Rasp"), config("Raspberry", "port"))
            initialized = self.controller.get_link_status()
        else:
            self.controller = controller
            initialized = True

        return "Initialized", initialized

    def close(self):
        """Terminate the communication protocol"""
        if self.is_master:
            self.controller.close()
        pass

    def commit_settings(self, param: Parameter):
        if param.type() == 'bool':
            if param.parent().name() == 'load_actuator_group' or param.parent().name() == 'load_detector_group':
                for type_access_variables in self.selected_components:

                    try :
                        if param.opts[type_access_variables] != "None":
                            exist_param_in_add = (False, 0)
                            for i, elem in enumerate(self.selected_components[type_access_variables]):
                                if elem.name() == param.name():
                                    exist_param_in_add = (True, i)

                            if param.value() and not exist_param_in_add[0]:
                                self.selected_components[type_access_variables].append(param)
                            elif exist_param_in_add[0]:
                                self.selected_components[type_access_variables].pop(exist_param_in_add[1])
                    except Exception as e:
                        logger.info(f"ERROR - NO ELEMENTS WITH NAME : {str(e)}")

            logger.info(f"{param}, Bool : {param.value()}\n{self.selected_components}")
        pass

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble, and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """
        access_variables = []
        labels_tab = []

        for i, type_access_variables in enumerate(self.selected_components):
            access_variables.append([])
            for elem in self.selected_components[type_access_variables]:
                try:
                    access_variables[i].append(elem.opts[type_access_variables])
                    labels_tab.append(elem.opts['name'])
                except Exception as e:
                    logger.info(f"ERROR - NO ELEMENTS WITH NAME : {str(e)}")
                                                # SPECIFIC LINE #
########################################################################################################################
        data_tot = self.controller.multi_acquisition(addresses=access_variables[0], pins=access_variables[1])
########################################################################################################################

        if isinstance(data_tot, str) and "ERROR" in data_tot:
            mess = f"Viewer ERROR : {data_tot}"
            data_tot = [0]
            logger.warning(mess)
        else:
            logger.info(f" Viewer Data : {data_tot}")

        if isinstance(data_tot, list):
            if len(labels_tab) == 1:
                data_tot = [np.array(data_tot)]
            else:
                data_tot = list(map(lambda x: np.array([x]), data_tot))

            self.dte_signal.emit(
                DataToExport(name='ZMQViewer',
                             data=[DataFromPlugins(
                                 name='Viewer',
                                 data=data_tot,
                                 dim='Data0D',
                                 labels=labels_tab)
                             ]
                             )
            )

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        return ''

if __name__ == '__main__':
    main(__file__)
