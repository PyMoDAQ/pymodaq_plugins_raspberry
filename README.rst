Raspberry plugin
################

.. the following must be adapted to your developed package, links to pypi, github  description...

.. image:: https://img.shields.io/pypi/v/pymodaq_plugins_raspberry.svg
   :target: https://pypi.org/project/pymodaq_plugins_raspberry/
   :alt: Latest Version

.. image:: https://readthedocs.org/projects/pymodaq/badge/?version=latest
   :target: https://pymodaq.readthedocs.io/en/stable/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_raspberry/workflows/Upload%20Python%20Package/badge.svg
   :target: https://github.com/PyMoDAQ/pymodaq_plugins_raspberry
   :alt: Publication Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_raspberry/actions/workflows/Test.yml/badge.svg
    :target: https://github.com/PyMoDAQ/pymodaq_plugins_raspberry/actions/workflows/Test.yml


PyMoDAQ plugin to control an experimental device (or test bench) through a
Raspberry Pi.

A small server runs **on the Raspberry Pi** and drives the components of the
device (sensors, actuators); PyMoDAQ talks to that server over the network. From
PyMoDAQ you then get a detector (to read the sensors) and an actuator (to drive
the outputs) as if they were local instruments.


Authors
=======

* Sebastien J. Weber  (sebastien.weber@cnrs.fr)
* Fabien Villedieu


Instruments
===========

Below is the list of instruments included in this plugin

Actuators
+++++++++

* **MoveRasp**: drive the outputs of the device (e.g. PWM or all-or-nothing
  actuators) wired to the Raspberry

Viewer0D
++++++++

* **ViewRasp**: read the sensors of the device (e.g. I2C sensors) wired to the
  Raspberry
  
Viewer1D
++++++++

* **daqhats**: control of the MCC128 DAQ hat for analog input/output


Viewer2D
++++++++

* **picamera**: control of the integrated pi camera using the Picamera2 library.
  This viewer relies on ``picamera2``, which is **only available on Linux/Raspberry**
  (it depends on a Linux-only package). On a Windows/macOS control machine the
  plugin still installs and works for the remote actuator/detector, but the
  PiCamera viewer is simply not loaded.


Adapting the plugin to your setup
=================================

Beware: some plugins are meant to be used with PyMoDAQ installed on the Raspberry directly:

 * **daqhats**
 * **picamera**
 
Some other are using the raspberry and the components plugged on it as an external DAQ connected to a computer. 
The computer and the Raspberry communicate over ZMQ:

* **MoveRasp**
* **ViewRasp**


ZMQ plugins
===========

Communication
+++++++++++++

The plugin is built to be adapted to a wide range of benches. Three things can be
changed independently:

* **The PyMoDAQ ⇄ Raspberry communication.** It uses a ZeroMQ link by default,
  but the transport is isolated behind a dedicated layer: it can be replaced by
  another communication mean (serial, HTTP, ...) without touching the rest. On the
  Raspberry side, implement the transport interface (``ITransport``) and wire it in
  ``main.py``; on the PyMoDAQ side, provide a class exposing the same methods as
  ``ZMQLink`` (``hardware/Link_PMQ.py``).

* **The Raspberry ⇄ components communication.** Each sensor and each actuator is
  driven by an interchangeable driver selected from the bench configuration
  (``src_raspberry/config.py``). Adding a new component is just a matter of writing
  a small driver class and registering it:

  - a new sensor → a class in ``src_raspberry/hardware/sensors.py`` registered in
    ``SENSOR_DRIVER_REGISTRY``;
  - a new actuator control mode → a class in ``src_raspberry/hardware/actuators.py``
    registered in ``ACTUATOR_DRIVER_REGISTRY`` (``PWM`` and ``DIGITAL`` are provided).

* **The set of JSON requests.** The PyMoDAQ side and the Raspberry side exchange
  JSON messages, and new request types can be added easily on both ends:

  - **Raspberry side**: add an entry to the routing table ``_requestHandlers`` in
    ``src_raspberry/handlers/json_handler.py`` with its handler method, which
    delegates any hardware access to the hardware backend (``IHardwareBackend``);
  - **PyMoDAQ side**: add a method to ``ZMQLink`` (``hardware/Link_PMQ.py``) that
    builds and sends the new request, then call it from the move/viewer plugins.


Raspberry-side server
+++++++++++++++++++++

The code that must run on the Raspberry Pi lives in the ``src_raspberry/`` folder
at the root of this repository. It is organised in independent layers — network
transport, JSON request handling, and hardware communication — each behind an
interface, which is what makes the points above easy to adapt. See
``src_raspberry/README.md`` for installation and the JSON protocol.


Installation instructions
+++++++++++++++++++++++++

* PyMoDAQ’s version >= 5
* On a Windows/macOS control machine the plugin installs as is; the ``picamera2``
  dependency (Linux-only) is automatically skipped, so only the PiCamera viewer is
  unavailable there.
* The Raspberry-side server requires the I2C bus and the ``pigpio`` daemon
  (see ``src_raspberry/README.md``).
  
  
 OnRaspberry Plugins
 ===================
* PyMoDAQ’s version >= 5

