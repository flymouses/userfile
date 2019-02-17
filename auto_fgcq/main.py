import logging
import time
from logging.handlers import RotatingFileHandler
import threading

import pyautogui as auto

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(),
                              RotatingFileHandler('main.log', maxBytes=31457280, backupCount=5)])


def log():
    return logging.getLogger(__name__)


pos = {
    'package': (),
    'gohome': (),
    'practice': ()
}


class UIOperation(object):

    def __init__(self, win):
        self._win = win

    def package_is_full(self):
        pass

    def sale_all(self):
        pass

    def open_package(self):
        pass

    def is_online(self):
        return False


class WorkerLog(object):
    name = ''

    def log_debug(self, msg):
        log().debug('{}: {}'.format(self.name, msg))

    def log_info(self, msg):
        log().info('{}: {}'.format(self.name, msg))

    def log_warning(self, msg):
        log().warning('{}: {}'.format(self.name, msg))

    def log_error(self, msg):
        log().error('{}: {}'.format(self.name, msg), exc_info=True)

    def log_error_and_raise_exception(self, msg):
        log().error('{}: {}'.format(self.name, msg), exc_info=True)
        raise Exception(msg)


class Actor(threading.Thread, WorkerLog):

    def __init__(self, title, win):
        self.win = win
        self.title = title
        super(Actor, self).__init__(name='Actor_{}'.format(self.title))
        self.win.resize(900, 500)
        self._ui = UIOperation(self.win)

    def run(self):
        self.log_info('logic start ... ')
        while True:
            if not self._ui.is_online():
                self.log_info('waite online...')
                continue
            time.sleep(60)


class Main(object):

    def __init__(self):
        self._ths = dict()

    def run(self):
        while True:
            try:
                for title, _ in auto.getWindows().items():
                    if not title.startswith('fgauto'):
                        continue
                    if title not in self._ths:
                        try:
                            win = auto.getWindow(title)
                            w = Actor(title, win)
                            w.setDaemon(True)
                            w.start()
                        except Exception as e:
                            log().error('new worker failed:{}'.format(e), exc_info=True)
                        else:
                            self._ths[title] = w
                    else:
                        pass
            except Exception as e:
                log().error('Main error {}'.format(e), exc_info=True)
            time.sleep(10)


if __name__ == '__main__':
    m = Main()
    m.run()
