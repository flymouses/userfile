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
    global _last
    if _last:
        _last = set(_last) & set(last)
    else:
        _last = set(last)
    if not last:
        return
    else:
        print(sorted(list(_last)))


def predicted_rs_with_100(num_t):
    rs1 = list()
    for i in all_num:
        if i[0] == num_t[0]:
            if {i[1], i[2]} & {num_t[1], num_t[2]}:
                pass
            else:
                rs1.append(i)
        else:
            pass
    rs2 = list()
    for i in all_num:
        if i[1] == num_t[1]:
            if {i[0], i[2]} & {num_t[0], num_t[2]}:
                pass
            else:
                rs2.append(i)
        else:
            pass
    rs3 = list()
    for i in all_num:
        if i[2] == num_t[2]:
            if {i[0], i[1]} & {num_t[0], num_t[1]}:
                pass
            else:
                rs3.append(i)
        else:
            pass
    rs = set(rs1) | set(rs2) | set(rs3)
    set_last(rs)


def predicted_rs_with_001(num_t):
    rs = [i for i in all_num if not (set(i) & set(num_t))]
    set_last(rs)


def predicted_rs_with_030(num_t):
    rp = [*num_t, *num_t]
    rs = list()
    for index in range(1, 3):
        rs.append(tuple(rp[index:index + 3]))
    set_last(rs)


def predicted_rs_with_110(num_t):
    rs1 = list()
    for i in all_num:  # 第一个数对
        if i[0] == num_t[0]:
            if num_t[1] == i[2] and i[1] != num_t[2]:
                rs1.append(i)
            elif num_t[2] == i[1] and i[2] != num_t[1]:
                rs1.append(i)
        else:
            pass

    rs2 = list()
    for i in all_num:  # 第二个数对
        if i[1] == num_t[1]:
            if num_t[0] == i[2] and i[0] != num_t[2]:
                rs2.append(i)
            elif num_t[2] == i[0] and i[2] != num_t[0]:
                rs2.append(i)
        else:
            pass

    rs3 = list()
    for i in all_num:  # 第三个数对
        if i[2] == num_t[2]:
            if num_t[1] == i[0] and i[1] != num_t[0]:
                rs2.append(i)
            elif num_t[0] == i[1] and i[0] != num_t[1]:
                rs2.append(i)
        else:
            pass

    rs = set(rs1) | set(rs2) | set(rs3)
    set_last(rs)


def predicted_rs_with_120(num_t):
    rs = [(num_t[0], num_t[2], num_t[1]), (num_t[2], num_t[1], num_t[0]), (num_t[1], num_t[0], num_t[2])]
    set_last(rs)


def predicted_rs_with_010(num_t):
    rs = list()
    for i in all_num:
        if num_t[0] == i[1]:
            if {num_t[1], num_t[2]} & {i[0], i[2]}:
                pass
            else:
                rs.append(i)
        elif num_t[0] == i[2]:
            if {num_t[1], num_t[2]} & {i[0], i[1]}:
                pass
            else:
                rs.append(i)
        elif num_t[1] == i[0]:
            if {num_t[0], num_t[2]} & {i[1], i[2]}:
                pass
            else:
                rs.append(i)
        elif num_t[1] == i[2]:
            if {num_t[0], num_t[2]} & {i[0], i[1]}:
                pass
            else:
                rs.append(i)
        elif num_t[2] == i[0]:
            if {num_t[0], num_t[1]} & {i[2], i[1]}:
                pass
            else:
                rs.append(i)
        elif num_t[2] == i[1]:
            if {num_t[0], num_t[1]} & {i[2], i[0]}:
                pass
            else:
                rs.append(i)
        else:
            pass
    set_last(rs)


def predicted_rs_with_020(num_t):
    rs = list()
    for i in all_num:
        if (set(i) & {num_t[0], num_t[1]}) and (num_t[2] not in i):
            if i[0] != num_t[0] and i[1] != num_t[1]:
                rs.append(i)
        elif (set(i) & {num_t[0], num_t[2]}) and (num_t[1] not in i):
            if i[0] != num_t[0] and i[2] != num_t[2]:
                rs.append(i)
        elif (set(i) & {num_t[1], num_t[2]}) and (num_t[0] not in i):
            if i[2] != num_t[2] and i[1] != num_t[1]:
                rs.append(i)
        else:
            pass
    set_last(rs)


def predicted_rs_with_200(num_t):
    rs = list()
    for i in all_num:
        if i[0] == num_t[0] and i[1] == num_t[1] and i[2] != num_t[2]:
            rs.append(i)
        elif i[0] == num_t[0] and i[2] == num_t[2] and i[1] != num_t[1]:
            rs.append(i)
        elif i[1] == num_t[1] and i[2] == num_t[2] and i[0] != num_t[0]:
            rs.append(i)
        else:
            pass
    set_last(rs)


def format_input(raw):
    left, right = raw.split()
    return (int(left[0]), int(left[1]), int(left[2])), (int(right[0]), int(right[1]), int(right[2]))


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
