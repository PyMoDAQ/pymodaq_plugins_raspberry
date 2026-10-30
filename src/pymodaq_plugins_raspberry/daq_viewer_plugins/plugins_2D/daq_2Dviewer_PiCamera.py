import numpy as np
from qtpy import QtWidgets

from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter
from pymodaq_utils.logger import set_logger, get_module_name

logger = set_logger(get_module_name(__file__))

from picamera2 import Picamera2


class DAQ_2DViewer_PiCamera(DAQ_Viewer_base):
    """ Instrument plugin class for a 2D viewer.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Viewer module through inheritance via
    DAQ_Viewer_base. It makes a bridge between the DAQ_Viewer module and the Python wrapper of a particular instrument.

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.

             """

    supported_platforms = ('linux',)  # a Raspberry Pi library
    supported_architectures = ('aarch64', 'armv7l')

    hardware_averaging = True
    live_mode_available = False

    params = comon_parameters + [
        {'title': 'Resolution:', 'name': 'resolution', 'type': 'list', 'value': 'low', 'limits': ['low', 'high']},
        {'title': 'Exposure Time:', 'name': 'exposure_time', 'type': 'int', 'value': 1000, 'suffix': 'µs'},
        
        #{'title': 'Zoom:', 'name': 'zoom', 'type': 'slide', 'value': 1.0, 'min': 0., 'max': 1., 'subtype': 'linear'},
        #{'title': 'Brightness:', 'name': 'brightness', 'type': 'slide', 'value': 50, 'min': 0, 'max': 100,
        # 'subtype': 'linear', 'int': True},
        #{'title': 'Contrast:', 'name': 'contrast', 'type': 'slide', 'value': 0, 'min': -100, 'max': 100,
        # 'subtype': 'linear', 'int': True},
    ]

    def ini_attributes(self):
        #  TODO declare the type of the wrapper (and assign it to self.controller) you're going to use for easy
        #  autocompletion
        self.controller: PiCamera2 = None

        # TODO declare here attributes you want/need to init with a default value
        self.live = False

        self.x_axis = None
        self.y_axis = None
        self.width = 640
        self.height = 480

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        # TODO for your custom plugin
        if param.name() == "resolution":
            if param.value() == 'low':
                self.controller.switch_mode(self.low_res_config)
            else:
                self.controller.switch_mode(self.high_res_config)
        #elif ...
        
        if param.name() == "exposure_time":
            self.controller.set_controls({"ExposureTime": param.value()}) #We test with exposure time 5000
        

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
        if self.is_master:
            self.controller = Picamera2()
        else:
            self.controller = controller
        
        min_exp, max_exp, default_exp = self.controller.camera_controls["ExposureTime"]
        logger.debug(f'Exposure times: {(min_exp, max_exp, default_exp)}')
        self.settings.child('exposure_time').setLimits((min_exp, max_exp))
        self.settings.child('exposure_time').setValue(default_exp)
        
        self.low_res_config = self.controller.create_preview_configuration()
        self.high_res_config = self.controller.create_still_configuration()

        self.controller.configure(self.low_res_config)
        

        logger.info(self.controller.camera_controls)
        logger.info(self.controller.camera_properties)
        #print(self.controller.capture_metadata())
        self.controller.start()

        info = "Whatever info you want to log"
        initialized = True
        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        if self.controller is not None and self.is_master:
            self.controller.close()

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

        self.camera_done = False
        self.Naverage = Naverage
        if 'live' in kwargs:
            self.live = kwargs['live']
        else:
            self.live = False
        logger.debug(f'live: {self.live}')
        if 'wait_time' in kwargs:
            self.wait_time = kwargs['wait_time']
            logger.debug(self.wait_time)
            
        self.grab(Naverage)
            
    def grab(self, Naverage):
        for ind in range(Naverage):
            array = self.controller.capture_array("main")
            logger.debug(f'array shape: {array.shape}')
            if len(array.shape) == 2:
                arrays = [array]
            elif len(array.shape) == 3:
                arrays = [array[..., ind] for ind in range(3)] #alpha is with the last index equal to 4, we may skip it!
            else:
                raise ValueError(f'The array shape is {array.shape} and is not handled')
            if ind == 0:
                dwa_camera = DataFromPlugins('PiCamera', data=arrays)
            else:
                dwa_camera = dwa_camera.average(DataFromPlugins('PiCamera', data=arrays),
                                                weight= ind+1)
        self.dte_signal.emit(DataToExport('myplugin', data=[dwa_camera]))
        

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.live = False
        return ''


if __name__ == '__main__':
    main(__file__, init=False)

