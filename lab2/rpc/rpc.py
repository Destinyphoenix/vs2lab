
import constRPC
import time
import threading

from context import lab_channel


class DBList:
    def __init__(self, basic_list):
        self.value = list(basic_list)

    def append(self, data):
        self.value = self.value + [data]
        return self


class Client:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.client = self.chan.join('client')
        self.server = None

    def run(self):
        self.chan.bind(self.client)
        self.server = self.chan.subgroup('server')

    def stop(self):
        self.chan.leave('client')

    def append(self, data, db_list, callback):
        assert isinstance(db_list, DBList)

        # Request senden
        msglst = (constRPC.APPEND, data, db_list)
        self.chan.send_to(self.server, msglst)

        # Thread zum Warten auf das Ergebnis starten
        def wait_for_result():
            msgrcv = self.chan.receive_from(self.server)

            # Nachrichteninhalt auswerten
            message = msgrcv[1]

            if message[0] == "RESULT":
                callback(message[1])

        thread = threading.Thread(target=wait_for_result)
        thread.start()

        # Auf ACK warten
        msgrcv = self.chan.receive_from(self.server)

        return thread


class Server:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.server = self.chan.join('server')
        self.timeout = 3

    @staticmethod
    def append(data, db_list):
        assert isinstance(db_list, DBList)
        return db_list.append(data)

    def run(self):
        self.chan.bind(self.server)

        while True:
            msgreq = self.chan.receive_from_any(self.timeout)

            if msgreq is not None:
                client = msgreq[0]
                msgrpc = msgreq[1]

                if constRPC.APPEND == msgrpc[0]:

                    # ACK sofort zurücksenden
                    self.chan.send_to({client}, ("ACK", None))

                    # Lange Ausführungszeit simulieren
                    time.sleep(10)

                    # Funktion ausführen
                    result = self.append(msgrpc[1], msgrpc[2])

                    # Ergebnis zurücksenden
                    self.chan.send_to({client}, ("RESULT", result))

                else:
                    pass
