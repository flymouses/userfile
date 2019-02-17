import logging
import time
from logging.handlers import RotatingFileHandler

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(),
                              RotatingFileHandler('main.log', maxBytes=31457280, backupCount=5)])


def log():
    return logging.getLogger(__name__)


def main():
    log().info('[main] start ...')
    while True:
        for actor in load_actors():  # 读取配置文件，读到所有的角色信息
            if not has_win(actor):  # 如果没有启动相关的进程，启动
                create_win(actor)
        time.sleep(5)


if __name__ == '__main__':
    main()
