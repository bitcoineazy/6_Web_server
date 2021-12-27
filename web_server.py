from socket import socket
from threading import Thread, Lock
import logging
import datetime
import time
from wsgiref.handlers import format_date_time


class Client(Thread):
    def __init__(self, addr, conn):
        Thread.__init__(self, name=str(addr[0]) + ' ' + str(addr[1]))
        self.host = addr[0]
        self.port = addr[1]
        self.conn = conn

    def run(self):
        # Запуск сервера
        request = self.conn.recv(DATA_SIZE).decode()
        response = ''
        if request != '':
            print(request)
            headers = request.split('\n')
            webpage = headers[0].split()[1]
            if webpage == '/':
                webpage = '/index.html'
            elif '.' not in webpage:
                webpage += '.html'
            # 1. Проверка типа файла
            if webpage.split('.')[-1] in FILES:
                try:
                    try:
                        with open(DEFAULT_FOLDER + webpage, 'r') as f:
                            content = f.read()
                        response = f"""HTTP/1.1 200 OK
                                Date: {get_date()}
                                Content-type: text/html
                                Server: localhost
                                Content-length: {len(content)}
                                Connection: close\n\n""" + content
                    except UnicodeDecodeError:
                        # 8. Бинарный тип
                        with open(DEFAULT_FOLDER + webpage, 'rb') as f:
                            content = f.read()
                        response = f"""HTTP/1.1 200 OK
                                Date: {get_date()}
                                Content-type: image/png
                                Server: localhost
                                Content-length: {len(content)}
                                Connection: close\n\n"""
                    with LOCK:
                        logging.info(f"| {self.host} | {webpage} | 200")
                except FileNotFoundError:
                    # 3. Ошибка 404
                    response = "HTTP/1.0 404 NOT FOUND\n\nPage Not Found!"
                    with LOCK:
                        logging.info(f"| {self.host} | {webpage} | 404")
            else:
                if webpage.split(".")[-1] != "ico":
                    response = "HTTP/1.0 403 FORBIDDEN\n\nForbidden Error!"
                    with LOCK:
                        logging.info(f"| {self.host} | {webpage} | 403")
            if "Content-type: image/" in response:
                self.conn.send(response.encode() + content)
            else:
                self.conn.send(response.encode())
        self.conn.close()


settings = {}
# 2. Настройки сервера
with open('settings.txt', 'r') as f:
    for i in f.readlines():
        settings[i.split('=')[0]] = i.split('=')[1]
SERVER_HOST = settings['DEFAULT_HOST'].strip()
SERVER_PORT = int(settings['DEFAULT_PORT'])
DATA_SIZE = int(settings['DATA_SIZE'])
DEFAULT_FOLDER = settings['DEFAULT_FOLDER']
# 6. Определенные типы
FILES = ['html', 'js', 'png', 'jpg', 'jpeg']
LOCK = Lock()

# 5. Логи
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(funcName)s: %(message)s",
    handlers=[logging.FileHandler("logs/web_server.log"),
              logging.StreamHandler()],
    level=logging.INFO)


def get_date():
    # Текущую дата и время в формате Http header Date
    now = datetime.datetime.now()
    stamp = time.mktime(now.timetuple())
    return format_date_time(stamp)


def is_available_port(port):
    try:
        sock = socket()
        sock.bind(("", port))
        sock.close()
        logging.info(f"Порт {port} свободен")
        return True
    except OSError:
        logging.info(f"Порт {port} занят")
        return False


def main(server_host, server_port):
    sock = socket()
    if not is_available_port(server_port):
        logging.info(f"Порт по умолчанию {server_port} занят")
        port_available = False
        while not port_available:
            server_port += 1
            port_available = is_available_port(server_port)
    sock.bind((server_host, server_port))
    logging.info(f"Старт Web-сервера {server_host}, порт: {server_port}")
    sock.listen(3)
    clients = []
    while True:
        try:
            conn, addr = sock.accept()
            clients.append(Client(addr, conn))
            clients[-1].start()
            for cl in clients:
                if not cl.is_alive():
                    clients.remove(cl)
        except Exception as e:
            logging.error(str(e))
            break
    sock.close()


if __name__ == "__main__":
    main(SERVER_HOST, SERVER_PORT)
