"""
Auskunft-Protokoll
------------------
TCP überträgt einen *Bytestrom*, keine einzelnen Nachrichten. Ein recv()
kann eine halbe Nachricht liefern oder zwei Nachrichten auf einmal. Darum
braucht das Protokoll eine eindeutige Nachrichtengrenze (Framing):

- Jede Nachricht ist ein JSON-Objekt, kodiert als UTF-8 (Umlaute in
  Namen sind also erlaubt).
- Jede Nachricht endet mit einem Zeilenumbruch b"\\n". json.dumps()
  erzeugt nie einen echten Zeilenumbruch (er wird als "\\n" escaped),
  deshalb ist b"\\n" als Trennzeichen eindeutig.

Nachrichtenarten:

    Anfragen (Client -> Server)
        {"op": "GET", "name": "<Name>"}
        {"op": "GETALL"}

    Antworten (Server -> Client)
        {"status": "OK", "entries": {"<Name>": "<Nummer>", ...}}
        {"status": "NOT_FOUND", "name": "<Name>"}

Abfolge: Der Client baut eine Verbindung auf und kann darüber beliebig
viele Anfragen schicken. Auf jede Anfrage folgt genau eine Antwort
(strikt abwechselnd: Anfrage, Antwort, Anfrage, Antwort, ...). Schließt
der Client die Verbindung, wartet der Server auf den nächsten Client.
Auf eine ungültige Anfrage antwortet der Server nicht, sondern schließt
die Verbindung.
"""

import json
import logging
import socket

import const_cs
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)  # init loging channels for the lab

# Trennzeichen zwischen zwei Nachrichten im TCP-Bytestrom
DELIMITER = b"\n"

# Beispiel-Telefonbuch, falls dem Server keines übergeben wird
DEFAULT_PHONEBOOK = {
    "Alice": "0721 925-1234",
    "Bob": "0721 925-5678",
    "Charlie": "0721 925-9012",
    "Jürgen": "0721 925-3456",
}


def handle_request(phonebook, request):
    """
    Backend-Funktion: bildet eine Anfrage auf eine Antwort ab.

    Kennt keine Sockets, nur Dicts. Dadurch lässt sie sich im Unit-Test
    direkt aufrufen, ohne Netzwerk und ohne laufenden Server.
    Eine ungültige Anfrage löst eine Exception aus (KeyError, ValueError, ...).
    """
    op = request["op"]  # which operation?

    if op == "GET":
        name = request["name"]
        if name in phonebook:
            return {"status": "OK", "entries": {name: phonebook[name]}}
        return {"status": "NOT_FOUND", "name": name}

    if op == "GETALL":
        return {"status": "OK", "entries": phonebook}

    raise ValueError(f"Unbekannte Operation: {op!r}")


class Channel:
    """
    Kapselt einen verbundenen TCP-Socket und überträgt darüber ganze
    Protokollnachrichten (Python-Dicts) statt roher Bytes.

    Client und Server nutzen beide diese Klasse, damit Kodierung und
    Framing nur an einer Stelle implementiert sind.
    """

    def __init__(self, sock):
        self.sock = sock
        # Bytes, die schon empfangen, aber noch nicht als Nachricht
        # ausgeliefert wurden (z.B. der Anfang der nächsten Nachricht)
        self._buffer = b""

    def send(self, message):
        """Kodiert ein Dict als JSON + UTF-8 + Trennzeichen und sendet es."""
        data = json.dumps(message).encode("utf-8") + DELIMITER
        # sendall() statt send(): send() darf weniger Bytes verschicken als
        # übergeben (bei großen Nachrichten wie GETALL mit 500 Einträgen
        # durchaus möglich). sendall() wiederholt, bis alles raus ist.
        self.sock.sendall(data)

    def receive(self):
        """
        Liest genau eine Nachricht und gibt sie als Dict zurück.
        Gibt None zurück, wenn die Gegenseite die Verbindung geschlossen hat.
        """
        # So lange Daten anhängen, bis eine vollständige Nachricht
        # (bis zum Trennzeichen) im Puffer liegt
        while DELIMITER not in self._buffer:
            chunk = self.sock.recv(4096)
            if not chunk:  # b"" heißt: Gegenseite hat die Verbindung geschlossen
                return None
            self._buffer += chunk
        # Erste Nachricht abschneiden, den Rest für den nächsten Aufruf aufheben
        line, self._buffer = self._buffer.split(DELIMITER, 1)
        return json.loads(line.decode("utf-8"))

    def close(self):
        """Schließt den Socket."""
        self.sock.close()


