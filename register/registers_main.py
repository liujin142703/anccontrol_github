#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/3/15 17:00
import sys
from PyQt5 import QtWidgets, QtCore
from register.registers_UI import Ui_Dialog
from config import *


class RegisterWindow(QtWidgets.QDialog, Ui_Dialog):
    signal = QtCore.pyqtSignal(list)  # 改变的寄存器值

    def __init__(self, data_map=None):
        super(RegisterWindow, self).__init__()
        self.setupUi(self)
        self.data_map = data_map
        self.set_default_data(self.data_map)
        self.tableWidget.itemDoubleClicked.connect(self.change_map_data)
        self.buttonBox.accepted.connect(self.accept)

    def set_default_data(self, data_map):
        # 自动可伸缩
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableWidget.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        # 初始化第一列addr数据
        row = 0
        for i in register_addrs_list:
            new_item = QtWidgets.QTableWidgetItem(str(hex(i)))
            new_item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            self.tableWidget.setItem(row, 0, new_item)
            row += 1

        if data_map:  # 有数据传入时，根据传入数据设置map表
            for i in range(1, 9):
                for j in range(19):
                    item = QtWidgets.QTableWidgetItem((data_map[j].bool_to_01())[i - 1])
                    item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
                    self.tableWidget.setItem(j, i, item)
            self.calculate_value(data_map)

        else:
            # 重置 value map 置零
            for i in range(1, 9):
                for j in range(19):
                    item = QtWidgets.QTableWidgetItem('0')
                    item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
                    self.tableWidget.setItem(j, i, item)
            self.calculate_value(data_map)
            #  value 置零
            # for i in range(19):
            #     item = QtWidgets.QTableWidgetItem('0x00')
            #     item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            #     self.tableWidget.setItem(i, 9, item)

    def calculate_value(self, data_map):
        for j in range(19):
            value = data_map[j].hex_value()
            item = QtWidgets.QTableWidgetItem(str(value))
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            self.tableWidget.setItem(j, 9, item)

    def change_map_data(self, e):
        if e.row() in range(19) and e.column() in range(1, 9):
            if e.data(0) == '0':
                e.setData(0, '1')
            else:
                e.setData(0, '0')

            for i in range(1, 9):
                for j in range(19):
                    self.data_map[j].bit[i - 1] = bool(int(self.tableWidget.item(j, i).data(0)))

            self.calculate_value(self.data_map)
            change_register_data = [e.row(), int(self.tableWidget.item(e.row(), 9).data(0), 16)]
            # print(change_register_data)
            self.signal.emit(change_register_data)


if __name__ == '__main__':
    from register import row_data

    row00 = row_data.RowData(True, False, False, False, False, False, False, False)
    row01 = row_data.RowData(False, False, False, False, False, False, False, False)
    row02 = row_data.RowData(True, False, False, False, False, False, False, False)
    row03 = row_data.RowData(False, False, False, False, False, False, False, False)
    row04 = row_data.RowData(True, True, False, False, False, False, False, False)
    row05 = row_data.RowData(False, False, False, False, False, False, False, False)
    row06 = row_data.RowData(True, False, False, False, False, False, False, False)
    row07 = row_data.RowData(False, False, False, False, False, False, False, False)
    row08 = row_data.RowData(True, True, True, False, True, False, False, True)
    row09 = row_data.RowData(False, False, True, True, True, True, True, True)
    row10 = row_data.RowData(True, False, False, False, False, False, False, False)
    row11 = row_data.RowData(True, False, False, False, False, False, False, False)
    row12 = row_data.RowData(False, False, False, False, False, False, False, False)
    row13 = row_data.RowData(False, False, False, False, False, False, False, False)
    row14 = row_data.RowData(False, False, False, False, False, False, False, False)
    row15 = row_data.RowData(True, False, False, False, False, False, False, False)
    row16 = row_data.RowData(False, False, False, False, False, False, False, False)
    row17 = row_data.RowData(False, False, False, False, False, False, False, False)
    row18 = row_data.RowData(False, False, False, False, False, False, False, False)
    registers_map = [row00, row01, row02, row03, row04, row05, row06, row07, row08, row09, row10,
                     row11, row12, row13, row14, row15, row16, row17, row18]
    app = QtWidgets.QApplication(sys.argv)
    win = RegisterWindow(registers_map)
    win.show()
    sys.exit(app.exec_())
