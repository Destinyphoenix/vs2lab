import logging
import threading
import time

import constRPC

from context import lab_channel

logger = logging.getLogger('vs2lab.lab2.rpc')


class DBList:
    def __init__(self, basic_list):
        self.value = list(basic_list)

    def append(self, data):
        self.value = self.value + [data]
        return self


class Client:
    def __init__(self):                             # self bezeichnet innerhalb der Methode genau das Objekt, an dem gerade gearbeitet wird. verweist auf das Objekt cl
        self.chan = lab_channel.Channel()           # erzeugt das Channel Objekt chan - stellt funktionen zum senden und empfangen bereit
        self.client = self.chan.join('client')      # mit der Methode join() von unserem Channel Objekt wird der Client beim Kan angemeldet und liefert seine Mitglieds-ID zurück - kruz: self.client enthält eine ID
        self.server = None                          # server und antwort-thread sind noch nicht eingetragen
        self.worker = None                          # im aktuellen Client Objekt cl wird im Attribut worker der Wert none gespeichert

    def run(self):
        self.chan.bind(self.client)                 # verknüpft den laufenden prozess meit seiner Kanal-ID
        self.server = self.chan.subgroup('server')  # Abfrage des angemeldetetn Servers
        if len(self.server) != 1:
            raise RuntimeError('Starten Sie genau einen RPC-Server vor dem Client.')

    def stop(self):
        # Erst abmelden, wenn Ergebnis und Callback verarbeitet wurden.
        if self.worker is not None:
            self.worker.join()
        self.chan.leave('client')

    def append(self, data, db_list, callback):
        """Nach dem ACK zurueckkehren; das Ergebnis erhaelt der Callback."""
        assert isinstance(db_list, DBList)
        if not callable(callback):
            raise TypeError('callback muss eine aufrufbare Funktion sein.')
        if self.worker is not None and self.worker.is_alive():                  # prüfung verhindert, dass derselbe Client einen weiteren RPC startet, während der verherige Antwort-Thread noch arbeitet
            raise RuntimeError('Dieser Client bearbeitet bereits einen RPC.')

        msglst = (constRPC.APPEND, data, db_list)  # message payload
        self.chan.send_to(self.server, msglst)  # send msg to server

        # Nur auf die Annahme warten, noch nicht auf das Ergebnis.
        sender, acknowledgement = self.chan.receive_from(self.server)
        if acknowledgement != constRPC.OK:
            raise RuntimeError('Unerwartete Antwort statt ACK.')
        logger.info('ACK von Server %s erhalten.', sender)

        self.worker = threading.Thread(         # erzeugt im Client-Objekt ein neues Thread-Objekt, dieses beschreibt eine auszuführende Aufgabe welche wir später starten und ihren Zustand abfragen können
            # Folgende Argumente werden beim Thread-Objekt hinterlegt
            target=self._receive_result,    # es soll die Methode receive_result (von unserem konkreten Client-Objekt damit kann der thrad auf dessen self.chan und self.server zugreifen) ausgeführt werden
            args=(callback,),               # die receive_result methode soll das argument callback bekommen
            name='RPC-Antwort',             # der name des thrads für die anzeige
        )
        self.worker.start()                 # Thread starten: ein zusätzlicher Ausführungsstrang im Client Prozes beginnt - _receive_result(callback) wird ausgeführt
        return self.worker

    def _receive_result(self, callback):    # Dieser Ausführungsstrang wartet auf das Ergebnis des Servers und ruft danach den Callback auf (Der Hauptthread kann derweil andere eilen ausführen)
        # Blockiert nur diesen Thread. Der Hauptthread kann weiterarbeiten.
        sender, result = self.chan.receive_from(self.server)
        logger.info('Ergebnis von Server %s erhalten.', sender)
        callback(result)


class Server:

    # srv verweist auf das Server-Objekt. self.sever enthält die Kanal-ID des Server Objekts
    def __init__(self):                                 # self bezeichnet das Server-Objekt welches in runsrv.py erzuegt wurde
        self.chan = lab_channel.Channel()               # speichert einen Verweis auf ein neues Channel-Objekt
        self.server = self.chan.join('server')          # .join('server') meildet den Server beim Kanal an und die zurückgegebene Mitglieds-ID wird in sel.server gespeichert
        self.timeout = 3                                # speichert Zahl 3. diese wird später als Empfangs-Timeout verwendet

    @staticmethod                                       # die Methode bekommt kein automatisches self-Argument (sie benötigt nur die beiden übergebenen Werte data und db_list)
    def append(data, db_list):                          # diese append methode gehört zur klasse Server. sie prüft das übergebene Objekt und ruft anschließen dessen append() auf
        assert isinstance(db_list, DBList)              # -stellt sicher, dass db_list ein Obkekt der Klasse DBList ist
        return db_list.append(data)

    def run(self):
        self.chan.bind(self.server)                     # bind() verknüpft den laufenden Serverprozess mit seiner Kanal-ID 
        while True:                                     # startet schleife die immer läuft. server soll nach einer Anfrage für die nächste bereitbleiben
            msgreq = self.chan.receive_from_any(self.timeout)  # wait for any request - auf nachricht von einem beliebigen kanalmitglied warten
            if msgreq is not None:
                client = msgreq[0]  # see who is the caller - Absender-ID
                msgrpc = msgreq[1]  # fetch call & parameters - Nachrichteninhalt
                if constRPC.APPEND == msgrpc[0]:        # Server prüft welche Operation gewünscht ist
                    self.chan.send_to({client}, constRPC.OK)    # annahme bestätigen mit der Empfänger-ID und dem ACK (constRPC.OK)
                    logger.info('ACK an Client %s gesendet; arbeite 10 Sekunden.', client)  # log ausgabe
                    time.sleep(10)                              # Server simuliert lange Bearbeitung. Server Thread wartet währenddesen kann der Clientprozess weiterarbeiten
                    result = self.append(msgrpc[1], msgrpc[2])  # Operation append ausführen. result ist eine lokale Variable in Server.run() sie verweist auf dieses Objekt
                    self.chan.send_to({client}, result)         # Server sendet result an dieselbe Client-ID. Der Antwort-Thread des Clients empfängt result und dieser ruft danach den Callback auf
                    logger.info('Ergebnis an Client %s gesendet.', client) # log ausgabe
                else:
                    pass  # unsupported request, simply ignore
