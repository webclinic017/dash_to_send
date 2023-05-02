import logging


class DashLoggerHandler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.queue = []

    def emit(self, record):
        msg = self.format(record)
        self.queue.append(msg)


logger = logging.getLogger('werkzeug')
logger.setLevel(logging.INFO)

# Create a StreamHandler and set its logging level to INFO
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

dashLoggerHandler = DashLoggerHandler()
logger.addHandler(dashLoggerHandler)
