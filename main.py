
from abc import abstractmethod
from pdb import set_trace
import sys
import json
import inspect
import datetime
from types import FrameType
from typing import Any, Callable, Optional, Union
from cheap_repr import cheap_repr

# -- -- -- Stack Frame Information -- -- -- #

class ViperFrame:
  """A stack-frame. Retrieve requested information.
  """
  fn_name: Optional[str]
  fn_line: Optional[int]
  fn_file: Optional[str]
  fn_filename: Optional[str]

  frame: FrameType

  def __init__(self, frame: FrameType):
    self.frame = frame
    self.fn_name = frame.f_code.co_name
    self.fn_line = frame.f_lineno
    self.fn_filename = frame.f_code.co_filename

    if frame is None:
      return

  def arguments(self) -> dict[str, Any]:
    argInfo = inspect.getargvalues(self.frame)

    pairs = { }
    for arg in argInfo.args:
      pairs[arg] = cheap_repr(argInfo.locals[arg])

    return pairs

  def parents(self, transformer) -> list[Any]:
    """List parent frames"""
    parents = []

    # build up a list of parent stacks
    tgt = self.frame.f_back
    while True:
      if tgt is None:
        break

      tgt = tgt.f_back
      if tgt is None:
        break

      parents.append(ViperFrame(tgt).transform(transformer))

    return parents

  def transform(self, transformer) -> dict[str, Any]:
    return transformer().transform(self)

# -- -- -- Event Parent Class -- -- -- #

class ViperEvent:
  """Includes information about a stack frame and event captured by settrace."""
  frame: ViperFrame
  event: str
  arg: Any

  @classmethod
  def new(cls, frame: FrameType, event: str, arg: Any):
    """Given information about a trace event (e.g a value was returned, a call was about to be made, etc), capture the information in a
    useful and JSON-storable format with a subclass for each event-type"""
    if event == 'call':
      return ViperEventCall(frame, event, arg)
    elif event == 'line':
      return ViperEventLine(frame, event, arg)
    elif event == 'return':
      return ViperEventReturn(frame, event, arg)
    elif event == 'exception':
      return ViperEventException(frame, event, arg)
    elif event == 'c_call':
      return ViperEventCCall(frame, event, arg)
    elif event == 'c_return':
      return ViperEventCReturn(frame, event, arg)
    elif event == 'c_exception':
      return ViperEventCException(frame, event, arg)
    else:
      raise Exception('event ' + event + ' not supported')

  @abstractmethod
  def __dict__(self):
    """An abstract method; each subclass should be representable as a dictionary"""
    raise NotImplementedError('dict() not implemented')



# -- -- -- Event Classes -- -- -- #

# TODO improve interface; frame as a class, event as an enum, arg as a safe json repr
class ViperEventCall(ViperEvent):
  def __init__(self, frame, event, arg):
    self.frame = ViperFrame(frame)
    self.event = event
    self.arg = cheap_repr(arg)

  def __dict__(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }

class ViperEventLine(ViperEvent):
  def __init__(self, frame, event, arg):
    self.frame = ViperFrame(frame)
    self.event = event
    self.arg = cheap_repr(arg)

  def __dict__(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }

class ViperEventReturn(ViperEvent):
  def __init__(self, frame, event, arg):
    self.frame = ViperFrame(frame)
    self.event = event
    self.arg = cheap_repr(arg)

  def __dict__(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }


class ViperEventException(ViperEvent):
  def __init__(self, frame, event, arg):
    self.frame = ViperFrame(frame)
    self.event = event
    self.arg = cheap_repr(arg)

  def __dict__(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }


class ViperEventCCall(ViperEvent):
  def __init__(self, frame, event, arg):
    self.frame = ViperFrame(frame)
    self.event = event
    self.arg = cheap_repr(arg)

  def __dict__(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }


class ViperEventCReturn(ViperEvent):
  def __init__(self, frame, event, arg):
    self.frame = ViperFrame(frame)
    self.event = event
    self.arg = cheap_repr(arg)

  def __dict__(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }


class ViperEventCException(ViperEvent):
  def __init__(self, frame, event, arg):
    self.frame = frame
    self.event = event
    self.arg = cheap_repr(arg)

  def __dict__(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }

# -- -- -- Function Types -- -- -- #

ViperEvents = Union[ViperEventCall, ViperEventLine, ViperEventReturn,
                    ViperEventException, ViperEventCCall, ViperEventCReturn, ViperEventCException]

ViperFilterFunc = Callable[[ViperEvents], bool]
ViperWriterFunc = Callable[[ViperEvents], Any]

# -- -- -- Core Viper Class -- -- -- #

class Viper:
  """Trace application calls, return values, and exceptions, and write the results to a callback function."""

  @abstractmethod
  def filter(self, event: ViperEvents) -> bool:
    raise NotImplementedError("you need to implement filter")

  @abstractmethod
  def transform(self, event: ViperEvents) -> dict[str, Any]:
    raise NotImplementedError("you need to implement transform")

  def writer(self, event: dict[str, Any]) -> None:
    """By default, Viper will print a JSON-representation of events to stderr"""
    print(json.dumps(event), file=sys.stderr)

  def start_trace(self) -> None:
    """Start tracing application"""
    def trace_wrapper(frame: FrameType, event: str, arg: Any):
      self.stop_trace()

      # pass to user trace function
      viper_event = ViperEvent.new(frame, event, arg)

      # filter an event
      if self.filter(viper_event):
        # write an event
        self.writer(self.transform(viper_event))

      self.start_trace()

    sys.settrace(trace_wrapper)

  def stop_trace(self) -> None:
    """Stop tracing application"""
    sys.settrace(None)



# -- -- --  Frame Transformers -- -- -- #

class ViperFrameTransformer:
  @abstractmethod
  def transform(self, frame: ViperFrame) -> dict[str, Any]:
    raise NotImplementedError("transform must be implemented")


class ViperParentFrame(ViperFrameTransformer):
  def transform(self, frame: ViperFrame) -> dict[str, Any]:
    return {
      'type': 'parent-frame',
      'fn_name': frame.fn_name,
      'fn_line': frame.fn_line,
      'fn_filename': frame.fn_filename,
      'time': datetime.datetime.now().isoformat(),
      'epoch': datetime.datetime.now().timestamp()
    }

class ViperChildFrame(ViperFrameTransformer):
  def transform(self, frame: ViperFrame) -> dict[str, Any]:

    return {
      'type': 'child-frame',
      'parents': frame.parents(ViperParentFrame),
      'fn_name': frame.fn_name,
      'fn_line': frame.fn_line,
      'args': [
        frame.arguments()
      ],
      'fn_filename': frame.fn_filename,
      'time': datetime.datetime.now().isoformat(),
      'epoch': datetime.datetime.now().timestamp()
    }

# -- -- -- Test Code -- -- -- #


def a(num):
  def c(x):
    return x

  for idx in range(10):
    y = c(idx)

  return 2


class SimpleSummary(Viper):
  def filter(self, event):
    return isinstance(event, ViperEventCall) and event.frame

  def transform(self, event):
    frame = event.frame.transform(ViperChildFrame)
    arg = event.arg
    event = event.event

    return {
      'event': event,
      'frame': frame,
      'arg': arg
    }

def main():
  viper = SimpleSummary()

  viper.start_trace()
  a(1)
  viper.stop_trace()

main()
