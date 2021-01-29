#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/4/25 16:08
import os
import xlrd
import numpy as np


class FilterImport(object):
    """理想滤波器曲线导入类"""

    def __init__(self, path):

        self.model_select(path)

    def model_select(self, path):
        p, t = os.path.splitext(path)
        if t == '.txt':
            self.import_filter_txt(path)
        else:
            self.import_filter_excel(path)

    def import_filter_excel(self, path):

        with xlrd.open_workbook(path) as readbook:
            try:
                table0 = readbook.sheet_by_index(0)
                nrows = table0.nrows  # sheet最大行数
                ncols = table0.ncols  # sheet最大列数
                # 数据基本大小识别
                if ncols < 2:
                    raise ValueError('参考数据不符合要求：数据列数<2')
                if nrows < 5:
                    raise ValueError('参考数据不符合要求：数据行数<5')

                # 格式识别
                value00 = table0.cell_value(0, 0)
                value01 = table0.cell_value(0, 1)

                if value00 == 'Generator' and value01 == 'Internal Loop':  # AMS FB数据导入

                    x_frequency = table0.col_values(0, start_rowx=8, end_rowx=nrows)
                    f_gain = table0.col_values(4, start_rowx=8, end_rowx=nrows)
                    f_phase = table0.col_values(5, start_rowx=8, end_rowx=nrows)
                    for m in (x_frequency, f_gain, f_phase):
                        for i in m.copy():
                            if not isinstance(i, (float, int)):
                                m.remove(i)
                    # 调整相位区间
                    f_phase_pi = np.array(f_phase)
                    f_phase_pi = f_phase_pi - 180
                    phase_num = (np.mod(f_phase_pi, 360) - 180)

                elif value00 == 'Generator' and value01 == 'SRC_2_AH +20dB':  # AMS FF数据导入

                    x_frequency = table0.col_values(0, start_rowx=8, end_rowx=nrows)
                    f_gain = table0.col_values(15, start_rowx=8, end_rowx=nrows)
                    f_phase = table0.col_values(16, start_rowx=8, end_rowx=nrows)
                    for m in (x_frequency, f_gain, f_phase):
                        for i in m.copy():
                            if not isinstance(i, (float, int)):
                                m.remove(i)
                    # 调整相位区间
                    f_phase_pi = np.array(f_phase)
                    f_phase_pi = f_phase_pi - 180
                    phase_num = (np.mod(f_phase_pi, 360) - 180)

                else:  # 自动义数据导入
                    x_frequency = table0.col_values(0, start_rowx=4, end_rowx=nrows)
                    f_gain = table0.col_values(1, start_rowx=4, end_rowx=nrows)
                    f_phase = table0.col_values(2, start_rowx=4, end_rowx=nrows)

                    if  len(x_frequency) != len(f_gain) and len(x_frequency) != len(f_phase):
                        raise ValueError('参考数据不符合要求：数据长度不一致')
                    for i in range(len(x_frequency)):
                        if not isinstance(x_frequency[i], (float, int)):
                            x_frequency.pop(i)
                            f_gain.pop(i)
                            f_phase.pop(i)
                    phase_num = f_phase

                self.x_frequency = x_frequency
                self.f_gain = f_gain
                self.f_phase = f_phase
                self.phase_num = phase_num
                # return x_frequency, f_gain, phase_num

            except Exception as e:
                raise ValueError('导入失败:' + str(e))

    def import_filter_txt(self, path):
        x_frequency, f_gain, phase_num = np.loadtxt(path, unpack=True, encoding='utf-8')
        self.x_frequency = x_frequency
        self.f_gain = f_gain
        self.f_phase = phase_num
        self.phase_num = phase_num
        # return x_frequency, f_gain, phase_num


if __name__ == '__main__':
    from includes.my_filter_simulator import MyFilterSimulator  # netlist仿真计算机绘图类

    path = r'F:\python_company\ANC_filter_calculate\data_examples\export_excel_test.xls'
    # path = r'E:\AMS\FB_Filter_Calculation - example.xlsx'
    test = FilterImport(path)
    simulator = MyFilterSimulator()
    simulator.my_bode_diagram(analysis=None, aim_curve_data=test)  ##绘制伯德图
