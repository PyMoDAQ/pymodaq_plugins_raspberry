import numpy as np
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

from pymodaq_plugins_raspberry.hardware.mcc128 import mcc128
from daqhats import   mcc128 ,OptionFlags, AnalogInputMode, TriggerModes


class DAQ_1DViewer_daqhats(DAQ_Viewer_base):
    """ Instrument plugin class for a 1D viewer.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Viewer module through inheritance via
    DAQ_Viewer_base. It makes a bridge between the DAQ_Viewer module and the Python wrapper of a particular instrument.

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.
         


    """
    params = comon_parameters+[
        {'title': 'Samples:', 'name': 'samples', 'type': 'int', 'value': 1000, 'min': 0, 'max' : 100000},
        {'title': 'Frequency :', 'name': 'frequency', 'type': 'int', 'value': 100, 'min': 0},
        {'title': 'Range', 'name': 'range', 'type': 'list', 'value':10 , 'limits':[10, 5, 2 ,1] },
        {'title': 'Mode', 'name': 'mode', 'type': 'list', 'value': 'SINGLE_END', 'limits': ['SINGLE_END', 'DIFFERENTIAL']},
        {'title': 'Single_End_Channel', 'name': 'channel_single', 'type': 'list', 'value': 'CH0H', 'limits': ['CHOH', 'CH1H', 'CH2H', 'CH3H', 'CH0L',\
                                                                                                         'CH1L', 'CH2L', 'CH3L']},
        {'title': 'Trigger Mode', 'name': 'trigger_mode', 'type': 'list', 'value': 'NONE', 'limits': ['NONE', 'RISING_EDGE' ,'FALLING_EDGE', 'ACTIVE_HIGH', \
                                                                                                      'ACTIVE_LOW']},
        {'title': 'Option' , 'name':'option', 'type': 'list', 'value': 'DEFAUT', 'limits': ['DEFAUT', 'NOSCALEDATA', 'NOCALIBRATEDATA']}


    ]

    def ini_attributes(self):
        self.controller: mcc128 = None
        self.option = OptionFlags.DEFAULT
        #self.controller.a_in_mode_write(0)
        #self.controller.a_in_range_write(0)
        self.mode = 0
        self.range = 0



    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        ## TODO for your custom plugin
        if param.name() == 'mode':
           self.set_mode()

        elif param.name() == 'range':
            self.set_range()
        ##

    def scan_data(self):
        self.controller.a_in_scan_start(1, self.settings['sample'], self.settings['frequency'], self.option)
        voltage = self.controller.a_in_scan_read(self.settings['sample'], 0)
        self.controller.a_in_scan_stop()
        self.controller.a_in_scan_cleanup()
        return voltage

    def set_mode(self):
        if self.settings['mode'] == 'SINGLE_ENDED':
            self.mode =0
        else:
            self.mode =1
        self.controller.a_in_mode_write(self.mode)

    def set_range(self):
        if self.settings['range'] == 10:
            self.range = 0
        elif self.settings['range'] == 5:
            self.range = 1
        elif self.settings['range'] == 2:
            self.range = 2
        elif self.settings['range'] == 1:
            self.range = 3
        self.controller.a_in_range_write(self.range)


    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        self.ini_detector_init(old_controller=controller,
                               new_controller=mcc128(0))

        info = "Whatever info you want to log"
        initialized = True
        return info, initialized

    def close(self):
        pass
        """Terminate the communication protocol"""


    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """

        ##synchrone version (blocking function)
        data = self.scan_data()
        xaxis =  np.arange(0,(self.settings['sample'])*1/self.settings['frequency'], 1/self.settings['frequency'] )

        self.dte_signal.emit(DataToExport('myplugin',
                                          data=[DataFromPlugins(name='Mock1', data=[data],
                                                                dim='Data1D', labels=['grabed'],
                                                                axes=[xaxis])]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        return ''


if __name__ == '__main__':
    main(__file__, init=False)
