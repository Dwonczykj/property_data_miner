from typing import Any, Generic, TypeVar, Callable
import traceback

TRes = TypeVar("TRes")

def predicatePipe(objResult:TRes, predicate:Callable[[TRes],bool], fnToPassTo:Callable[[TRes,Any],Any], *otherFnArgs, returnIfnull=None):
    if predicate(objResult):
        return fnToPassTo(objResult, *otherFnArgs)
    else:
        return returnIfnull
    
def nullPipe(objResult:TRes, fnToPassTo:Callable[[TRes,Any],Any], *otherFnArgs, returnIfnull=None):
    return predicatePipe(objResult, lambda o: o is not None, fnToPassTo, returnIfnull=returnIfnull, *otherFnArgs)

def exception_to_string(excp:Exception):
   stack = traceback.extract_stack()[:-3] + traceback.extract_tb(excp.__traceback__)  # add limit=?? 
   pretty = traceback.format_list(stack)
   return ''.join(pretty) + '\n  {} {}'.format(excp.__class__,excp)
    