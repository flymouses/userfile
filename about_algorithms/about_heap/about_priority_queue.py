class MinIndexPQ(object):
    """
    索引优先队列, 归并多个有序的输入流
    """

    def __init__(self):
        pass

    def insert(self, item):
        pass

    def pop(self):
        pass


def sort_multi_items(*list_iters):
    """
    合并多个有序得流
    list_iters:[ iter1, iter2 ]
    时间复杂度 O(MN) M总元素个数，N归并流个数
    """
    rs = list()
    SPEC_OBJ = object()
    current_value = [SPEC_OBJ] * len(list_iters)
    _list_iters = [iter(_iterable) for _iterable in list_iters]

    while True:
        for index, item in enumerate(_list_iters):
            if current_value[index] is SPEC_OBJ:
                try:
                    value = next(item)
                except StopIteration:
                    pass
                else:
                    current_value[index] = value
        m = None
        mi = None
        for index, value in enumerate(current_value):
            if value is not SPEC_OBJ:
                if m is None:
                    m = value
                    mi = index
                else:
                    if value < m:
                        m = value
                        mi = index
        if m is None:
            break
        else:
            current_value[mi] = SPEC_OBJ
            rs.append(m)

    print(rs)

    return rs


if __name__ == '__main__':
    # pq = MinIndexPQ()
    # pq.insert([3, 4, 5])
    # pq.insert([7, 8, 9])
    # pq.insert([1, 2, 3])
    #
    # for i in range(1, 10):
    #     assert pq.pop() == i

    assert sort_multi_items([7, 8, 9], [1, 4, 5], [2, 6, 11, 12, 13]) == [1, 2, 4, 5, 6, 7, 8, 9, 11, 12, 13]
