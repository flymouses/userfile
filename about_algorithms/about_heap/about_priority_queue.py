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


def sort_multi_items(list_iters):
    """
    合并多个有序得流
    list_iters:[ iter1, iter2 ]
    """
    rs = list()
    while True:
        current_value = [None] * len(list_iters)
        for index, item in enumerate(list_iters):
            pass


if __name__ == '__main__':
    pq = MinIndexPQ()
    pq.insert([3, 4, 5])
    pq.insert([7, 8, 9])
    pq.insert([1, 2, 3])

    for i in range(1, 10):
        assert pq.pop() == i
