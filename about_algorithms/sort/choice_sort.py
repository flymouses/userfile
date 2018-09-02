from random import randint

from sort.sort_utils import *


@time_cost
def sort(unsorted_list):
    length = len(unsorted_list)
    for i in range(length):
        for j in range(i + 1, length):
            if less(unsorted_list[j], unsorted_list[i]):
                exchange(unsorted_list, i, j)
    return unsorted_list


if __name__ == '__main__':
    l = unsort_list()
    # print('before sort:{}'.format(l))
    sort_list = sort(l)
    # print('after sort:{}'.format(sort_list))
    assert is_sorted(sort_list), 'not sorted list!'
