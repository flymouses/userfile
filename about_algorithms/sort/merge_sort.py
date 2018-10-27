from sort.sort_utils import *


def hanni(n, x, y, z):
    """
    汉娜塔问题 n个盘，从x移动到y
    :param n: 个数
    :param x: 原始位置
    :param y: 目标位置
    :param z: 中转柱子
    :return:
    """
    if n == 0:
        return
    hanni(n - 1, x, z, y)
    print('{} -> {}'.format(x, y))
    hanni(n - 1, z, y, x)


def merge(items1, items2):
    rs = list()
    p1 = 0
    p2 = 0
    while len(rs) < (len(items1) + len(items2)):
        if p1 >= len(items1):
            rs.append(items2[p2])
            p2 += 1
            continue

        if p2 >= len(items2):
            rs.append(items1[p1])
            p1 += 1
            continue

        if items1[p1] < items2[p2]:
            rs.append(items1[p1])
            p1 += 1
        else:
            rs.append(items2[p2])
            p2 += 1
    return rs

def merge_sort(itmes):
    """
    :param itmes: 待排序元素
    :return:
    """
    if len(itmes) <= 1:
        return itmes
    p = len(itmes) // 2
    return merge(merge_sort(itmes[:p]), merge_sort(itmes[p:]))


@time_cost
def _tcost(itmes):
    return merge_sort(itmes)


if __name__ == '__main__':
    # hanni(3, 'A', 'B', 'C')
    l = unsort_list()
    sort_list1 = _tcost(l)
    assert is_sorted(sort_list1), 'not sorted list!'
