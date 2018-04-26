# coding=utf-8
import pytest

import predicted_num


def test_with_020():
    rs = predicted_num.predicted_rs_with_020((1, 2, 3))
    for i in rs:
        assert (i.count(1) + i.count(2) + i.count(3)) == 2
        assert i[0] != 1
        assert i[1] != 2
        assert i[2] != 3
