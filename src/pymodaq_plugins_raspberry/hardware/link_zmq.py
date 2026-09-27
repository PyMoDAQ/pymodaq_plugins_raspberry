# annotations such as list[str] | list[int] are evaluated at definition time before Python 3.10
from __future__ import annotations

import zmq
import json
import uuid

from pymodaq.utils.logger import set_logger, get_module_name
logger = set_logger(get_module_name(__file__))

DEFAULT_TIMEOUT_MS = 2000  # maximum wait for a raspberry's response, in milliseconds

class ZMQLink:
    """
    Set up the connection between the Pymodaq Dashboard and the raspberry's script
    --------------------
    To work, you need to install and launch the raspberry's script and get his ip address.
    """

    __isLinked : bool
    __context : zmq.Context
    __socket : zmq.Socket
    __id_socket : str
    __address : str
    __timeout_ms : int

    def __init__(self, ip_address : str, port : str, timeout_ms : int = DEFAULT_TIMEOUT_MS):
        """
        Init the object and start the connection
        --------------------
        :param ip_address: The raspberry's ip address
        :param port: The raspberry's communication port (5555 by default)
        :param timeout_ms: Maximum wait for a response, in milliseconds (2000 by default)
        :return: void - start the ZMQ connection
        """
        self.__isLinked = False
        self.__id_socket = ""
        self.__context = None
        self.__socket = None
        self.__address = ""
        self.__timeout_ms = int(timeout_ms)
        self.open(ip_address, port)
        return

    def open(self, ip_address : str, port : str):
        """
        Start the connection
        --------------------
        :param ip_address: The raspberry's ip address
        :param port: The raspberry's communication port (5555 by default)
        :return: void - Start the ZMQ connection
        """
        if ip_address is None:
            raise ValueError("ERROR - ip address not set")

        self.close()  # releases the previous socket and context when reopening
        self.__context = zmq.Context()
        self.__address = f"tcp://{ip_address}:{port}"
        self.__new_socket()

        # connect() is asynchronous and never fails, even towards a wrong address:
        # only an answered 'scan' request proves that the raspberry's script is reachable
        response = self.__write({"type": "scan"})
        self.__isLinked = isinstance(response, dict) and response.get("state") == "ACK"

        if self.__isLinked:
            logger.info(f"ZMQ LINK -> CONNECTED |"
                        f" IP ROUTER : {ip_address} |"
                        f" PORT ROUTER : {port} |"
                        f" ID DEALER : {self.__id_socket}")
        else:
            logger.warning(f"ZMQ LINK -> NOT CONNECTED | {self.__address} | {response}")
        return

    def close(self):
        """
        Stop the connection
        --------------------
        :return: Close the ZMQ connection
        """
        if self.__socket is not None:
            self.__socket.close(linger=0)
            self.__socket = None
        if self.__context is not None:
            self.__context.term()
            self.__context = None
        self.__isLinked = False
        return

    def __new_socket(self):
        """
        Create the DEALER socket, with bounded waits, and connect it to the raspberry
        --------------------
        :return: void - replace the current socket
        """
        if self.__socket is not None:
            self.__socket.close(linger=0)

        self.__socket = self.__context.socket(zmq.DEALER)
        self.__id_socket = str(uuid.uuid4())
        self.__socket.setsockopt_string(zmq.IDENTITY, self.__id_socket)
        self.__socket.setsockopt(zmq.RCVTIMEO, self.__timeout_ms)
        self.__socket.setsockopt(zmq.SNDTIMEO, self.__timeout_ms)
        self.__socket.setsockopt(zmq.LINGER, 0)
        self.__socket.connect(self.__address)

    def __write(self, request : dict):
        """
        Send a JSON request to the raspberry's script
        --------------------
        :param request: A dictionary formatted for a request
        :return: The response from the raspberry's script,
                 or {"state": "ERROR", "value": <message>} if the raspberry does not answer
        """
        if self.__socket is None:
            return {"state": "ERROR", "value": "link closed"}
        try:
            self.__socket.send(json.dumps(request).encode('utf-8'))
        except zmq.Again:
            return self.__timeout_error()
        return self.__read()

    def __read(self):
        """
        Receive a JSON response from the raspberry's script
        --------------------
        :return: The response from a request, sent by the raspberry's script,
                 or {"state": "ERROR", "value": <message>} on timeout or invalid response
        """
        try:
            inp_mq = self.__socket.recv()
        except zmq.Again:
            return self.__timeout_error()

        if isinstance(inp_mq, bytes):
            inp_mq = inp_mq.decode('utf-8')
        try:
            return json.loads(inp_mq)
        except ValueError:
            return {"state": "ERROR", "value": f"invalid response from {self.__address} : {inp_mq}"}

    def __timeout_error(self) -> dict:
        """
        Handle a raspberry that does not answer in time
        --------------------
        :return: A structured error response
        """
        message = f"TIMEOUT - no response from {self.__address} within {self.__timeout_ms} ms"
        logger.warning(message)
        # A late response would be read as the answer to the next request:
        # a new socket (new identity) discards it
        self.__new_socket()
        return {"state": "ERROR", "value": message}

    def get_link_status(self) -> bool:
        """
        Get the status of the link (True -> the raspberry answered, False -> no answer or closed)
        --------------------
        :return: The status of the connection
        """
        return self.__isLinked

    def multi_acquisition(self, addresses : list[str] | list[int] = None, pins : list[str] | list[int] = None) -> list | str:
        """
        Send a JSON multi-acquisition request to the raspberry's script
        --------------------
        :param addresses: A list of addresses linked to multiples components
        :param pins: A list of pins linked to multiples components
        :return: A list of value read by each component,
                order of the list : all the value of addresses, next, all the value of pins.
                A failed reading is replaced by nan (and logged with the raspberry's message)
        """
        if addresses is None and pins is None:
            raise ValueError("ERROR: hardware should have an address or a pin")

        output = {
                "type": "AQ-MULTI",
                "components": []
            }

        if addresses is not None :
            for i in range(len(addresses)):
                output["components"].append(
                    {
                        "register": "add",
                        "add": addresses[i]
                    }
                )

        if pins is not None:
            for i in range(len(pins)):
                output["components"].append(
                    {
                        "register": "pin",
                        "pin": pins[i]
                    }
                )

        inp_mq = self.__write(output)

        if not isinstance(inp_mq, dict):
            return "ERROR : input type incorrect, dict required"
        if inp_mq.get("state") != "ACK":
            return f"ERROR : {inp_mq.get('value')}"

        for i, elem in enumerate(inp_mq["value"]):
            if type(elem) != int and type(elem) != float:
                # log the raspberry's message before replacing it: nan cannot be mistaken for a measure
                component = output["components"][i] if i < len(output["components"]) else {}
                register = component.get("register", "?")
                reason = elem.get("value", elem) if isinstance(elem, dict) else elem
                logger.warning(f"READ ERROR - {register} {component.get(register, '?')} : {reason}")
                inp_mq["value"][i] = float('nan')

        return inp_mq["value"]

    def pilotage(self, value : str | int, pin : str | int) -> float | str:
        """
        Send a JSON control request to the raspberry's script
        --------------------
        Actuators are driven by their GPIO pin: the raspberry's script has no I2C actuator driver
        :param value: The value wanted for the component
        :param pin: The pin of the component
        :return: The value read by the component after control
        """
        inp_mq = self.__write(
            {
                "type": "PI",
                "register": "pin",
                "pin": pin,
                "value" : value
            }
        )

        if isinstance(inp_mq, dict):
            if inp_mq["state"] == "ACK":
                return inp_mq["value"]
            else:
                return f"{inp_mq['state']} : {inp_mq['value']}"
        else:
            return "ERROR : input type incorrect, dict required"

if __name__ == '__main__':
    """Quick link check from a terminal (read only, nothing is driven):
    python -m pymodaq_plugins_raspberry.hardware.link_zmq <ip address> [port]"""
    import sys

    if len(sys.argv) < 2:
        sys.exit("usage: python -m pymodaq_plugins_raspberry.hardware.link_zmq <ip address> [port]")

    link = ZMQLink(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '5555')
    print(f"Raspberry reachable : {link.get_link_status()}")
    link.close()
