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
        rev = func(*args, **kwargs)
        print('cost time is {:.10f}s'.format((time.time() - st_time)))
        return rev

    return wrap


def unsort_list(n=10000):
    return [randint(0, n) for _ in range(n)]


def is_sorted(check_list):
    return sorted(check_list) == check_list
