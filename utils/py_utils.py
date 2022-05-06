from typing import Any, Generic, TypeVar, Callable
import traceback

TRes = TypeVar("TRes")


def predicatePipe(objResult: TRes, 
                  predicate: Callable[[TRes], bool], 
                  fnToPassTo: Callable[[TRes, Any], Any] | Callable[[TRes], Any],
                  *otherFnArgs, 
                  returnIfnull=None):
    if predicate(objResult):
        return fnToPassTo(objResult, *otherFnArgs)
    else:
        return returnIfnull
    
def nullPipe(objResult:TRes,
             fnToPassTo:Callable[[TRes,Any],Any]|Callable[[TRes],Any], 
             *otherFnArgs, 
             returnIfnull=None):
    return predicatePipe(objResult, lambda o: o is not None, fnToPassTo, returnIfnull=returnIfnull, *otherFnArgs)

def int_to_pos_int(arg:int, zero_allowed:bool):
    return max(arg,(0 if zero_allowed else 1))

def force_lwr_bnd_int(arg:int, lwr_bnd:int):
    return max(arg,lwr_bnd)

def force_upr_bnd_int(arg:int, upr_bnd:int):
    return min(arg,upr_bnd)

def exception_to_string(excp:Exception):
   stack = traceback.extract_stack()[:-3] + traceback.extract_tb(excp.__traceback__)  # add limit=?? 
   pretty = traceback.format_list(stack)
   return ''.join(pretty) + '\n  {} {}'.format(excp.__class__,excp)
    