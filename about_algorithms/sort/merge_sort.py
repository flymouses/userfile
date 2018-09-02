from random import randint

from sort.sort_utils import *


@time_cost
def sort(unsorted_list):
    _sort(unsorted_list, 0, len(unsorted_list) - 1)
    return unsorted_list


def _sort(unsort_list, lo, hi):
    if hi <= lo:
        return None
    else:
        mid = lo + (hi - lo) // 2
        _sort(unsort_list, lo, mid)
        _sort(unsort_list, mid + 1, hi)
        merge(unsort_list, lo, mid, hi)


def merge(unsort_list, lo, mid, hi):
    copy_unsort_list = unsort_list.copy()
    i, j = lo, mid + 1
    for index in range(lo, hi + 1):
        if i > mid:
            unsort_list[index] = copy_unsort_list[j]
            j += 1
        elif j > hi:
            unsort_list[index] = copy_unsort_list[i]
            i += 1
        elif less(copy_unsort_list[j], copy_unsort_list[i]):
            unsort_list[index] = copy_unsort_list[j]
            j += 1
        else:
            unsort_list[index] = copy_unsort_list[i]
            i += 1


if __name__ == '__main__':
    l = unsort_list()
    # print('before sort:{}'.format(l))
    sort_list = sort(l)
    # print('after sort:{}'.format(sort_list))
    assert is_sorted(sort_list), 'not sorted list!'
