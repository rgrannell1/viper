
from abc import abstractmethod
import json
import sys
import datetime
from types import FrameType
from typing import Any

class Viper:
  def __init__(self, trace) -> None:
      self.trace = trace

  def start_trace(self) -> None:
    def trace_wrapper (frame: FrameType, event: str, arg: Any):
      self.stop_trace()

      # pass
      viper_event = Event.new(frame, event, arg)
      self.trace(viper_event)

      self.start_trace()

    sys.settrace(trace_wrapper)

  def stop_trace(self) -> None:
    sys.settrace(None)




class Event:
  @classmethod
  def new(cls, frame: FrameType, event: str, arg: Any):
    if event == 'call':
      return EventCall(frame, event, arg)
    if event == 'line':
      return EventLine(frame, event, arg)
    if event == 'return':
      return EventReturn(frame, event, arg)
    if event == 'exception':
      return EventException(frame, event, arg)


    if event == 'c_call':
      return EventCCall(frame, event, arg)
    if event == 'c_return':
      return EventCReturn(frame, event, arg)
    if event == 'c_exception':
      return EventCException(frame, event, arg)


  @abstractmethod
  def dict(self):
    raise NotImplementedError('dict() not implemented')


  def __repr__(self) -> str:
      return json.dumps(self.dict())


class EventCall(Event):
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

  def dict(self) -> dict[str, Any]:
    return {
      'frame': self.frame,
      'event': self.event,
      'arg': self.arg
    }

class EventLine(Event):
  def __init__(self, frame, event, arg):
    self.frame = frame
    self.event = event
    self.arg = arg

class EventReturn(Event):
  def __init__(self, frame, event, arg):
    self.frame = frame
    self.event = event
    self.arg = arg

class EventException(Event):
  def __init__(self, frame, event, arg):
    self.frame = frame
    self.event = event
    self.arg = arg

class EventCCall(Event):
  def __init__(self, frame, event, arg):
    self.frame = frame
    self.event = event
    self.arg = arg

class EventCReturn(Event):
  def __init__(self, frame, event, arg):
    self.frame = frame
    self.event = event
    self.arg = arg

class EventCException(Event):
  def __init__(self, frame, event, arg):
    self.frame = frame
    self.event = event
    self.arg = arg




def a(num):
  def c(x):
    print(x)
    return x

  for idx in range(10):
    c(idx)

  return 2

def calleable(event: Event):
  print(event)

def main():
  vip = Viper(calleable)

  vip.start_trace()
  a(1)
  vip.stop_trace()

main()
