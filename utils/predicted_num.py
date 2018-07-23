# coding=utf-8
"""
冒险岛甘地活动，预测数字脚本
输入：数字 结果
输出：可能会出现的结果
结果的表达方式：结果为三位数,分别代表 ○，△，╳
"""
from itertools import permutations

all_num = list(permutations(range(1, 10), 3))
_last = None


def set_last(last):
    if __name__ == '__main__':
        global _last
        if _last:
            _last = set(_last) & set(last)
        else:
            _last = set(last)
        if not last:
            return
        else:
            print(sorted(list(_last)), len(_last))
    else:
        pass


def right_num(num_t, num_rs):
    return num_t.count(num_rs[0]) + num_t.count(num_rs[1]) + num_t.count(num_rs[2])


def right_pos(num_t, num_rs):
    count0 = 1 if num_t[0] == num_rs[0] else 0
    count1 = 1 if num_t[1] == num_rs[1] else 0
    count2 = 1 if num_t[2] == num_rs[2] else 0
    return count0 + count1 + count2


def predicted_rs_with_100(num_t):
    rs = list()
    for i in all_num:
        if right_num(i, num_t) == 1 and right_pos(i, num_t) == 1:
            rs.append(i)
    set_last(rs)
    return rs


def predicted_rs_with_001(num_t):
    rs = list()
    for i in all_num:
        if right_num(i, num_t) == 0 and right_pos(i, num_t) == 0:
            rs.append(i)
    set_last(rs)
    return rs


def predicted_rs_with_030(num_t):
    rs = list()
    for i in all_num:
        if right_num(i, num_t) == 3 and right_pos(i, num_t) == 0:
            rs.append(i)
    set_last(rs)
    return rs


def predicted_rs_with_110(num_t):
    rs = list()
    for i in all_num:
        if right_num(i, num_t) == 2 and right_pos(i, num_t) == 1:
            rs.append(i)
    set_last(rs)
    return rs


def predicted_rs_with_120(num_t):
    rs = list()
    for i in all_num:
        if right_num(i, num_t) == 3 and right_pos(i, num_t) == 1:
            rs.append(i)
    set_last(rs)
    return rs


def predicted_rs_with_010(num_t):
    rs = list()
    for i in all_num:
        if right_num(i, num_t) == 1 and right_pos(i, num_t) == 0:
            rs.append(i)
    set_last(rs)
    return rs


def predicted_rs_with_020(num_t):
    rs = list()
    for i in all_num:
        if right_num(i, num_t) == 2 and right_pos(i, num_t) == 0:
            rs.append(i)
    set_last(rs)
    return rs


def predicted_rs_with_200(num_t):
    rs = list()
    for i in all_num:
        if right_num(i, num_t) == 2 and right_pos(i, num_t) == 2:
            rs.append(i)
    set_last(rs)
    return rs


def format_input(raw):
    left, right = raw.split()
    return (int(left[0]), int(left[1]), int(left[2])), (int(right[0]), int(right[1]), int(right[2]))


if __name__ == '__main__':
    while True:
        raw_input = input('输入数字和结果：')
        if raw_input == 'r':
            print('reset successful!')
            set_last([])
            continue
        else:
            num, result = format_input(raw_input)
        if result == (0, 0, 1):
            predicted_rs_with_001(num)  # 全错
        if result == (1, 0, 0):
            predicted_rs_with_100(num)
        if result == (1, 1, 0):
            predicted_rs_with_110(num)
        if result == (1, 2, 0):
            predicted_rs_with_120(num)
        if result == (2, 0, 0):
            predicted_rs_with_200(num)
        if result == (0, 1, 0):
            predicted_rs_with_010(num)
        if result == (0, 2, 0):
            predicted_rs_with_020(num)
        if result == (0, 3, 0):
            predicted_rs_with_030(num)
        if result == (3, 0, 0):
            print('successful!')
            set_last([])
