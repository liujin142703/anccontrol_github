#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
import numpy as np


def get_R_value(value1=0):
    """
    notch filter 幅值调整电阻取值
    采用direction形式将0-61数字转换为0-100k电阻阻值:
    滑块取值范围0-61，>61值默认输出100k
    输入为str格式：10k
    """
    d = {0: '0', 1: '10', 2: '12', 3: '15', 4: '18', 5: '22', 6: '27', 7: '33', 8: '39', 9: '47', 10: '56',
         11: '68', 12: '82', 13: '100', 14: '120', 15: '150', 16: '180', 17: '220', 18: '270', 19: '330', 20: '390', 21: '470',
         22: '560', 23: '680', 24: '820', 25: '1k', 26: '1.2k', 27: '1.5k', 28: '1.8k', 29: '2.2k', 30: '2.7k', 31: '3.3k',
         32: '3.9k', 33: '4.7k', 34: '5.6k', 35: '6.8k', 36: '8.2k', 37: '10k', 38: '12k', 39: '15k', 40: '18k', 41: '22k',
         42: '27k', 43: '33k', 44: '39k', 45: '47k', 46: '56k', 47: '68k', 48: '82k', 49: '100k', 50: '120k',
         51: '150k', 52: '180k', 53: '220k', 54: '270k', 55: '330k', 56: '390k', 57: '470k', 58: '560k', 59: '680k', 60: '820k',
         61: '1000k'}
    return d[value1]


def R_value2map(value):
    R_value = np.array([200., 220., 240., 270., 300., 330., 360.,
                        390., 430., 470., 510., 560., 620., 680.,
                        750., 820., 910., 1000., 1100., 1200., 1300.,
                        1500., 1600., 1800.,
                        2000., 2200., 2400., 2700., 3000., 3300., 3600.,
                        3900., 4300., 4700., 5100., 5600., 6200., 6800.,
                        7500., 8200., 9100., 10000., 11000., 12000., 13000.,
                        15000., 16000., 18000., 20000., 22000., 24000., 27000.,
                        30000., 33000., 36000., 39000., 43000., 47000., 51000.,
                        56000., 62000., 68000., 75000., 82000., 91000., 100000.,
                        110000., 120000., 130000., 150000., 160000., 180000., 200000.,
                        220000., 240000., 270000.,
                        300000., 330000., 360000., 390000., 430000., 470000., 510000.,
                        560000., 620000., 680000., 750000., 820000., 910000., 1000000.,
                        1100000., 1200000., 1300000., 1500000., 1600000., 1800000., 2000000.,
                        2200000., 2400000., 2700000.,
                        3000000., 3300000., 3600000., 3900000., 4300000., 4700000., 5100000.,
                        5600000., 6200000., 6800000., 7500000., 8200000., 9100000., 10000000.,
                        11000000., 12000000., 13000000., 15000000., 16000000., 18000000., 20000000.
                        ])
    D_value = abs(R_value - value)
    pos = np.where(D_value == D_value.min())
    # E12系列电容容值标准
    Rb_valueMap = ['200', '220', '240', '270', '300', '330', '360',
                   '390', '430', '470', '510', '560', '620', '680',
                   '750', '820', '910', '1k', '1.1k', '1.2k', '1.3k',
                   '1.5k', '1.6k', '1.8k',
                   '2k', '2.2k', '2.4k', '2.7k', '3k', '3.3k', '3.6k',
                   '3.9k', '4.3k', '4.7k', '5.1k', '5.6k', '6.2k', '6.8k',
                   '7.5k', '8.2k', '9.1k', '10k', '11k', '12k', '13k',
                   '15k', '16k', '18k', '20k', '22k', '24k', '27k',
                   '30k', '33k', '36k', '39k', '43k', '47k', '51k',
                   '56k', '62k', '68k', '75k', '82k', '91k', '100k',
                   '110k', '120k', '130k', '150k', '160k', '180k', '200k',
                   '220k', '240k', '270k',
                   '300k', '330k', '360k', '390k', '430k', '470k', '510k',
                   '560k', '620k', '680k', '750k', '820k', '910k', '1000k',
                   '1100k', '1200k', '1300k', '1500k', '1600k', '1800k', '2000k',
                   '2200k', '2400k', '2700k',
                   '3000k', '3300k', '3600k', '3900k', '4300k', '4700k', '5100k',
                   '5600k', '6200k', '6800k', '7500k', '8200k', '9100k', '10000k',
                   '11000k', '12000k', '13000k', '15000k', '16000k', '18000k', '20000k'
                   ]
    return Rb_valueMap[pos[0][0]]


