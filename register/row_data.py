#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/3/15 11:02
__author__ = 'jin'

from bitarray import bitarray


class RowData(object):

    def __init__(self, b0, b1, b2, b3, b4, b5, b6, b7):
        self.bit = bitarray([b0, b1, b2, b3, b4, b5, b6, b7])

    def hex_value(self):
        num = int(self.bit.to01(), base=2)
        return '%#.2x' % num

    def dec_value(self):
        num = int(self.bit.to01(), base=2)
        return str(num)

    def dec_value_latter_six(self):
        num = int(self.bit.to01()[-6:], base=2)
        return str(num)

    def bool_to_01(self):
        return self.bit.to01()

    def value_to_bit(self, value):
        a = bin(value).replace('0b', '')
        b = '0' * (8 - len(a))
        num = b + a
        for i in range(8):
            self.bit[i] = bool(int(num[i]))


if __name__ == '__main__':
    row01 = RowData(True, True, True, True, True, False, True, False)
    row02 = RowData(True, True, True, True, True, True, True, True)
    row03 = RowData(True, True, True, True, True, True, True, True)

    a = row01.dec_value()
    print(a, type(a))