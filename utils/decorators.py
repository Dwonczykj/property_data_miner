from functools import wraps
from threading import local
from typing import Callable

_MAX_RECURSION_FUNC = 100

def recursion_detector(max_recursion_limit:int=_MAX_RECURSION_FUNC):
    '''Protect a function from recursion
        - Ideally the decorated function takes hashable args so that they can be added to the signature of the function to blow up immediately
    '''
    
    def decorator(func:Callable):
        
        func._thread_locals = local()

        @wraps(func)
        def wrapper(*args, **kwargs):
            params = tuple(args) + tuple(kwargs.items())

            if not hasattr(func._thread_locals, 'seen'):
                func._thread_locals.seen = set()
            
            if not hasattr(func._thread_locals, 'seen_times'):
                func._thread_locals.seen_times = 0
                
            hashable_params = False
            if all((hasattr(p,'hash') for p in params)):
                hashable_params = True
                if params in func._thread_locals.seen:
                    raise RuntimeError('Already called this function with the same arguments')

                func._thread_locals.seen.add(params)
            
            func._thread_locals.seen_times += 1
            if func._thread_locals.seen_times > max_recursion_limit:
                raise RuntimeError(
                    f'Already called this function {max_recursion_limit} times, check this is correct, if so increase the recursion limit')
            
            try:
                res = func(*args, **kwargs)
            finally:
                if hashable_params:
                    func._thread_locals.seen.remove(params)
                func._thread_locals.seen_times -= 1
                

            return res

        return wrapper
    
    return decorator
