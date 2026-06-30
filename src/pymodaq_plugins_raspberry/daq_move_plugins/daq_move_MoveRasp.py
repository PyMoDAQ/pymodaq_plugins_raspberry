from pint.facets.numpy import quantity
from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun, main,
                                                          DataActuator, DataActuatorType)

from pymodaq_gui.parameter import Parameter

from ..hardware.link_zmq import ZMQLink
from ..hardware.config_components import get_actuators_hardware, get_access_variables

from pymodaq_plugins_raspberry import config

from pymodaq.utils.logger import set_logger, get_module_name
logger = set_logger(get_module_name(__file__))

class DAQ_Move_MoveRasp(DAQ_Move_base):
    """ Plugin class for controlling components through a raspberry

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
    controller: ZMQLink  # the class that link pymodaq to the raspberry
    output_value = 0 # temp variable to transport the return value

    # TOML ACTUATOR LOAD
    ####################################################################################################################
    actuators = get_actuators_hardware(config)
    ####################################################################################################################

    # SETUP AXES VARIABLES
    ####################################################################################################################
    is_multiaxes = True
    _axis_names = [actuator['title'] for actuator in actuators]
    _controller_units = [actuator['units'] for actuator in actuators]
    _epsilon = [0.1 for actuator in actuators]
    data_actuator_type = DataActuatorType.DataActuator
    current_component = None
    name_access_variables = get_access_variables(config)
    ####################################################################################################################

    # SETUP SPECIFIC CONFIG FOR PRESET
    ####################################################################################################################
    params = comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)
    ####################################################################################################################

    def ini_attributes(self):
        self.controller: ZMQLink = None

        for elem in self.actuators:
            self.update_move_settings(self.axis_name)

        self.settings['bounds', 'is_bounds'] = True

        pass

    def user_condition_to_reach_target(self) -> bool:
        """ Implement a condition for exiting the polling mechanism and specifying that the
        target value has been reached

       Returns
        -------
        bool: if True, PyMoDAQ considers the target value has been reached
        """
        return True

    def close(self):
        """Terminate the communication protocol"""
        if self.is_master:
            self.controller.close()
        pass

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == 'axis':
            self.update_move_settings(param.value())

    def update_move_settings(self, param : str):
        """Update the settings of the actuators

        Parameters
        ----------
        param: str
            the name of the parameter (within detector_settings) whose value has been changed by the user
        """
        for elem in self.actuators:
            if elem['title'] == param:
                self.current_component = elem
                self.settings['bounds', 'max_bound'] = elem['max']
                self.settings['bounds', 'min_bound'] = elem['min']
                self.settings['units'] = elem['units']
                break

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (ZMQLink)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

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

        self.settings.child('scaling').setOpts(visible=False)
        return "Initialized", initialized

    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (DataActuator) value of the absolute target positioning
        """

        value = self.check_bound(value)
        self.target_value = value
        value = self.set_position_with_scaling(value)

        self.move_value(value)

    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (DataActuator) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        self.move_value(value)

    def move_home(self):
        """Call the reference method of the controller"""
        self.move_value(DataActuator(name='set_value_home', data=0, units=self.axis_unit))

    def move_value(self, value):
        """ Move the actuator to the target actuator value defined by value
        Used by move_rel() and move_abs()
        Parameters
        ----------
        value: value of the target positioning
        """
        output = 0
        access_variables = None

        if isinstance(value, DataActuator):
            value = value.value(self.axis_unit)

        # value = (value * 255) / 10000 # Formula for converting the PWM duty cycle percentage to a raw value in PigPio
        if self.current_component is not None and (isinstance(value, float) or isinstance(value, int)):

            for elem in self.name_access_variables:
                try:
                    if self.current_component[elem] != 'None':
                        access_variables = self.current_component[elem]

                                                # SPECIFIC LINES #
########################################################################################################################
                        if elem == "address":
                            output = self.controller.pilotage(address=access_variables, value=value)
                        else:
                            output = self.controller.pilotage(pin=access_variables, value=value)
########################################################################################################################
                except Exception as e:
                    logger.info(f"ERROR - NO ELEMENTS WITH NAME : {str(e)}")

            if not isinstance(output, str):
                self.output_value = output
                logger.info(f"Move : {access_variables} -> {value} | Output : {output}")
            else:
                logger.warning(output)

        else:
            logger.warning("Input value not in the correct format")

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        return DataActuator(data=self.output_value, units=self.axis_unit)

if __name__ == '__main__':
    main(__file__)
