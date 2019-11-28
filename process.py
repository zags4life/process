# procman.py

from .output_listener import OutputListener
from .process_mgr import LocalProcess, RemoteProcess

__all__ = ['Process']

class Process(object):
    def __init__(self, cmd, shell=False, host=None, port=5000):
        super().__init__()

        self.__proc = LocalProcess(cmd, shell) if host is None \
            else RemoteProcess(cmd, shell, host, port)

        self.__output_listener = OutputListener()
        self.on_process_output_event = \
            self.__output_listener.on_output_event

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.stop(timeout=1)

    def start(self):
        assert not self.is_running

        self.__proc.start()
        self.__output_listener.stdout = self.__proc.stdout()
        self.__output_listener.stderr = self.__proc.stderr()
        self.__output_listener.start_listener()

    def stop(self, timeout=5):
        '''Stops the underlying process'''

        # Defer all logic to the underlying process class
        self.__proc.stop(timeout=timeout)
        self.__output_listener.stop_listener(timeout=timeout)

    def wait_for_exit(self, timeout=None):
        return self.__proc.wait_for_exit(timeout=timeout)

    @property
    def is_running(self):
        return self.__proc.is_running()