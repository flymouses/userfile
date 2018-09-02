"""
sort utils
"""

from functools import wraps
from random import randint
import time

__all__ = ['exchange', 'less', 'time_cost', 'unsort_list',
           'is_sorted']


def exchange(target_list, index_a, index_b):
    target_list[index_a], target_list[index_b] = target_list[index_b], target_list[index_a]
    return None


def less(a, b):
    return a < b


def time_cost(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        st_time = time.time()
        rev = list()
        for _ in range(10):
            if not rev:
                rev = func(*args, **kwargs)
            else:
                func(*args, **kwargs)
        print('call 10 times, avg cost time is {:.10f}s'.format((time.time() - st_time) / 10))
        return rev

    return wrap


def unsort_list(n=100):
    return [randint(0, n) for _ in range(n)]


def is_sorted(check_list):
    return sorted(check_list) == check_list
