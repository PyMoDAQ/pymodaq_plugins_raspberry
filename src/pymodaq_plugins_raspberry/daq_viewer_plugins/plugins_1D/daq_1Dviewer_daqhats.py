import numpy as np
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter
from daqhats import mcc128, OptionFlags, AnalogInputMode, TriggerModes, AnalogInputRange
from pymodaq.utils.parameter.utils import iter_children


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
    params = comon_parameters + [
        {'title': 'Trigger Active', 'name': 'trigger_active', 'type': 'bool', 'value': False},
        {'title': 'Trigger Mode', 'name': 'trigger_mode', 'type': 'list', 'value': 'RISING_EDGE',
         'limits': ['RISING_EDGE', 'FALLING_EDGE', 'ACTIVE_HIGH',
                    'ACTIVE_LOW']},
        {'title': 'External_clock', 'name': 'extclock', 'type': 'bool', 'value': False},
        {'title': 'Multichannel', 'name': 'multi', 'type': 'bool', 'value': False},
        {'title': 'Number of sample:', 'name': 'num_sample', 'type': 'int', 'value': 1000, 'min': 0, 'max': 100000},
        {'title': 'Frequency :', 'name': 'frequency', 'type': 'int', 'value': 100, 'min': 0},
        {'title': 'Range', 'name': 'range', 'type': 'list', 'value': 10, 'limits': [10, 5, 2, 1]},
        {'title': 'Mode', 'name': 'mode', 'type': 'list', 'value': 'SINGLE_END',
         'limits': ['SINGLE_ENDED', 'DIFFERENTIAL']},
        {'title': 'Channel _1', 'name': 'channel_single', 'type': 'list', 'value': 'CH0H',
         'limits': ['CH0H', 'CH1H', 'CH2H', 'CH3H', 'CH0L',
                    'CH1L', 'CH2L', 'CH3L']},
        {'title': 'Channel_2_', 'name': 'channel_single_2', 'type': 'list', 'value': 'CH1H',
         'limits': ['CH0H', 'CH1H', 'CH2H', 'CH3H', 'CH0L',
                    'CH1L', 'CH2L', 'CH3L']},
        {'title': "Channel", 'name': 'channel_active', 'type': 'group', 'children': [
            {'title': 'CH0H', 'name': 'CH0H', 'type': 'bool', 'value': False},
            {'title': 'CH1H', 'name': 'CH1H', 'type': 'bool', 'value': False},
            {'title': 'CH2H', 'name': 'CH2H', 'type': 'bool', 'value': False},
            {'title': 'CH3H', 'name': 'CH3H', 'type': 'bool', 'value': False},
            {'title': 'CH0L', 'name': 'CH0L', 'type': 'bool', 'value': False},
            {'title': 'CH1L', 'name': 'CH1L', 'type': 'bool', 'value': False},
            {'title': 'CH2L', 'name': 'CH2L', 'type': 'bool', 'value': False},
            {'title': 'CH3L', 'name': 'CH3L', 'type': 'bool', 'value': False}
        ]}

    ]
    """Initialize the attributes

    """

    def __init__(self, parent=None, params_state=None):
        super().__init__(parent, params_state)
        self.num_channels = None

    def ini_attributes(self):
        self.controller: mcc128(0) = None
        self.option = 0
        self.mode = 0
        self.range = 0
        self.input_channel_1 = 1
        self.input_channel_2 = 2
        self.channel_mask = 0
        self.num_channels = 0

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """

        if param.name() == 'mode':
            self.set_mode()
        elif param.name() == 'range':
            self.set_range()
        elif param.name() == 'trigger_mode':
            self.set_trigger()
        # elif param.name() == 'channel_active':
        # self.active_channel()
        elif param.name() in iter_children(self.settings.child('channel_active'), []):
            self.active_channel()

    def scan_data(self, totalsamples: int, scan_freq: int, name_channel: int):

        self.controller.a_in_scan_start(name_channel, totalsamples, scan_freq, self.option)
        voltage = self.controller.a_in_scan_read_numpy(totalsamples, 0.5)
        self.controller.a_in_scan_stop()
        self.controller.a_in_scan_cleanup()
        return voltage.data

    """ This sets the analog input range to one of the value
        +/- 10V
        +/- 5V
        +/- 2V
        +/- 1V 
    """

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

    # MODE

    def set_mode(self):
        if self.settings['mode'] == 'SINGLE_ENDED':
            self.mode = 0
        elif self.settings['mode'] == 'DIFFERENTIAL':
            self.mode = 1
        self.controller.a_in_mode_write(self.mode)

    """
    This reads the sets the external trigger mode input of the card
    There are 4 type available TRIGGER mode:
        *RISING_EDGE: Star scan when the external trigger is from LOW to HIGH
        *FALLING_EDGE: Star scan when the external trigger is from HIGH to LOW
        *ACTIVE_HIGH: Start scan when the external trigger is HIGH
        *ACTIVE_LOW: Start scan when the external trigger is LOW
    
    """

    def set_trigger(self):
        global Tmode
        mode_trigger = self.settings['trigger_mode']
        if mode_trigger == 'RISING_EDGE':
            Tmode = 0
        elif mode_trigger == 'FALLING_EDGE':
            Tmode = 1
        elif mode_trigger == 'ACTIVE_HIGH':
            Tmode = 2
        elif mode_trigger == 'ACTIVE_LOW':
            Tmode = 3
        self.controller.trigger_mode(Tmode)


    """

    This function reads the states of channels on the interface and returns the bit mask of the active channels, 
    the number of activated channels, and a list of the names of these channels.
    
    ----------------------
    Return 
    
        count: Bit mask of the channels activated
        number_channels: Number of channels activated
        name_channels: List of the activated channels 
        
    """

    def active_channel(self):
        count = 0
        number_channels = 0
        name_channel = []
        # for param in self.settings.child():
        # if param.name() == 'channel_active':
        if self.settings['channel_active', 'CH0H']:
            count = count + 1
            number_channels += 1
            name_channel.append('CH0H')
        if self.settings['channel_active', 'CH1H']:
            count = count + 2
            number_channels += 1
            name_channel.append('CH1H')
        if self.settings['channel_active', 'CH2H']:
            count = count + 4
            number_channels += 1
            name_channel.append('CH2H')
        if self.settings['channel_active', 'CH3H']:
            count = count + 8
            number_channels += 1
            name_channel.append('CH3H')
        if self.settings['channel_active', 'CH0L']:
            count = count + 16
            number_channels += 1
            name_channel.append('CH0L')
        if self.settings['channel_active', 'CH1L']:
            count = count + 32
            number_channels += 1
            name_channel.append('CH1L')
        if self.settings['channel_active', 'CH2L']:
            count = count + 64
            number_channels += 1
            name_channel.append('CH2L')
        if self.settings['channel_active', 'CH3L']:
            count = count + 128
            number_channels += 1
            name_channel.append('CH3L')
        return count, number_channels, name_channel

    """
    This used to convert the initial list of data which is returned by the function "self.scan_data" into 
    a list of arrays in which each array corresponds to the data of each active channel 
    
    Parameter:
        
        list_signal_non_arranged (list): the list of data which is returned by the function "self.scan_data"
        nb_channel_activated (int): the number of active channels
    
    Return:
        list_signal_arranged (list): the list of arranged data  
    """
    def get_data(self, list_signal_non_arranged, nb_channel_activated):
        list_signal_arranged = []
        for k in range(nb_channel_activated):
            list_signal_arranged.append(np.array(list_signal_non_arranged[k]))
        i = nb_channel_activated
        while i <= len(list_signal_non_arranged) - nb_channel_activated:
            for j in range(nb_channel_activated):
                list_signal_arranged[j] = np.append(list_signal_arranged[j], list_signal_non_arranged[i + j])
            i = i + nb_channel_activated
        return list_signal_arranged

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

        self.option = 0

        if self.settings['trigger_active']:
            self.option += 8

        if self.settings['extclock']:
            self.option += 4

        self.channel_mask, self.num_channels, label = self.active_channel()

        num_sample = self.settings['num_sample']
        freq = self.settings['frequency']

        # get and store the list of acquired data into signal
        signal = self.scan_data(num_sample, freq, self.channel_mask)
        # arrange the data of 'signal'
        # 'data_signal' is a list of array in which each array corresponds to the acquired data of each active channel
        data_signal = self.get_data(signal, self.num_channels)

        xaxis = Axis('time', 'seconds', np.arange(0, num_sample * 1 / freq, 1 / freq), 0)

        self.dte_signal.emit(DataToExport('myplugin', data=[DataFromPlugins(name='Mock1', data=data_signal,
                                                                            dim='Data1D', labels=label,
                                                                            axes=[xaxis])]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        return ''


if __name__ == '__main__':
    main(__file__, init=False)
