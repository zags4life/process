# output_listener.py
from enum import IntEnum
import threading
import queue

from eventing_subsystem import event, Event
from utils import Listener

from .output_handlers import OutputHandler

__all__ = ['OutputListener']

class ReadlineMutex(object):
    def __init__(self, *fds):
        self.__q = queue.Queue()
        self.__threads = []

        # Create a thread for each file descriptor
        for fd in fds:
            t = threading.Thread(target=self.__reading_thread, args=(fd,))
            t.daemon = True
            t.start()
            self.__threads.append(t)

        self._count = len(self.__threads)
        if self._count == 0:
            raise ValueError("Invalid number of file descriptors")

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                fd, line = self.__q.get(True, 0.5)
            except queue.Empty:
                continue

            if line is None:
                self._count -= 1

                if self._count == 0:
                    for thread in self.__threads:
                        thread.join()
                    raise StopIteration()
                continue
            return fd, line

    def __reading_thread(self, fd):
        iterator = fd

        for line in iterator:
            if not line:
                break

            if isinstance(line, bytes):
                line = line.decode('utf-8')

            self.__q.put((fd, line.strip()))
        self.__q.put((fd, None))

class OutputEventType(IntEnum):
    STDOUT = 0
    STDERR = 1
    BOS = 2
    EOS = 3

class OutputUpdateEvent(object):
    '''Represents an output event.

    This is a wrapper class over four events, allowing a caller to
    register one OutputHandler, rather than all four callback APIs
    '''

    __on_bos_event    = Event()
    __on_eos_event    = Event()
    __on_stdout_event = Event(str)
    __on_stderr_event = Event(str)

    def __iadd__(self, callback):
        '''Registers an OutputHandler'''
        assert isinstance(callback, OutputHandler), \
            'handler must implement OutputHandler abc'

        # OutputHandler ABC defines four methods: on_bos, on_eos, on_stdout,
        # and on_stderr.  Register each method with the corrisponding events
        self.__on_bos_event += callback.on_bos
        self.__on_eos_event += callback.on_eos
        self.__on_stdout_event += callback.on_stdout
        self.__on_stderr_event += callback.on_stderr

        # Return self to enable cascading
        return self

    def __isub__(self, callback):
        '''Unregisters an OutputHandler'''
        assert isinstance(callback, OutputHandler), \
            'handler must implement OutputHandler abc'

        # OutputHandler ABC defines four methods: on_bos, on_eos, on_stdout,
        # and on_stderr.  Unregister each method with the corrisponding events.
        self.__on_bos_event -= callback.on_bos
        self.__on_eos_event -= callback.on_eos
        self.__on_stdout_event -= callback.on_stdout
        self.__on_stderr_event -= callback.on_stderr

        # Return self to enable cascading
        return self

    def __call__(self, event_type, line=None):
        '''Invokes the event given the event type'''

        ops = {
            OutputEventType.STDOUT: self.__on_stdout_event,
            OutputEventType.STDERR: self.__on_stderr_event,
            OutputEventType.BOS: lambda line: self.__on_bos_event(),
            OutputEventType.EOS: lambda line: self.__on_eos_event(),
        }

        assert event_type in ops, "Unknown event type '{}'".format(event_type)

        return ops[event_type](line)

        # if evt_type == OutputEventType.STDOUT:
            # return self.__on_stdout_event(line)
        # elif evt_type == OutputEventType.STDERR:
            # return self.__on_stderr_event(line)
        # elif evt_type == OutputEventType.BOS:
            # return self.__on_bos_event()
        # elif evt_type == OutputEventType.EOS:
            # return self.__on_eos_event()

        # raise AssertionError("Unknown event type '{}'".format(evt_type))

    def clear(self):
        self.__on_bos_event.clear()
        self.__on_eos_event.clear()
        self.__on_stderr_event.clear()
        self.__on_stdout_event.clear()

class OutputListener(Listener):
    def __init__(self):
        self.stdout = None
        self.stderr = None
        
        self.__on_output_event = OutputUpdateEvent()
        self.__reader_mutex = None
        self.__reader_thread = None

    @property
    def on_output_event(self):
        return self.__on_output_event

    @on_output_event.setter
    def on_output_event(self, event):
        assert event is self.__on_output_event

    ##########################################################
    # Listener ABC implementation
    ##########################################################

    def start_listener(self):
        if self.__reader_thread:
            return

        assert self.stdout is not None and self.stderr is not None

        # Signal to listners the start of the stream
        self.__on_output_event(OutputEventType.BOS)

        self.__reader_thread = threading.Thread(target=self.___reader_thread_main)
        self.__reader_thread.daemon = True
        self.__reader_thread.start()

    def stop_listener(self):
        if self.__reader_thread:
            self.__reader_thread.join()
            self.__reader_thread = None

    ##########################################################
    # Private methods
    ##########################################################

    def ___reader_thread_main(self):
        fds = (self.stdout, self.stderr)
        self.__reader_mutex = ReadlineMutex(*fds)

        for fd, line in self.__reader_mutex:
            if fd == fds[0]:
                event_type = OutputEventType.STDOUT
            elif fd == fds[1]:
                event_type = OutputEventType.STDERR

            self.__on_output_event(event_type, line)

        # Signal the end of the stream
        self.__on_output_event(OutputEventType.EOS)