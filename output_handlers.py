# output_handlers.py
from abc import ABC, abstractmethod
from datetime import datetime
import sys
import threading
import time
from queue import Queue, Empty
import weakref


__all__ = [
    'ConsoleOutputHandler',
    'FileOutputHandler',
    'OutputHandler',
    'PrintOutputHandler',
    'TailOutputHandler'
]


class OutputHandler(ABC):
    @abstractmethod
    def on_bos(self, sender):
        pass

    @abstractmethod
    def on_eos(self, sender):
        pass

    @abstractmethod
    def on_stdout(self, sender, line):
        pass

    @abstractmethod
    def on_stderr(self, sender, line):
        pass

class PrintOutputHandler(OutputHandler):
    def on_bos(self, sender):
        pass
    on_eos = on_bos

    def on_stdout(self, sender, line):
        print(self._format_line(line, 'INFO'))
        return line

    def on_stderr(self, sender, line):
        print(self._format_line(line, 'ERROR'))
        return line

    @classmethod
    def _format_line(cls, line, prefix = None):
        if isinstance(line, bytes):
            line = line.decode('utf-8')

        timestamp = datetime.now()

        if prefix:
            return '{}: {} - {}'.format(timestamp, prefix, line)
        return '{}: {}'.format(timestamp, line)

class ConsoleOutputHandler(OutputHandler):
    def on_bos(self, sender):
        pass
    on_eos = on_bos

    def on_stdout(self, sender, line):
        print(line)
        return line

    def on_stderr(self, sender, line):
        print(line, file=sys.stderr)
        return line

class FileOutputHandler(OutputHandler):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self._fd = None

    def on_bos(self, sender):
        self._fd = open(self.filename, 'w')

    def on_eos(self, sender):
        self._fd.close()
        self._fd = None

    def on_stdout(self, sender, line):
        assert self._fd
        self._fd.write('{}: {}\n'.format(datetime.now(), line))
        self._fd.flush()
        return line
    on_stderr = on_stdout

class TailIterator(object):
    def __init__(self, lines):
        self._q = Queue()

        for line in lines:
            self._q.put_nowait(line)

    def append_line(self, line):
        self._q.put(line, block=True, timeout=0.5)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return self._q.get(block=True, timeout=0.5)
        except Empty:
            raise StopIteration()

class TailOutputHandler(OutputHandler):
    def __init__(self):
        super().__init__()
        self.__lines = []
        self.__weakrefs = []

    def on_bos(self, sender):
        pass
    on_eos = on_bos

    def on_stdout(self, sender, line):
        refs = []
        for ref in self.__weakrefs:
            iter = ref()
            if iter:
                iter.append_line(line)
                refs.append(ref)

            self.__weakrefs = refs
        self.__lines.append(line)
    on_stderr = on_stdout

    @property
    def lines(self):
        iterator = TailIterator(self.__lines)
        self.__weakrefs.append(weakref.ref(iterator))
        return iterator
