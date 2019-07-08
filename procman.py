# procman.py

import subprocess

from .output_listener import OutputListener

__all__ = ['Process']

class Process(object):
    def __init__(self, cmd):
        super().__init__()
        self._cmd = cmd
        self._output_listener = OutputListener()
        self._proc = None

        self.on_process_output_event = \
            self._output_listener.on_output_event

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.stop(timeout=1)

    def start(self):
        if self._proc:
            return

        proc = subprocess.Popen(self._cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._output_listener.stdout = proc.stdout
        self._output_listener.stderr = proc.stderr
        self._output_listener.start_listener()
        self._proc = proc

    def stop(self, timeout=10):
        if not self._proc:
            return

        self._proc.terminate()
        self._proc.wait(timeout=timeout)
        retval = self._proc.poll()

        if not retval:
            self._proc.kill()
            self._proc.wait(timeout=timeout)
            retval = self._proc.poll()
        self._output_listener.stop_listener()
        self._proc = None
        return retval

    def wait_for_exit(self, timeout=None):
        try:
            self._proc.wait(timeout=timeout)
            return True
        except subprocess.TimeoutExpired:
            return False

    def is_running(self):
        return self._proc and self._proc.poll() is None