class Server:
    """Der Auskunft-Server: nimmt Verbindungen an und beantwortet Anfragen."""

    _logger = logging.getLogger("vs2lab.lab1.clientserver.Server")

    def __init__(self, phonebook=None):
        # Datenebene: das Telefonbuch liegt "in-memory" als Dictionary vor
        self.phonebook = DEFAULT_PHONEBOOK if phonebook is None else phonebook
        self._serving = True

        # Socket-Lebenszyklus, Schritt 1: Socket erzeugen
        # AF_INET = IPv4, SOCK_STREAM = TCP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )  # prevents errors due to "addresses in use"
        self._logger.info("Server socket created")

        # Schritt 2: an Adresse und Port binden
        self.sock.bind((const_cs.HOST, const_cs.PORT))
        # accept() soll nicht ewig blockieren, damit serve() regelmäßig
        # prüfen kann, ob es beendet werden soll (_serving == False)
        self.sock.settimeout(3)
        self._logger.info("Server bound to socket %s", self.sock)

    def _serve_connection(self, channel, address):
        """Beantwortet Anfragen eines Clients, bis dieser die Verbindung schließt."""
        while True:
            # Schritt 5: Anfrage empfangen
            request = channel.receive()
            if request is None:
                break  # Client hat die Verbindung geschlossen
            self._logger.info("Received request from %s: %s", address, request)

            # Anfrage verarbeiten (Verarbeitungsebene)
            response = handle_request(self.phonebook, request)

            # Schritt 6: Antwort senden
            channel.send(response)
            self._logger.info(
                "Sent response to %s: status %s", address, response["status"]
            )

    def serve(self):
        """Hauptschleife des Servers. Läuft, bis _serving auf False gesetzt wird."""
        # Schritt 3: auf eingehende Verbindungen hören
        # (1 = höchstens eine wartende Verbindung in der Warteschlange)
        self.sock.listen(1)
        self._logger.info("Server listening on %s:%s", const_cs.HOST, const_cs.PORT)

        while (
            self._serving
        ):  # as long as _serving (checked after connections or socket timeouts)
            try:
                # Schritt 4: Verbindung annehmen. accept() liefert einen
                # *neuen* Socket nur für diesen Client; self.sock bleibt der
                # "Empfangssocket" für weitere Verbindungen.
                (connection, address) = self.sock.accept()
            except socket.timeout:
                continue  # niemand hat sich verbunden -> _serving erneut prüfen

            self._logger.info("Accepted connection from %s", address)
            channel = Channel(connection)
            try:
                self._serve_connection(channel, address)
            except Exception as error:  # pylint: disable=broad-except
                # Ein kaputter oder abgestürzter Client darf nicht den ganzen
                # Server beenden: nur diese Verbindung aufgeben
                self._logger.warning("Dropping connection to %s: %r", address, error)
            finally:
                # Schritt 7: Verbindungssocket schließen
                channel.close()
                self._logger.info("Closed connection to %s", address)

        # Schritt 8: Empfangssocket schließen, Server ist beendet
        self.sock.close()
        self._logger.info("Server down.")


class Client:
    """
    Der Auskunft-Client. Seine öffentlichen Methoden get() und getall()
    bilden die Auskunft-API, die die Benutzerschnittstelle aufruft.
    """

    logger = logging.getLogger("vs2lab.lab1.clientserver.Client")

    def __init__(self):
        # Socket erzeugen und mit dem Server verbinden. connect() blockiert,
        # bis der Server die Verbindung mit accept() angenommen hat.
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )  # AF_INET = IPv4 SOCK_STREAM = TCP
        sock.connect((const_cs.HOST, const_cs.PORT))  # aus cer const datei
        self.channel = Channel(sock)
        self.logger.info("Client connected to socket %s", sock)

    def _request(self, request):
        """Sendet eine Anfrage und wartet auf die zugehörige Antwort."""
        self.channel.send(request)
        self.logger.info("Sent request: %s", request)
        response = self.channel.receive()
        if response is None:
            raise ConnectionError("Server hat die Verbindung geschlossen")
        self.logger.info("Received response: status %s", response["status"])
        return response

    def get(self, name):
        """
        API-Operation GET: sucht einen Namen im Telefonbuch.
        Gibt die Telefonnummer zurück oder None, wenn der Name fehlt.
        """
        response = self._request({"op": "GET", "name": name})
        if response["status"] == "NOT_FOUND":
            return None
        return response["entries"][name]

    def getall(self):
        """API-Operation GETALL: gibt das ganze Telefonbuch als Dict zurück."""
        return self._request({"op": "GETALL"})["entries"]

    def close(self):
        """Verbindung schließen. Danach ist der Server frei für den nächsten Client."""
        self.channel.close()
        self.logger.info("Client down.")
