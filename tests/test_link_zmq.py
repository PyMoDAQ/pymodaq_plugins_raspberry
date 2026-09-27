# -*- coding: utf-8 -*-
"""
Tests of the PyMoDAQ <-> Raspberry chain without hardware.

A fake ROUTER server runs in a thread and answers like the raspberry's script;
a real ZMQLink is plugged to it. Written with unittest: runs with
`python -m unittest discover tests` (no extra package) and with pytest.
"""
import json
import math
import threading
import time
import unittest

import zmq

from pymodaq_plugins_raspberry.hardware.link_zmq import ZMQLink


class FakeRaspberry:
    """Fake raspberry's script: a ROUTER socket answering with a user-given function"""

    def __init__(self, answer):
        self.answer = answer  # function(request: dict) -> response dict, or None to stay silent
        self.requests = []
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.port = self.socket.bind_to_random_port("tcp://127.0.0.1")
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        while True:
            try:
                if not self.socket.poll(100):
                    continue
                client_id, message = self.socket.recv_multipart()
            except zmq.ZMQError:
                return  # socket closed by stop()
            request = json.loads(message)
            self.requests.append(request)
            response = self.answer(request)
            if response is not None:
                self.socket.send_multipart([client_id, json.dumps(response).encode('utf-8')])

    def stop(self):
        self.socket.close(linger=0)
        self.thread.join(timeout=1)
        self.context.term()


def bench_answer(request: dict):
    """Answers like the simulated bench: one sensor at 0x48, one actuator on pin 18"""
    if request["type"] == "scan":
        return {"state": "ACK", "value": {"actuator": [], "detector": []}}
    if request["type"] == "AQ-MULTI":
        values = []
        for component in request["components"]:
            if component.get("add") == "0x48":
                values.append(21.5)
            else:
                values.append({"state": "ERROR", "value": "Capteur introuvable"})
        return {"state": "ACK", "value": values}
    if request["type"] == "PI":
        if request.get("pin") == "18":
            return {"state": "ACK", "value": int(request["value"])}
        return {"state": "ERROR", "value": f"Pin {request.get('pin')} introuvable."}
    return {"state": "ERROR", "value": f"Type de requête inconnu : '{request['type']}'"}


def within(seconds, function, *args, **kwargs):
    """Call function in a thread: a blocked call fails the test instead of freezing the whole run"""
    result = {}
    thread = threading.Thread(target=lambda: result.update(value=function(*args, **kwargs)), daemon=True)
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        raise AssertionError(f"{function.__name__} blocked for more than {seconds} s")
    return result["value"]


class TestZMQLink(unittest.TestCase):

    link = None

    def start(self, answer, timeout_ms=1000):
        self.server = FakeRaspberry(answer)
        self.link = within(5, ZMQLink, "127.0.0.1", str(self.server.port), timeout_ms)

    def tearDown(self):
        if self.link is not None:  # a blocked link cannot be closed from this thread
            self.link.close()
        self.server.stop()

    def test_acquisition(self):
        self.start(bench_answer)
        self.assertTrue(self.link.get_link_status())
        self.assertEqual(self.link.multi_acquisition(addresses=["0x48"]), [21.5])
        self.assertEqual(self.server.requests[-1],
                         {"type": "AQ-MULTI", "components": [{"register": "add", "add": "0x48"}]})

    def test_pilotage(self):
        self.start(bench_answer)
        self.assertEqual(self.link.pilotage(200, pin="18"), 200)
        self.assertEqual(self.server.requests[-1],
                         {"type": "PI", "register": "pin", "pin": "18", "value": 200})

    def test_error_response(self):
        self.start(bench_answer)
        # a failed reading is nan in place, the other values are kept, nothing is raised
        values = self.link.multi_acquisition(addresses=["0x48", "0x99"])
        self.assertEqual(values[0], 21.5)
        self.assertTrue(math.isnan(values[1]))
        # a refused control is returned as an error message
        self.assertTrue(self.link.pilotage(10, pin="7").startswith("ERROR"))

    def test_timeout(self):
        answered = {"scan": True}
        # answers the connection check, then stays silent like a frozen raspberry
        self.start(lambda request: bench_answer(request) if answered.pop(request["type"], False) else None,
                   timeout_ms=300)
        self.assertTrue(self.link.get_link_status())
        start = time.monotonic()
        result = within(5, self.link.multi_acquisition, addresses=["0x48"])
        self.assertLess(time.monotonic() - start, 2)
        self.assertIsInstance(result, str)
        self.assertIn("TIMEOUT", result)


if __name__ == '__main__':
    unittest.main()
