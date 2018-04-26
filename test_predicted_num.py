# coding=utf-8
import pytest

import predicted_num


def right_num(num_t):
    return num_t.count(1) + num_t.count(2) + num_t.count(3)


def right_pos(num_t):
    count0 = 1 if num_t[0] == 1 else 0
    count1 = 1 if num_t[1] == 2 else 0
    count2 = 1 if num_t[2] == 3 else 0
    return count0 + count1 + count2


def test_with_030():
    rs = predicted_num.predicted_rs_with_030((1, 2, 3))
    for i in rs:
        assert right_num(i) == 3
        assert right_pos(i) == 0


def test_with_020():
    rs = predicted_num.predicted_rs_with_020((1, 2, 3))
    for i in rs:
        assert right_num(i) == 2
        assert right_pos(i) == 0


def test_with_010():
    rs = predicted_num.predicted_rs_with_010((1, 2, 3))
    for i in rs:
        assert right_num(i) == 1
        assert right_pos(i) == 0


def test_with_100():
    rs = predicted_num.predicted_rs_with_100((1, 2, 3))
    for i in rs:
        assert right_num(i) == 1
        assert right_pos(i) == 1


def test_with_110():
    rs = predicted_num.predicted_rs_with_110((1, 2, 3))
    for i in rs:
        assert right_num(i) == 2
        assert right_pos(i) == 1


def test_with_120():
    rs = predicted_num.predicted_rs_with_120((1, 2, 3))
    for i in rs:
        assert right_num(i) == 3
        assert right_pos(i) == 1


def test_with_200():
    rs = predicted_num.predicted_rs_with_200((1, 2, 3))
    for i in rs:
        assert right_num(i) == 2
        assert right_pos(i) == 2
