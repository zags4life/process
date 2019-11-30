Process Python Module
=======================
The `process` module is a Python module that enables callers to create and control local and remote processes.  In addition to process control it also allows the caller to handle process output, i.e. `stdout` and `stderr`, using `OutputHandlers`.

### Requirements
- Python 3.7

Topics
------


Output Handling
---------------
An `OutputHandler` is an `ABC` implementation that 'handles' a processes `stdout` and `stderr` output.  An `OutputHandler` can be attached to a `Process` using the `Process` classes `output_handlers` event list.

## OutputHander
The `OutputHander` `ABC` requires four API's, `on_bos`, `on_eos`, `on_stdout`, and `on_stderr`.  Each handler can then handle each event as necessary.

### Interface
```
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
```

## Registering OutputHandlers
To register an `OutputHandler` to a process, using the `+=` operator on the `Process` class' `output_handlers` event list.

```
with Process(cmd='ping 127.0.0.1', shell=True) as proc:
    proc.output_handlers += ConsoleOutputHandler()
    proc.start()
    proc.wait_for_exit()
```

## Unregistering OutputHandler
To unregister an `OutputHander`, use the `-=` operator on the `Process` class' `output_handlers`.  Note: unregistering an `OutputHander` is thread safe and can be done from within a callback, if necessary.

```
handler = ConsoleOutputHandler()

with Process(cmd='ping 127.0.0.1', shell=True) as proc:
    proc.output_handlers += handler
    proc.start()
    proc.wait_for_exit()
    proc.output_handlers -= handler
```

## Built in OutputHandlers
The `Process` module exposes four `OutputHander`s.  

### ConsoleOutputHandler
The `ConsoleOutputHandler` will print all output to the console using `print`.

```
with Process(cmd='ping 127.0.0.1', shell=True) as proc:
    proc.output_handlers += ConsoleOutputHandler()
    proc.start()
    proc.wait_for_exit()
```

### FileOutputHandler
The `FileOutputHandler` will write all output to a file

```
with Process(cmd='ping 127.0.0.1', shell=True) as proc:
    proc.output_handlers += FileOutputHandler('output.txt')
    proc.start()
    proc.wait_for_exit()
```

### TailOutputHandler
The `TailOutputHandler` stores all process output to a backing list.  This is helpful for the cases where interrogating the output.

```
tail_handler = TailOutputHandler()
with Process(cmd='ping 127.0.0.1', shell=True) as proc:
    proc.output_handlers += tail_handler
    proc.start()
    proc.wait_for_exit()
    
for line in tail_handler.get_lines():
    print(line)
```

Process Control
---------------


Remote Process Control
----------------------


