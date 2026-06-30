import zmq
import json
import uuid

from pymodaq.utils.logger import set_logger, get_module_name
logger = set_logger(get_module_name(__file__))

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

    def __init__(self, ip_address : str, port : str):
        """
        Init the object and start the connection
        --------------------
        :param ip_address: The raspberry's ip address
        :param port: The raspberry's communication port (5555 by default)
        :return: void - start the ZMQ connection
        """
        self.__isLinked = False
        self.__id_socket = ""
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
        assert ip_address is not None, "ERROR - ip address not set"

        self.__context = zmq.Context()
        self.__socket = self.__context.socket(zmq.DEALER)

        self.__id_socket = str(uuid.uuid4())
        self.__socket.setsockopt_string(zmq.IDENTITY, self.__id_socket)

        self.__socket.connect(f"tcp://{ip_address}:{port}")
        self.__isLinked = True

        print(f"ZMQ LINK -> CONNECTED |"
              f" IP ROUTER : {ip_address} |"
              f" PORT ROUTER : {port} |"
              f" ID DEALER : {self.__id_socket}")
        return

    def close(self):
        """
        Stop the connection
        --------------------
        :return: Close the ZMQ connection
        """
        self.__socket.close()
        self.__isLinked = False
        return

    def __write(self, request : dict):
        """
        Send a JSON request to the raspberry's script
        --------------------
        :param request: A dictionary formatted for a request
        :return: The response from the raspberry's script
        """
        self.__socket.send(json.dumps(request).encode('utf-8'))
        return self.__read()

    def __read(self):
        """
        Receive a JSON response from the raspberry's script
        --------------------
        :return: The response from a request, sent by the raspberry's script
        """
        inp_mq = self.__socket.recv()
        if isinstance(inp_mq, bytes):
            inp_mq = inp_mq.decode('utf-8')
        return json.loads(inp_mq)

    def get_link_status(self) -> bool:
        """
        Get the status of the socket (True -> open, False -> closed)
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
                order of the list : all the value of addresses, next, all the value of pins
        """
        assert addresses is not None or pins is not None, "ERROR: hardware should have an address or a pin"

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

        for i, elem in enumerate(inp_mq["value"]):
            if type(elem) != int and type(elem) != float:
                inp_mq["value"][i] = -1
                logger.warning(f"READ ERROR - {inp_mq['value'][i]}")

        return inp_mq["value"]

    def pilotage(self, value : str | int, address : str | int = None, pin : str | int = None) -> float | str:
        """
        Send a JSON control request to the raspberry's script
        --------------------
        :param value: The value wanted for the component
        :param address: The address of the component
        :param pin: The pin of the component
        :return: The value read by the component after control
        """
        assert address is not None or pin is not None, "ERROR: hardware should have an address or a pin"
        assert not (address is not None and pin is not None), \
            "ERROR: only one of address or pin should be given, not both"

        inp_mq = None

        if address is not None:
            inp_mq = self.__write(
                {
                    "type": "PI",
                    "register": "add",
                    "add": address,
                    "value" : value
                }
            )
        elif pin is not None:
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
    """Main section used during development tests"""

    Capteur1 = ZMQLink("172.17.50.41", '5555')

    print(Capteur1.multi_acquisition(addresses=["0x49"]))
    print(Capteur1.pilotage("0", pin="18"))

    Capteur1.close()
