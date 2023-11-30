import numpy as np

from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

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

    hardware_averaging = True
    live_mode_available = True

    params = comon_parameters + [
        {'title': 'Zoom:', 'name': 'zoom', 'type': 'slide', 'value': 1.0, 'min': 0., 'max': 1., 'subtype': 'linear'},
        {'title': 'Brightness:', 'name': 'brightness', 'type': 'slide', 'value': 50, 'min': 0, 'max': 100,
         'subtype': 'linear', 'int': True},
        {'title': 'Contrast:', 'name': 'contrast', 'type': 'slide', 'value': 0, 'min': -100, 'max': 100,
         'subtype': 'linear', 'int': True},
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
        if param.name() == "a_parameter_you've_added_in_self.params":
            self.controller.your_method_to_apply_this_param_change()
        #elif ...

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
                               new_controller=PiCamera2())

        # config = self.controller.create_preview_configuration()
        # self.controller.configure(config)
        self.capture_config = self.controller.create_still_configuration()

        print(self.controller.camera_controls)
        print(self.controller.camera_properties)
        print(self.controller.capture_metadata())
        self.controller.start(show_preview=True)

        # self.controller.resolution = (self.width, self.height)
        # # self.camera.resolution = (1648, 928)
        # self.controller.framerate = 32  # nombres d'images par secondes
        #
        # self.controller.rotation = 180
        #
        # self.camera.zoom = (0, 0, 1, 1)
        #
        # # Produit un tableau tridimensionnel RGB à partir d'une capture RGB
        # # self.rawCapture = PiRGBArray(self.camera, size=(self.width, self.height))
        # self.rawCapture = PiRGBArray(self.camera, size=(self.width, self.height))

        info = "Whatever info you want to log"
        initialized = True
        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        if self.controller is not None:
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
        if 'wait_time' in kwargs:
            self.wait_time = kwargs['wait_time']


        for ind in range(Naverage):
            if self.live:
                array = self.controller.capture_array("main")
            else:
                array = self.controller.switch_mode_and_capture_array(self.capture_config, "main")
            if len(array.shape) == 2:
                arrays = [array]
            elif len(array.shape) == 3:
                arrays = [array[..., ind] for ind in range(array.shape[2])]
            else:
                arrays = [array[..., ind, 0] for ind in range(array.shape[2])]  # TODO: check this with alpha
            if ind == 0:
                dwa_camera = DataFromPlugins('PiCamera', data=arrays)
            else:
                dwa_camera = dwa_camera.average(DataFromPlugins('PiCamera', data=arrays),
                                                weight= ind+1)
        if self.live:
            self.dte_signal_temp.emit(DataToExport('myplugin', data=[dwa_camera]))
        else:
            self.dte_signal.emit(DataToExport('myplugin', data=[dwa_camera]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        return ''


if __name__ == '__main__':
    main(__file__, init=False)
