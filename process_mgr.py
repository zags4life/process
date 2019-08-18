# process_mgr.py

from multiprocessing.managers import BaseManager, BaseProxy
import subprocess

__all__ = []

AUTHKEY=b'J7STkDPM0t'

class LocalProcess(object):
    def __init__(self, cmd, shell=False):
        self.cmd = cmd
        self.shell = shell
        self.proc = None

        self.__stdout = None
        self.__stderr = None

    def stderr(self):
        '''Returns stderr, as a stream, of the process'''
        return self.__stderr

    def stdout(self):
        '''Returns stdout, as a stream, of the process'''
        return self.__stdout

    def start(self):
        '''Starts the process'''
        print('STARTING')
        assert not self.proc, 'Process already running'

        self.proc = subprocess.Popen(self.cmd, shell=self.shell,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.__stdout = self.proc.stdout
        self.__stderr = self.proc.stderr

    def stop(self, timeout=None):
        '''Stops the process'''

        # If the process is not running, do nothing
        if not self.is_running():
            return

        self.proc.terminate()

        try:
            if self.wait_for_exit(timeout=timeout):
                return self.proc.returncode
            else:
                self.proc.kill()
                self.proc.wait(timeout=timeout)
                return self.proc.returncode
        finally:
            self.proc = None

    def wait_for_exit(self, timeout=None):
        '''Waits for the process to exit

        Parameters:
        timeout: the maximum amount of time to block, in seconds, for the
                 process to exit.  If timeout is None, this method
                 will block infinitely.
        '''
        try:
            self.proc.wait(timeout=timeout)
            return True
        except subprocess.TimeoutExpired:
            return False

    def is_running(self):
        '''Returns True is the underlying process is running,
        otherwise False
        '''
        return self.proc and self.proc.poll() is None

def RemoteProcess(cmd, shell, host, port=5000):
    manager = ProcessManager(host=host, port=port)
    manager.connect()
    return manager.LocalProcess(cmd, shell)

class FileDescriptor(BaseProxy):
    _exposed_ = ['readline']
    def readline(self):
        return self._callmethod('readline')

class ProcessManager(BaseManager):
    def __init__(self, host='127.0.0.1', port=5000):
        super().__init__(address=(host, port), authkey=AUTHKEY)

ProcessManager.register(typeid='LocalProcess', callable=LocalProcess,
    method_to_typeid={'stdout': 'FileDescriptor', 'stderr': 'FileDescriptor'})
ProcessManager.register(typeid='FileDescriptor', proxytype=FileDescriptor)
