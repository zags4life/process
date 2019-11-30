# __main__.py
import subprocess
import threading
import time

from .output_handlers import *
from .output_listener import *
from .process import Process

import gc

start_time = time.time()

CMD = 'ping 127.0.0.1'

def process_manager_test():
    print('Running Process Test ...')

    timeout=10
    delay = 3

    with Process(CMD, host='127.0.0.1') as proc:
        tail = TailOutputHandler()

        proc.on_process_output_event += tail
        proc.on_process_output_event += PrintOutputHandler()

        proc.start()
        proc.wait_for_exit(timeout=timeout)
        proc.stop()

        print()
        for num, line in enumerate(tail.lines):
            print('{0:>3}: {1}'.format(num+1, line))

        print("\nTook {} sec".format((time.time() - start_time)))

def output_listener_test():
    threads = []

    def stuff(output):
        try:
            proc = subprocess.Popen(CMD, shell=True, 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

        for line in tail_handler.get_lines():
            print(f'0x{threading.current_thread().ident:08x} ' \
                f'- {datetime.now()}: {line}')


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
    # process_manager_test()
    output_listener_test()