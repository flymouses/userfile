import math
import time
import random
from itertools import combinations


class MaxPQHeap(object):

    def __init__(self, max_length=-1):
        self.pq = ['_no_content']
        self.size = 0

    # 插入新元素
    def insert(self, item):
        self.pq.append(item)
        self.size += 1
        self.swim(self.size)
        return item

    # 删除最大元素，并返回
    def del_max(self):
        self.exchange(1, self.size)
        rev = self.pq.pop()
        self.size -= 1
        self.sink(1)
        return rev

    # 上浮一个元素，到合适的位置
    def swim(self, pos):
        while pos > 1 and self.pq[pos] > self.pq[pos // 2]:
            self.exchange(pos, pos // 2)
            pos = pos // 2

    # 下沉一个元素到合适的位置
    def sink(self, pos):
        while 2 * pos <= self.size:
            j = 2 * pos
            if (j + 1) <= self.size and self.pq[j] <= self.pq[j + 1]:
                j += 1
            if self.pq[pos] < self.pq[j]:
                self.exchange(pos, j)
                pos = j
            else:
                break

    def exchange(self, a, b):
        self.pq[a], self.pq[b] = self.pq[b], self.pq[a]

    def __str__(self):
        content = ''
        for h in range(1, self.high() + 1):
            st = pow(2, (h - 1))
            line = ' '.join(map(str, self.pq[st:st + st]))
            content += line
            content += '\n'
        return content

    def high(self):
        return math.floor(math.log(self.size, 2)) + 1

    def max_size(self):
        return pow(2, self.high()) - 1


class MaxPQList(object):

    def __init__(self):
        self.pq = list()

    def insert(self, item):
        self.pq.append(item)
        return item

    def del_max(self):
        self.pq.sort(reverse=True)
        return self.pq.pop()


def insert_and_del(pq):
    st = time.time()
    for i in range(100000):
        pq.insert(i)
    for _ in range(100000):
        pq.del_max()
    print('cost {}'.format(time.time() - st))


if __name__ == '__main__':
    insert_and_del(MaxPQHeap())  # cost 4s
    insert_and_del(MaxPQList())  # cost 117s
