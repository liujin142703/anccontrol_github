#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/8/30 11:34
import sys
import os
import threading
import ctypes
from PyQt5 import QtWidgets, QtCore
from register.register_rw_ui import Ui_Dialog
from config import *

so = ctypes.windll.LoadLibrary
path = os.path.join(os.getcwd(), 'USB_I2C', 'USBIOX.DLL')
lib = so(path)
_lock = threading.Lock()


class MyCH341AControlWindow(QtWidgets.QDialog, Ui_Dialog):
    num = 3
    delay_time = 0.02
    register_write_signal = QtCore.pyqtSignal(list)  # 改变的寄存器值

    def __init__(self, connect_state, chip_num):
        super(MyCH341AControlWindow, self).__init__()
        self.setupUi(self)
        self.signals_slots()
        if enable_registers_new_addr:  # 新版register地址映射
            self.power_addr = 0x01
            self.register_addrs_list = [i for i in range(64)]
        else:  # 旧版register地址映射
            self.power_addr = 0x20
            self.register_addrs_list = [0x10, 0x11, 0x12, 0x13,
                                        0x14, 0x15, 0x16, 0x17, 0x20,
                                        0x21, 0x30, 0x31, 0x32, 0x33,
                                        0x34, 0x35, 0x3d, 0x3e, 0x3f,
                                        0x36, 0x37, 0x38, 0x39, 0x18,
                                        0x19, 0x22, 0x23, 0x24, 0x25,
                                        0x26, 0x27, 0x28, 0x29, 0x3a,
                                        0x3b, 0x3c, 0x2c]
        self.i2c_init(connect_state, chip_num)

    def i2c_init(self, connect_state, chip_num):
        if connect_state == '芯片已连接...':
            self.groupBox.setEnabled(True)
            if chip_num == 0:  # 控制主芯片
                self.label_connect_state.setText('芯片已连接:控制芯片1')
                if enable_registers_new_addr:
                    self.i2c_addr = 0x9a
                else:
                    self.i2c_addr = 0x8e
            else:  # 控制从芯片
                self.label_connect_state.setText('芯片已连接:控制芯片2')
                if enable_registers_new_addr:
                    self.i2c_addr = 0x98
                else:
                    self.i2c_addr = 0x8c
        else:
            self.groupBox.setEnabled(False)

    def signals_slots(self):
        self.btn_write.clicked.connect(self.write_register)
        self.btn_read.clicked.connect(self.read_register)

    def ch341a_i2c_read(self, addr):
        addr = int(addr)
        data = ctypes.create_string_buffer(1)
        mbuffer = ctypes.create_string_buffer(32)
        mbuffer[0] = self.i2c_addr
        mbuffer[1] = addr

        lib.USBIO_StreamI2C(0, 2, mbuffer, 1, data)  # 处理I2C数据流函数
        a = int.from_bytes(data.value, 'big')

        return a

    def ch341a_i2c_write(self, addr, value):
        addr = int(addr)
        value = int(value)
        data = ctypes.create_string_buffer(1)
        mbuffer = ctypes.create_string_buffer(32)
        mbuffer[0] = self.i2c_addr
        mbuffer[1] = addr
        mbuffer[2] = value

        lib.USBIO_StreamI2C(0, 3, mbuffer, 0, data)

    def write_register(self):
        addr = int(self.le_write_addr.text(), base=16)
        value = int(self.le_write_value.text(), base=16)
        if addr in self.register_addrs_list and value < 256:
            self.register_write_signal.emit([addr, value])
        else:
            QtWidgets.QMessageBox.information(self, '提示', 'addr/value值非法')

    def read_register(self):
        addr = int(self.le_read_addr.text(), base=16)
        if addr in self.register_addrs_list:
            _lock.acquire()
            try:
                self.ch341a_i2c_write(self.power_addr, 0xe9)
                self.ch341a_i2c_write(0x3f, 0x00)
                value = self.ch341a_i2c_read(addr)
                self.label_read_value.setText('get：' + hex(value))
            finally:
                _lock.release()
        else:
            QtWidgets.QMessageBox.information(self, '提示', 'addr值非法')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myWin = MyCH341AControlWindow()
    myWin.show()
    sys.exit(app.exec_())
