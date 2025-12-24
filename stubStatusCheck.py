import time

serverStartStatus = set()


def server_check(server):
    while True:
        if server in serverStartStatus:
            time.sleep(1)
            return
        else:
            time.sleep(1)
