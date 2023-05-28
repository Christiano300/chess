import sys
import subprocess
from subprocess import Popen, PIPE
import threading


def run():
    p = Popen(r'C:\Users\Christian\Desktop\stockfish', stdin=PIPE, stdout=PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    sys.stdout.write("Started Local Terminal...\r\n\r\n")

    ""
    
    def writeall(p):
        while True:
            # print("read data: ")
            data = p.stdout.read(1)
            if not data:
                break
            # sys.stdout.write(data)
            # sys.stdout.flush()
            print(repr(data), end=' ')
            sys.stdout.flush()

    writer = threading.Thread(target=writeall, args=(p,))
    writer.start()

    try:
        while True:
            d = sys.stdin.read(1)
            if not d:
                break
            write(p, d)

    except EOFError:
        pass

def write(process, message):
    process.stdin.write(message)
    process.stdin.flush()
    
run()
