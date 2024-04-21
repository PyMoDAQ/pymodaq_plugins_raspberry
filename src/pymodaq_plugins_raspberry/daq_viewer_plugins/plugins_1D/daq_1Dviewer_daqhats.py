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
        {'title': 'External_clock', 'name': 'extclock_mode', 'type': 'bool', 'value': False},
        {'title': 'External sampling rate', 'name': 'extclock_rate', 'type': 'int', 'value': 0},
        {'title': 'Number of samples:', 'name': 'num_sample', 'type': 'int', 'value': 1000, 'min': 0},
        {'title': 'Sampling rate :', 'name': 'sampling_rate', 'type': 'int', 'value': 10000, 'min': 0, 'max': 100000},
        {'title': 'Range', 'name': 'range', 'type': 'list', 'value': 10, 'limits': [10, 5, 2, 1]},
        {'title': 'Mode', 'name': 'mode', 'type': 'list', 'value': 'SINGLE_END',
         'limits': ['SINGLE_ENDED', 'DIFFERENTIAL']},
        {'title': "Channel", 'name': 'channel_on', 'type': 'group', 'children': [
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

    def __init__(self, parent=None, params_state=None):
        super().__init__(parent, params_state)
        self.num_channels = None

    def ini_attributes(self):
        self.controller: mcc128 = None
        self.option = 0
        self.mode = 0
        self.range = 0
        self.channel_mask = 0
        self.num_channels = 0
        self.data_signal = []
        self.list_channel_names = []

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
        elif param.name() in iter_children(self.settings.child('channel_on'), []):
            self.active_channel()
        elif param.name() == 'sampling_rate':
            sample_rate_real = self.controller.a_in_scan_actual_rate(self.num_channels, param.value())
            param.setValue(sample_rate_real)

    def scan_data(self, totalsamples: int, scan_rate: int, name_channel: int):

        """
        This start a hardware-paced analog input channel scan . Then this function reads and return the data from the
        buffer.The aggregate sampling rate of all activated channels can't exceed 100kS/s

        =================    ================
        Channels activate    Scan rate (kS/s)
        =================    ================
            1                      100
            2                      50
            3                      33,33
            4                      25
            5                      20
            6                      16,67
            7                      14,29
            8                      12,50
        ==============      ================

        Parameters
        ----------
        totalsamples: int
            The numbers of samples which we want to aquire
        scan_rate: int
            The sampling rate of each channel
        name_channel: int
            The bit mask of the channels activated

        Returns: list
            The list of data scanned
        """

        self.controller.a_in_scan_start(name_channel, totalsamples, scan_rate, self.option)
        voltage = self.controller.a_in_scan_read_numpy(totalsamples, 0.5)
        self.controller.a_in_scan_stop()
        self.controller.a_in_scan_cleanup()
        return voltage.data

    def set_range(self):

        """ This sets the analog input range to one of these values:
            +/- 10V
            +/- 5V
            +/- 2V
            +/- 1V
        """

        if self.settings['range'] == 10:
            self.range = AnalogInputRange['BIP_10V'].value
        elif self.settings['range'] == 5:
            self.range = AnalogInputRange['BIP_5V'].value
        elif self.settings['range'] == 2:
            self.range = AnalogInputRange['BIP_2V'].value
        elif self.settings['range'] == 1:
            self.range = AnalogInputRange['BIP_1V'].value
        self.controller.a_in_range_write(self.range)

    def set_mode(self):

        """ This sets the analog input mode to one of two values
            * Single ended
            * Differential
        """

        if self.settings['mode'] == 'SINGLE_ENDED':
            self.mode = AnalogInputMode.SE.value
        elif self.settings['mode'] == 'DIFFERENTIAL':
            self.mode = AnalogInputMode.DIFF.value
        self.controller.a_in_mode_write(self.mode)

    def set_trigger(self):

        """
        This reads the sets the external trigger mode input of the card
        There are 4 type available TRIGGER mode:
            *RISING_EDGE: Start the scan when the trigger signal transition from LOW to HIGH
            *FALLING_EDGE: Start the scan when the trigger signal transition from HIGH to LOW
            *ACTIVE_HIGH: Start the scan when the trigger signal is HIGH
            *ACTIVE_LOW: Start the scan when the trigger signal is LOW

        """

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

    def active_channel(self):

        """
        This function reads the states of channels on the interface and sets the bit mask of the active channels,
        the number of activated channels, and a list of the names of these channels.

        """

        bit_mask = 0  # the bit mask of the active channels
        number_channels = 0  # the number of activated channels
        name_channels = [] # the list of the names of these channels
        if self.settings['channel_on', 'CH0H']:
            bit_mask = bit_mask + 1
            number_channels += 1
            name_channels.append('CH0H')
        if self.settings['channel_on', 'CH1H']:
            bit_mask = bit_mask + 2
            number_channels += 1
            name_channels.append('CH1H')
        if self.settings['channel_on', 'CH2H']:
            bit_mask = bit_mask + 4
            number_channels += 1
            name_channels.append('CH2H')
        if self.settings['channel_on', 'CH3H']:
            bit_mask = bit_mask + 8
            number_channels += 1
            name_channels.append('CH3H')
        if self.settings['channel_on', 'CH0L']:
            bit_mask = bit_mask + 16
            number_channels += 1
            name_channels.append('CH0L')
        if self.settings['channel_on', 'CH1L']:
            bit_mask = bit_mask + 32
            number_channels += 1
            name_channels.append('CH1L')
        if self.settings['channel_on', 'CH2L']:
            bit_mask = bit_mask + 64
            number_channels += 1
            name_channels.append('CH2L')
        if self.settings['channel_on', 'CH3L']:
            bit_mask = bit_mask + 128
            number_channels += 1
            name_channels.append('CH3L')
        self.channel_mask, self.num_channels, self.label = bit_mask, number_channels, name_channels

    def get_data(self, list_signal_non_arranged, nb_channel_activated):
        """

        This methode arranges the list of data received from activated channels. It converts this list of data into a list
        of numpy arrays. The order of each array corresponds to the order of each activated channel on the interface (from CH0H to CH3L)

        Example: When you activate 2 channels CHOH and CH2L, this function will return a list of 2 arrays: the first one is
        data of channel CH0H and the second one is data of channel CH2L

        Parameters
        ----------
        list_signal_non_arranged : list
           List of data obtained by function scan_data()
        nb_channel_activated : int
            The quantity of activated channels

        Returns
        -------
        list_signal_arranged : list of numpy array
            list of data of each channel arranged

        """
        list_signal_arranged = []
        if len(list_signal_non_arranged) != 0:
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

        self.option = 0
        self.channel_mask = 1

        self.settings.child('channel_on', 'CH0H').setValue(True)

        self.data_signal = self.scan_data(self.settings['num_sample'], self.settings['sampling_rate'],
                                          self.channel_mask)
        xaxis = Axis('time', 'seconds', np.arange(0, self.settings['num_sample'] * 1 / self.settings['sampling_rate'],
                                                  1 / self.settings['sampling_rate']), 0)

        self.dte_signal.emit(DataToExport('myplugin', data=[DataFromPlugins(name='Mock1', data=self.data_signal,
                                                                            dim='Data1D', labels=['CH0H'],
                                                                            axes=[xaxis])]))

        info = ""
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

        num_sample = self.settings['num_sample']
        freq = self.settings['sampling_rate']

        self.option = 0

        # Set up mode Trigger
        if self.settings['trigger_active'] == True:
            self.option += OptionFlags['EXTTRIGGER'].value

        # Set up mode External clock
        if self.settings['extclock_mode'] == True:
            self.option += OptionFlags['EXTCLOCK'].value
            external_spl_rate = self.settings['extclock_rate']
            if external_spl_rate == 0:
                raise ValueError("Sampling rate cannot be zero")
            else:
                xaxis = Axis('time', 'seconds', np.arange(0, num_sample * 1 / external_spl_rate, 1 / external_spl_rate),
                             0)  # Redefine the x-axis when the external clock is used
        else:
            xaxis = Axis('time', 'seconds', np.arange(0, num_sample * 1 / freq, 1 / freq), 0)

        self.channel_mask, self.num_channels, self.list_channel_names = self.active_channel()

        signal = self.scan_data(num_sample, freq, self.channel_mask)

        if len(signal) != 0:  # Condition to avoid empty data error
            self.data_signal = self.get_data(signal, self.num_channels)

        self.dte_signal.emit(DataToExport('myplugin', data=[DataFromPlugins(name='Mock1', data=self.data_signal,
                                                                            dim='Data1D',
                                                                            labels=self.list_channel_names,
                                                                            axes=[xaxis])]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        return ''


if __name__ == '__main__':
    main(__file__, init=False)
