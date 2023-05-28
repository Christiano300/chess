from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection
from subprocess import STDOUT, Popen, PIPE
from queue import Queue
from threading import Event, Thread
import sys
from io import StringIO
from time import sleep

ONE_INT_ARG_TOKENS = ("depth", "seldepth", "time", "nodes", "multipv",
                  "currmovenumber", "hashfull", "nps", "tbhits", "cpuload")

Move = tuple[tuple[int, int], tuple[int, int]]

_ArgValue = dict[str, str | list[str] | dict[str, int]] | list[str] | list[Move]
_Argument = tuple[str, _ArgValue]


class OutputManager:
    def __init__(self, queue: Queue):
        self.stringio = StringIO()
        self.queue = queue

    def write(self, data):
        self.stringio.write(data)
        if data == "\n":
            line = self.read().strip()
            if line != "":
                self.queue.put(line)

    def flush(self):
        self.stringio.flush()

    def read(self):
        """
        Reads the input and clears the buffer
        """
        value = self.stringio.getvalue()
        self.stringio = StringIO()
        return value


class EngineManager:
    def __init__(self, engine: str, out_queue: Queue[_Argument]):
        self.engine = engine
        self._out_queue: Queue[str] = Queue()
        self._out = OutputManager(self._out_queue)
        self.out_queue = out_queue
        self.buffer = []
        self.process = None
        self.ready_condition = Event()
        self.ready_condition.clear()

    def start(self):
        self.process = Popen(self.engine, stdin=PIPE, stdout=PIPE,
                             stderr=STDOUT, universal_newlines=True)
        self._write_raw("isready\n")

        def read():
            while True:
                # print("read iter")
                # print("read data: ")
                data = self.process.stdout.read(1)  # type: ignore
                if not data:
                    break
                self._out.write(data)
                self._out.flush()
                # sys.stdout.write(data)    # temp
                # sys.stdout.flush()        # temp

        self.writer = Thread(target=read, daemon=True)
        self.writer.start()

        def handle_output():
            while True:
                # print("output iter")
                output = self._out_queue.get()
                if not self.ready_condition.is_set():
                    if output == "readyok":
                        self.ready_condition.set()
                        print("engine ready")
                    else:
                        continue
                elif output.startswith("info"):
                    parts = output.split()
                    self.out_queue.put(("info", parse_info(parts)))
                
                elif output.startswith("bestmove"):
                    res = {}
                    parts = output.split()
                    res["move"] = parts[1]
                    if (len(parts)) == 4:
                        res["ponder"] = parts[3]
                    self.out_queue.put(("bestmove", res))
                
                elif output.startswith("Nodes searched"):
                    self.out_queue.put(("moves", [uci_to_move(i[:4]) for i in self.buffer]))
                    print("Engine output moves")
                    self.buffer.clear()

                else:
                    self.buffer.append(output)

                self._out_queue.task_done()

        self.handler = Thread(target=handle_output, daemon=True)
        self.handler.start()

        # try:
        #     while True:
        #         d = sys.stdin.read(1)       # temp
        #         if not d:
        #             break
        #         self.write(self.process, d)

        # except EOFError:
        #     pass

    def _write_raw(self, message):
        self.process.stdin.write(message)  # type: ignore
        self.process.stdin.flush()        # type: ignore

    def send(self, command: str):
        self.ready_condition.wait()
        if not command.endswith("\n"):
            command += "\n"
        print(f"engine recieved {command}")
        self._write_raw(command)


def parse_info(args: list[str]) -> _ArgValue:
    res = {}
    i = 1
    while i < len(args):
        arg = args[i]
        if arg in ONE_INT_ARG_TOKENS:
            res[arg] = int(args[i + 1])
            i += 2

        elif arg == "score":
            score = {}
            i += 1
            if args[i] == "cp":
                score["cp"] = args[i + 1]
                i += 2
            if args[i] == "mate":
                score["mate"] = args[i + 1]
                i += 2
            if args[i] in ("upperbound", "lowerbound"):
                score[args[i]] = 1
                i += 1
            res["score"] = score

        elif arg == "currmove":
            res["currmove"] = args[i + 1]
            i += 2
            
        elif arg == "pv":
            res["pv"] = args[i + 1:]
            break
        
        elif arg == "string":
            res["string"] = " ".join(args[i + 1:])
            break

        else:
            print("recieved invalid argument: " + arg)
            quit()

    return res

def engine_loop(conn: Connection):
    print("engine loop started")
    engine_queue = Queue()
    engine = EngineManager("engines/stockfish.exe", engine_queue)
    engine.start()
    
    def recv():
        while True:
            conn.send(engine_queue.get())
    
    def send():
        while True:
            engine.send(conn.recv())
    
    Thread(target=recv, daemon=True).start()
    Thread(target=send, daemon=True).start()

def get_engine_process():
    ui_conn, engine_conn = Pipe()
    engine_process = Process(target=engine_loop, args=(engine_conn,))
    engine_process.start()
    return ui_conn, engine_process

def get_engine_thread():
    ui_conn, engine_conn = Pipe()
    engine_thread = Thread(target=engine_loop, args=(engine_conn,), daemon=True)
    # engine_thread.start()
    return ui_conn, engine_thread

def uci_to_move(uci: str) -> Move:
    return ((ord(uci[0]) - 97, int(uci[1]) - 1), (ord(uci[2]) - 97, int(uci[3]) - 1))


def move_to_uci(move: Move) -> str:
    return f"{chr(move[0][0] + 97)}{move[0][1] + 1}{chr(move[1][0] + 97)}{move[1][1] + 1}"

def main():
    def queue(output_queue: Queue):
        while True:
            res = output_queue.get()
            print(f"{res}")
            output_queue.task_done()

    def send_in(em: EngineManager):
        try:
            while True:
                char = sys.stdin.read(1)
                if not char:
                    break
                em._write_raw(char)
        except EOFError:
            pass

    q_out: Queue[_Argument] = Queue()

    em = EngineManager(r'C:\Users\Christian\Desktop\stockfish', q_out)
    em.start()

    Thread(target=queue, args=(q_out,)).start()
    Thread(target=send_in, args=(em,)).start()


if __name__ == '__main__':
    # main()
    Thread(target=main).start()
