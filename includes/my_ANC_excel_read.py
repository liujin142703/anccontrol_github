#!/usr/bin/env python
# -*- coding:utf-8 -*-
import xlrd
import numpy as np


class My_ANC_ExcelRead(object):
    def __init__(self, path):
        self.path = path
        self.open_excel()

    def open_excel(self):
        with xlrd.open_workbook(self.path) as self.readbook:
            # 获取第0页sheet
            self.table0 = self.readbook.sheet_by_index(0)
            self.nrows = self.table0.nrows  # sheet最大行数
            self.ncols = self.table0.ncols  # sheet最大列数
            try:
                # 判断数据是否合法：总行数大于10行，起始频率位置判断设置为1~20k
                if int(self.nrows) > 10 \
                        and int(self.table0.cell_value(8, 0)) > 1 \
                        and int(self.table0.cell_value(8, 0)) < 20000:
                    # 获取第0列，8：end表格数值, 表格中为曲线x坐标，单位Hz
                    self.x_frequency = self.table0.col_values(0, start_rowx=8, end_rowx=self.nrows)
                    # 获取第15列，8：end表格数值，为滤波器幅值响应，单位dBV
                    self.f_gain = self.table0.col_values(15, start_rowx=8, end_rowx=self.nrows)
                    # 获取第16列，8：end表格数值，为滤波器相频响应，单位deg
                    self.f_phase = self.table0.col_values(16, start_rowx=8, end_rowx=self.nrows)
                    # 相位区间设置为-pi~pi,
                    self.f_phase_pi = np.array(self.f_phase)
                    self.f_phase_pi = self.f_phase_pi - 180
                    self.phase_num = (np.mod(self.f_phase_pi, 360) - 180)

            except:
                raise ValueError('参考数据不符合模板要求：\n'
                                 '数据从第9行开始：第1列为坐标轴，第16列为增益值，第17列为相位')


if __name__ == '__main__':
    from PyQt5 import QtWidgets
    from includes.my_filter_simulator import MyFilterSimulator  # netlist仿真计算机绘图类

    # path = r'F:\python_company\my_excel\FF FilterCalculation.xlsx'
    path = r'E:\AMS\FILTER\QC20-filter-3435\QC20-FB-20181026.xlsx'
    test = My_ANC_ExcelRead(path)
    simulator = MyFilterSimulator()
    simulator.my_bode_diagram(analysis=None, aim_curve_data=test)  ##绘制伯德图
