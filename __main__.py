# __main__.py
import subprocess
import threading
import time

from .output_handlers import *
from .output_listener import *
from .procman import Process

import gc

start_time = time.time()

def process_manager_test():
    print('Running Process Test ...')

    with Process('ping 127.0.0.1') as proc:
        tail = TailOutputHandler()

        proc.on_process_output_event += tail
        proc.on_process_output_event += PrintOutputHandler()

        proc.start()
        proc.wait_for_exit(timeout=120)

        time.sleep(3)

        print()
        for line in tail.lines:
            print(line)

        print("Took {} sec".format((time.time() - start_time) - 3))


def output_listener_test():
    threads = []

    def stuff(output):
        cmd = 'ping 127.0.0.1'

        try:
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output.stdout = proc.stdout
            output.stderr = proc.stderr
            output.start_listener()
        finally:
            try:
                proc.wait()
            except subprocess.TimeoutExpired:
                proc.terminate()

                if not proc.poll():
                    proc.kill()
            except KeyboardInterrupt:
                proc.terminate()

                if not proc.poll():
                    proc.kill()

    def tailer(output):
        from datetime import datetime
        tail_handler = TailOutputHandler()

        output.on_output_event += tail_handler

        time.sleep(10)

        for line in tail_handler.lines:
            print('0x{0:08x} - {1}: {2}'.format(threading.current_thread().ident, datetime.now(), line))


    with OutputListener() as output:
        t = threading.Thread(target=stuff, args=(output,))
        t.daemon = True
        threads.append(t)

        t = threading.Thread(target=tailer, args=(output,))
        t.daemon = True
        threads.append(t)

        for t in threads:
            t.start()

        time.sleep(10)
        for t in threads:
            t.join()

if __name__ == '__main__':
    process_manager_test()
    # output_listener_test()