def R_value2map_2(value):
    R_value = np.array([0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6,
                        3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8,
                        7.5, 8.2, 9.1, 10., 11., 12., 13.,
                        15., 16., 18.,
                        20., 22., 24., 27., 30., 33., 36.,
                        39., 43., 47., 51., 56., 62., 68.,
                        75., 82., 91., 100., 110., 120., 130.,
                        150., 160., 180.,
                        200., 220., 240., 270., 300., 330., 360.,
                        390., 430., 470., 510., 560., 620., 680.,
                        750., 820., 910., 1000., 1100., 1200., 1300.,
                        1500., 1600., 1800.,
                        2000., 2200., 2400., 2700., 3000., 3300., 3600.,
                        3900., 4300., 4700., 5100., 5600., 6200., 6800.,
                        7500., 8200., 9100., 10000., 11000., 12000., 13000.,
                        15000., 16000., 18000., 20000., 22000., 24000., 27000.,
                        30000., 33000., 36000., 39000., 43000., 47000., 51000.,
                        56000., 62000., 68000., 75000., 82000., 91000., 100000.,
                        110000., 120000., 130000., 150000., 160000., 180000., 200000.,
                        220000., 240000., 270000.,
                        300000., 330000., 360000., 390000., 430000., 470000., 510000.,
                        560000., 620000., 680000., 750000., 820000., 910000., 1000000.,
                        1100000., 1200000., 1300000., 1500000., 1600000., 1800000., 2000000.,
                        2200000., 2400000., 2700000.,
                        3000000., 3300000., 3600000., 3900000., 4300000., 4700000., 5100000.,
                        5600000., 6200000., 6800000., 7500000., 8200000., 9100000., 10000000.,
                        11000000., 12000000., 13000000., 15000000., 16000000., 18000000., 20000000.])
    D_value = abs(R_value - value)
    pos = np.where(D_value == D_value.min())
    # E12系列电容容值标准
    Rb_valueMap = ['0', '2.2', '2.4', '2.7', '3.0', '3.3', '3.6',
                   '3.9', '4.3', '4.7', '5.1', '5.6', '6.2', '6.8',
                   '7.5', '8.2', '9.1', '10.0', '11.0', '12.0', '13.0',
                   '15.0', '16.0', '18.0',
                   '20.0', '22.0', '24.0', '27.0', '30.0', '33.0', '36.0',
                   '39.0', '43.0', '47.0', '51.0', '56.0', '62.0', '68.0',
                   '75.0', '82.0', '91.0', '100.0', '110.0', '120.0', '130.0',
                   '150.0', '160.0', '180.0',
                   '200', '220', '240', '270', '300', '330', '360',
                   '390', '430', '470', '510', '560', '620', '680',
                   '750', '820', '910', '1k', '1.1k', '1.2k', '1.3k',
                   '1.5k', '1.6k', '1.8k',
                   '2k', '2.2k', '2.4k', '2.7k', '3k', '3.3k', '3.6k',
                   '3.9k', '4.3k', '4.7k', '5.1k', '5.6k', '6.2k', '6.8k',
                   '7.5k', '8.2k', '9.1k', '10k', '11k', '12k', '13k',
                   '15k', '16k', '18k', '20k', '22k', '24k', '27k',
                   '30k', '33k', '36k', '39k', '43k', '47k', '51k',
                   '56k', '62k', '68k', '75k', '82k', '91k', '100k',
                   '110k', '120k', '130k', '150k', '160k', '180k', '200k',
                   '220k', '240k', '270k',
                   '300k', '330k', '360k', '390k', '430k', '470k', '510k',
                   '560k', '620k', '680k', '750k', '820k', '910k', '1000k',
                   '1100k', '1200k', '1300k', '1500k', '1600k', '1800k', '2000k',
                   '2200k', '2400k', '2700k',
                   '3000k', '3300k', '3600k', '3900k', '4300k', '4700k', '5100k',
                   '5600k', '6200k', '6800k', '7500k', '8200k', '9100k', '10000k',
                   '11000k', '12000k', '13000k', '15000k', '16000k', '18000k', '20000k']
    return Rb_valueMap[pos[0][0]]


if __name__ == '__main__':
    d = R_value2map_2(30000)
    print(d)
