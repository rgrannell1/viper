
from abc import abstractmethod
import json
import sys
import datetime
from types import FrameType
from typing import Any, Callable, Union



class ViperEvent:
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

  def __repr__(self) -> str:
    """Print a JSON representation of an event"""
    return json.dumps(self.__dict__())


# TODO improve interface; frame as a class, event as an enum, arg as a safe json repr
class ViperEventCall(ViperEvent):
  def __init__(self, frame, event, arg):
    self.frame = self.process_frame(frame)
    self.event = event
    self.arg = arg

  def process_frame(self, frame) -> dict[str, Any]:
    co = frame.f_code
    func_name = co.co_name
    caller = frame.f_back # todo unroll trace, with a cache

    now = datetime.datetime.now()
    return {
      'fn': {
        'name': func_name,
        'line': frame.f_lineno,
        'file': co.co_filename
      },
      'meta': {
        'time': now.time().isoformat(),
        'epoc': now.timestamp()
      }
    }

  def __dict__(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }

class ViperEventLine(ViperEvent):
  def __init__(self, frame, event, arg):
    self.frame = frame
    self.event = event
    self.arg = arg

  def __dict__(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }

class ViperEventReturn(ViperEvent):
  def __init__(self, frame, event, arg):
    self.frame = frame
    self.event = event
    self.arg = arg

  def __dict__(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }


class ViperEventException(ViperEvent):
  def __init__(self, frame, event, arg):
    self.frame = frame
    self.event = event
    self.arg = arg

  def __dict__(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }


class ViperEventCCall(ViperEvent):
  def __init__(self, frame, event, arg):
    self.frame = frame
    self.event = event
    self.arg = arg

  def __dict__(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }


class ViperEventCReturn(ViperEvent):
  def __init__(self, frame, event, arg):
    self.frame = frame
    self.event = event
    self.arg = arg

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
    self.arg = arg

  def __dict__(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }


# function parameter types
ViperEvents = Union[ViperEventCall, ViperEventLine, ViperEventReturn,
                    ViperEventException, ViperEventCCall, ViperEventCReturn, ViperEventCException]

ViperFilterFunc = Callable[[ViperEvents], bool]
ViperWriterFunc = Callable[[ViperEvents], Any]


class Viper:
  """Trace application calls, return values, and exceptions, and write the results to a callback function."""

  @abstractmethod
  def filter(self, event: ViperEvents) -> bool:
    raise NotImplementedError("you need to implement filter")

  def writer(self, event) -> None:
    """By default, Viper will print a JSON-representation of events to stderr"""
    print(event, file=sys.stderr)

  def start_trace(self) -> None:
    """Start tracing application"""
    def trace_wrapper(frame: FrameType, event: str, arg: Any):
      self.stop_trace()

      # pass to user trace function
      viper_event = ViperEvent.new(frame, event, arg)
      if self.filter(viper_event):
        self.writer(viper_event)

      self.start_trace()

    sys.settrace(trace_wrapper)

  def stop_trace(self) -> None:
    """Stop tracing application"""
    sys.settrace(None)



def a(num):
  def c(x):
    print(x)
    return x

  for idx in range(10):
    y = c(idx)

  return 2

def filter(event: ViperEvent):
  return isinstance(event, ViperEventCall) and event.frame

class PitViper(Viper):
  def filter(self, event):
    return True

def main():
  viper = PitViper()

  viper.start_trace()
  a(1)
  viper.stop_trace()

main()
