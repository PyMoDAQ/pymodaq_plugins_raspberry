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
        {'title': 'Nombre de points:', 'name': 'nombre_points', 'type': 'int', 'value': 1000, 'min': 0, 'max': 100000},
        {'title': 'Duree', 'name': 'duree', 'type': 'int', 'value': 5, 'min': 0},
        {'title': 'Range', 'name': 'range', 'type': 'list', 'value': 10, 'limits': [10, 5, 2, 1]},
        {'title': 'Mode', 'name': 'mode', 'type': 'list', 'value': 'DIFFERENTIAL',
         'limits': ['SINGLE_END', 'DIFFERENTIAL']},
        {'title': 'Channel', 'name': 'channel', 'type': 'list', 'value': 0, 'limits': [0, 1, 2, 3, 4, 5, 6, 7]},
        {'title': 'Trigger Mode', 'name': 'trigger_mode', 'type': 'list', 'value': 'NONE',\
         'limits': ['NONE', 'RISING_EDGE', 'FALLING_EDGE', 'ACTIVE_HIGH', \
                    'ACTIVE_LOW']},
        {'title': 'Option', 'name': 'option', 'type': 'list', 'value': 'DEFAUT',\
         'limits': ['DEFAUT', 'NOSCALEDATA', 'NOCALIBRATEDATA']}

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
        self.controller.npts =  self.settings['nombre_points']




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

    def get_data(self, list_signal, samples, nb_channel_activated):
        list_signal_arranged = []
        for k in range(nb_channel_activated):
            list_signal_arranged.append([list_signal[k]])
        i = nb_channel_activated
        while i <= len(list_signal) - nb_channel_activated:
            for j in range(nb_channel_activated):
                list_signal_arranged[j].append(list_signal[i + j])
            i = i + nb_channel_activated
        return list_signal_arranged

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
        data = [5, 4, 3, 3, 45, 4, 6, 7, 8, 1, 2, 3, 4, 5, 2, 44, 33, 2, 1, 32]
        #data, timing = self.controller.generateur(self.settings['duree'])
        #data = data + np.random.random(len(data))
        xaxis = Axis('time', 'seconds',np.array([0,1,2,3,4,5,6,7,8,9]), 0 )

        king = self.get_data(data, 10, 2)


        self.dte_signal.emit(DataToExport('myplugin',
                                          data=[DataFromPlugins(name='Mock1', data=[np.array([5,6,7,4,2,4,5,6,8,65])],
                                                                dim='Data1D', labels=['grabed'],
                                                                axes=[xaxis])]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        return ''


if __name__ == '__main__':
    main(__file__, init=False)
