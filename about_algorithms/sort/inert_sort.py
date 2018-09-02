from random import randint

from sort.sort_utils import *


@time_cost
def sort(unsorted_list):
    length = len(unsorted_list)
    for i in range(length):
        t = i
        j = i - 1
        while j >= 0 and less(unsorted_list[t], unsorted_list[j]):
            exchange(unsorted_list, t, j)
            j -= 1
            t -= 1
    return unsorted_list


if __name__ == '__main__':
    l = unsort_list()
    # print('before sort:{}'.format(l))
    sort_list = sort(l)
    # print('after sort:{}'.format(sort_list))
    assert is_sorted(sort_list), 'not sorted list!'
