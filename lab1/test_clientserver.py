"""
Unit-Tests für den Telefonauskunftsdienst.

Zwei Gruppen:
- TestBackend testet clientserver.handle_request() direkt, ganz ohne Netzwerk.
- TestAuskunftService testet die Auskunft-API (Client.get/getall) über
  echte TCP-Sockets gegen einen Server, der in einem Thread läuft.
"""

import logging
import threading
import unittest

import clientserver
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

# Telefonbuch mit 500 Einträgen für den GETALL-Test ("Für Experten")
BIG_PHONEBOOK = {f"Person{i:03d}": f"0721 {i:06d}" for i in range(500)}
BIG_PHONEBOOK["Jürgen"] = "0721 925-3456"  # ein Eintrag mit Umlaut

SMALL_PHONEBOOK = {"Alice": "123", "Bob": "456"}


class TestBackend(unittest.TestCase):
    """Backend-Funktion ohne Sockets."""

    def test_get_found(self):
        response = clientserver.handle_request(SMALL_PHONEBOOK, {"op": "GET", "name": "Alice"})
        self.assertEqual(response, {"status": "OK", "entries": {"Alice": "123"}})

    def test_get_not_found(self):
        response = clientserver.handle_request(SMALL_PHONEBOOK, {"op": "GET", "name": "Zoe"})
        self.assertEqual(response, {"status": "NOT_FOUND", "name": "Zoe"})

    def test_getall(self):
        response = clientserver.handle_request(SMALL_PHONEBOOK, {"op": "GETALL"})
        self.assertEqual(response, {"status": "OK", "entries": SMALL_PHONEBOOK})

    def test_unknown_op(self):
        with self.assertRaises(ValueError):
            clientserver.handle_request(SMALL_PHONEBOOK, {"op": "DELETE"})


class TestAuskunftService(unittest.TestCase):
    """Auskunft-API über echte Sockets."""
    _server = clientserver.Server(BIG_PHONEBOOK)  # create single server in class variable
    _server_thread = threading.Thread(target=_server.serve)  # define thread for running server

    @classmethod
    def setUpClass(cls):
        cls._server_thread.start()  # start server loop in a thread (called only once)

    def setUp(self):
        super().setUp()
        self.client = clientserver.Client()  # create new client for each test

    def test_get(self):
        self.assertEqual(self.client.get("Person042"), "0721 000042")

    def test_get_umlaut(self):
        self.assertEqual(self.client.get("Jürgen"), "0721 925-3456")

    def test_get_not_found(self):
        self.assertIsNone(self.client.get("Niemand"))

    def test_getall_500(self):
        # Die Antwort ist deutlich größer als ein recv(4096), testet also,
        # dass Channel.receive() mehrere Stücke korrekt zusammensetzt
        self.assertEqual(self.client.getall(), BIG_PHONEBOOK)

    def test_several_requests_one_connection(self):
        # Mehrere Anfragen über dieselbe Verbindung
        self.assertEqual(self.client.get("Person000"), "0721 000000")
        self.assertEqual(len(self.client.getall()), 501)
        self.assertEqual(self.client.get("Person499"), "0721 000499")

    def test_malformed_request(self):
        # Am Client vorbei Müll senden: der Server schließt diese Verbindung,
        # läuft aber weiter und bedient den nächsten Client
        self.client.channel.sock.sendall(b"kein json\n")
        self.assertIsNone(self.client.channel.receive())
        other = clientserver.Client()
        self.assertEqual(other.get("Person001"), "0721 000001")
        other.close()

    def tearDown(self):
        self.client.close()  # terminate client after each test

    @classmethod
    def tearDownClass(cls):
        cls._server._serving = False  # break out of server loop. pylint: disable=protected-access
        cls._server_thread.join()  # wait for server thread to terminate


if __name__ == '__main__':
    unittest.main()
