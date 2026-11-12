import logging

import rpc
from context import lab_channel, lab_logging

logger = logging.getLogger('vs2lab.lab2.rpc.runsrv')


def main():
    lab_logging.setup(stream_level=logging.INFO)
    chan = lab_channel.Channel()
    chan.channel.flushall()
    logger.debug('Flushed all redis keys.')

    srv = rpc.Server()
    logger.info('Asynchroner RPC-Server bereit. Beenden mit Strg+C.')
    try:
        srv.run()
    except KeyboardInterrupt:
        logger.info('Server wird beendet.')
    finally:
        srv.chan.leave('server')


if __name__ == '__main__':
    main()
