import numpy as np
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

from pymodaq_plugins_raspberry.hardware.mcc128 import mcc128


class DAQ_1DViewer_BaoFadoua(DAQ_Viewer_base):
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
        {'title': 'Nombre de points:', 'name': 'nombre_points', 'type': 'int', 'value': 1000, 'min': 0},
        {'title': 'Duree:', 'name': 'duree', 'type': 'float', 'value': 5, 'min': 0}

    ]

    def ini_attributes(self):
        self.controller: mcc128 = None

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        ## TODO for your custom plugin
        if param.name() == "nombre_points":
           self.set_nb_points()

#        elif ...
        ##

    def set_nb_points(self):
        nb_points = self.settings['nombre_points']
        self.controller.npts = nb_points


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
                               new_controller=mcc128())

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
        data, timing = self.controller.generateur(self.settings['duree'])
        xaxis = Axis('time', 'seconds', timing, 0 )
        self.dte_signal.emit(DataToExport('myplugin',
                                          data=[DataFromPlugins(name='Mock1', data=[data],
                                                                dim='Data1D', labels=['grabed'],
                                                                axes=[xaxis])]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        return ''


if __name__ == '__main__':
    main(__file__, init=False)
