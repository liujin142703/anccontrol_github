#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/7/1 9:44

"""
VA6610芯片通过I2C接口读写寄存器类
USB接口芯片型号：PIC24FJ64GB
MyHID: 主芯片控制类
HIDSlave：从芯片控制类
"""

import os
import time
import threading
import ctypes
from queue import Queue
import numpy as np
from PyQt5 import QtCore

so = ctypes.cdll.LoadLibrary
path = os.path.join(os.path.abspath('.'), 'libHID', 'x32', 'LibHID.dll')
lib = so(path)
lib.HID_Init()
_lock = threading.Lock()
usb_connect = False


class MyHID(QtCore.QObject):
    """master芯片及USB连接检测及读写控制类"""
    num = 3
    delay_time = 0.02
    register_addrs = [0x10, 0x11, 0x12, 0x13,
                      0x14, 0x15, 0x16, 0x17, 0x20,
                      0x21, 0x30, 0x31, 0x32, 0x33,
                      0x34, 0x35, 0x3d, 0x3e, 0x3f]
    signal = QtCore.pyqtSignal(list)  # 读取到的寄存器值
    state_signal = QtCore.pyqtSignal(str)
    otp_burn_times_signal = QtCore.pyqtSignal(int)
    otp_burn_state_signal = QtCore.pyqtSignal(str)
    ui_changed_queue = Queue(maxsize=1000)
    ui_load_queue = Queue(maxsize=1000)
    ui_burn_queue = Queue(maxsize=1000)

    def __init__(self):
        super(MyHID, self).__init__()
        self.state = 'no_usb'
        self.chip_first_connect = True
        self.ui_changed = []
        self.tr_flag = False

    @staticmethod
    def check_usb_connect():
        global usb_connect
        if lib.HID_Detect():
            usb_connect = True
            return True
        else:
            usb_connect = False
            return False

    def init_usb(self):
        """
        初始化USB连接
        :return:false 连接失败，true 连接成功
        """
        lib.HID_Connect()
        a = np.array([0x00, 0x07, 0x04, 0x03, 0x01, 0x04, 0x04, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb]).astype(np.uint8)
        a_ctypes_ptr = ctypes.cast(a.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        b = np.zeros(65).astype(np.uint8)
        b_ctypes_ptr = ctypes.cast(b.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(a_ctypes_ptr, 65)
        self.hid_read(b_ctypes_ptr, 65)

        a = np.array([0x00, 0x01, 0x05, 0x00, 0x67, 0x00, 0x00, 0x00, 0x03, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb]).astype(np.uint8)
        a_ctypes_ptr = ctypes.cast(a.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(a_ctypes_ptr, 65)
        self.hid_read(b_ctypes_ptr, 65)

        a = np.array([0x00, 0x02, 0x0c, 0x00, 0xe2, 0x00, 0x07, 0x00,
                      0x00, 0x02, 0x01, 0x02, 0x00, 0x00, 0x00, 0x00,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb]).astype(np.uint8)
        a_ctypes_ptr = ctypes.cast(a.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(a_ctypes_ptr, 65)

        return True

    def check_chip_connect(self):
        print('inter check')
        a = np.array([0x00, MyHID.num, 0x08, 0x00, 0x61, 0x00, 0x03, 0x00,
                      0x01, 0x8e, 0x20, 0x8f, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb]).astype(np.int8)
        a_ctypes_ptr = ctypes.cast(a.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        b = np.zeros(65).astype(np.uint8)
        b_ctypes_ptr = ctypes.cast(b.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(a_ctypes_ptr, 65)
        self.hid_read(b_ctypes_ptr, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256
        print(b[6])
        print('leave check')
        if b[6] == 0x00 and b[2] == 0x06:
            return True
        else:
            return False

    def lib_hid_read(self, ctypes_ptr, num=65):
        """hid_read子线程，tr_flag = False为读取完成标志"""
        lib.HID_Read(ctypes_ptr, num)
        self.tr_flag = False

    def hid_read(self, ctypes_ptr, num=65):
        """读取芯片参数线程，当获得读取完成标志or超时2秒后结束此父线程，子线程自动结束"""
        self.tr_flag = True
        son = threading.Thread(target=self.lib_hid_read, args=(ctypes_ptr, num))
        son.setDaemon(True)
        son.start()
        time.sleep(0.004)
        start_time = time.time()
        while time.time() - start_time < 2:
            if not self.tr_flag:
                break
            else:
                time.sleep(0.1)

    @staticmethod
    def register_write_prepare():
        otp_read1 = np.array([0x00, MyHID.num, 0x08, 0x00, 0xe1, 0x00, 0x03, 0x00,
                              0x00, 0x8e, 0x20, 0x09, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb]).astype(np.int8)
        otp_read1_ctypes_ptr = ctypes.cast(otp_read1.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(otp_read1_ctypes_ptr, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256
        otp_write = np.array([0x00, MyHID.num, 0x08, 0x00, 0xe1, 0x00, 0x03, 0x00,
                              0x00, 0x8e, 0x3f, 0x02, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb]).astype(np.int8)
        otp_write_ctypes_ptr = ctypes.cast(otp_write.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(otp_write_ctypes_ptr, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256

    @staticmethod
    def register_write(addr, value):
        """
        寄存器更改函数，发送数据格式：0x00, MyHID.num, 0x08, 0x00, 0xe1, 0x00, 0x03, 0x00, 0x00, 0x8e, addr, value
        :param addr: 寄存器地址
        :param value: addr及对应的value
        :return: None
        """
        a001 = np.array([0x00, MyHID.num, 0x08, 0x00, 0xe1, 0x00, 0x03, 0x00,
                         0x00, 0x8e, addr, value, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb]).astype(np.int8)
        a_ctypes_ptr_001 = ctypes.cast(a001.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(a_ctypes_ptr_001, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256

    @staticmethod
    def register_read_prepare():
        otp_read1 = np.array([0x00, MyHID.num, 0x08, 0x00, 0xe1, 0x00, 0x03, 0x00,
                              0x00, 0x8e, 0x20, 0x09, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb]).astype(np.int8)
        otp_read1_ctypes_ptr = ctypes.cast(otp_read1.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(otp_read1_ctypes_ptr, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256

        otp_read2 = np.array([0x00, MyHID.num, 0x08, 0x00, 0xe1, 0x00, 0x03, 0x00,
                              0x00, 0x8e, 0x3f, 0x00, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb]).astype(np.int8)
        otp_read2_ctypes_ptr = ctypes.cast(otp_read2.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(otp_read2_ctypes_ptr, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256

    def register_read(self, addr):
        """
        寄存器读取函数，发送数据读取格式：0x00, MyHID.num, 0x08, 0x00, 0x61, 0x00, 0x03, 0x00,0x01, 0x8e, addr, 0x8f,
        :param addr: 待读取的寄存器地址
        :return: 寄存器地址下对应的value
        """
        a002 = np.array([0x00, MyHID.num, 0x08, 0x00, 0x61, 0x00, 0x03, 0x00,
                         0x01, 0x8e, addr, 0x8f, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb]).astype(np.int8)
        a_ctypes_ptr_002 = ctypes.cast(a002.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        b08 = np.zeros(65).astype(np.uint8)
        b_ctypes_ptr_08 = ctypes.cast(b08.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(a_ctypes_ptr_002, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256
        self.hid_read(b_ctypes_ptr_08, 65)
        if b08[6] == 0xfd and addr != 0x3f:
            raise ValueError('读取到0x3d')
        return b08[9]  # 返回register addr对应的value

    def register_load(self, read=False):
        self.register_write(0x20, 0x09)
        self.register_write(0x3f, 0x01)
        self.register_read(0x30)
        time.sleep(0.015)
        self.register_read(0x34)
        time.sleep(0.015)
        self.register_read(0x10)
        time.sleep(0.015)
        self.register_read(0x14)
        time.sleep(0.015)
        if read:
            self.register_read_prepare()
            for addr in MyHID.register_addrs:
                value = self.register_read(addr)  # 读取芯片寄存器value
                self.signal.emit([addr, value])  # 根据读取值更改软件界面

    # def register_burn(self):
    #     otp_burn_addrs = [0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17]
    #     current_data = dict()  # 待烧入参数
    #     self.register_read_prepare()
    #     for addr in otp_burn_addrs:
    #         value = self.register_read(addr)
    #         current_data[addr] = value
    #
    #     self.register_load(read=False)  # OTP保险丝数据
    #     otp_data = dict()
    #     self.register_read_prepare()
    #     for addr in otp_burn_addrs:
    #         value = self.register_read(addr)
    #         otp_data[addr] = value
    #
    #     if otp_data[0x13] != 0:
    #         print('无法烧录')
    #         raise EnvironmentError('已烧录3次，无法继续烧录')
    #     else:
    #         for addr in otp_burn_addrs:  # 还原芯片接入状态参数
    #             self.register_write_prepare()
    #             self.register_write(addr, current_data[addr])
    #
    #         current_data1 = dict()
    #         self.register_read_prepare()
    #         for addr in otp_burn_addrs:
    #             value = self.register_read(addr)
    #             current_data1[addr] = value
    #
    #         if current_data1 == current_data:
    #             print('开始烧录')
    #             self.register_write_prepare()
    #             self.register_write(0x3f, 0x03)
    #             self.register_read_prepare()
    #
    #             value = self.register_read(0x3f)
    #             assert value == 0x03
    #             time.sleep(0.015)
    #
    #             value = self.register_read(0x30)
    #             # assert value == 0x00
    #             time.sleep(0.015)
    #
    #             value = self.register_read(0x1f)
    #             # assert value == 0x00
    #             time.sleep(0.015)
    #
    #             value = self.register_read(0x10)
    #             # assert value == 0x00
    #             time.sleep(0.015)
    #
    #             return True
    #
    #         else:
    #             raise ValueError('参数验证失败')

    def register_burn(self):  # burn 不做参数检查
        self.register_write(0x20, 0x09)
        self.register_write(0x3f, 0x03)

        value = self.register_read(0x3f)
        print('3f register: ',value)
        time.sleep(0.015)

        value = self.register_read(0x30)
        # assert value == 0x00
        time.sleep(0.015)

        value = self.register_read(0x1f)
        # assert value == 0x00
        time.sleep(0.015)

        value = self.register_read(0x10)
        # assert value == 0x00
        time.sleep(0.015)

        return True


    # 槽
    def ui_changed_slot(self, data):
        self.ui_changed_queue.put(data)

    def ui_load_slot(self):
        self.ui_load_queue.put(True)

    def ui_burn_slot(self):
        self.ui_burn_queue.put(True)

    # state
    def state_no_usb(self):
        print('检测USB中...')
        _lock.acquire()
        try:
            self.state_signal.emit('USB未连接...')
            if self.check_usb_connect():  # 连接成功
                try:
                    self.init_usb()
                    return 'no_chip'
                except Exception as e:
                    raise IOError('USB初始化失败：\n' + str(e))

            else:  # 连接不成功，重新识别
                if lib.HID_IsConncet():
                    lib.HID_Disconnect()
                time.sleep(0.5)
                return 'no_usb'
        finally:
            _lock.release()

    def state_no_chip(self):
        print('检测chip中...')
        _lock.acquire()
        try:
            self.state_signal.emit('USB已连接,检测芯片中...')
            time.sleep(self.delay_time)
            if self.check_usb_connect():
                if self.check_chip_connect():
                    self.chip_first_connect = True
                    return 'connect_success'
                else:
                    return 'no_chip'
            else:
                return 'no_usb'
        finally:
            _lock.release()

    def state_load(self):
        _lock.acquire()
        try:
            print('master get load signal, start load')
            self.register_load(read=True)
            return 'connect_success'
        except Exception as e:
            print('load fail:' + str(e))
            return 'connect_success'
        finally:
            _lock.release()

    def state_burn(self):
        _lock.acquire()
        try:
            print('master get burn signal, start load')
            self.register_burn()
            self.otp_burn_state_signal.emit('烧录成功')
            return 'connect_success'
        except Exception as e:
            print('burn fail:' + str(e))
            self.otp_burn_state_signal.emit('烧录失败:' + '\n' + str(e))
            return 'no_chip'
        finally:
            _lock.release()

    def state_connect_success(self):
        # print('芯片已连接...')
        self.state_signal.emit('芯片已连接...')
        _lock.acquire()
        try:
            if self.chip_first_connect:  # 第一次连接写入版本信息等
                print('第一次连接')
                current_data = dict()  # 读取当前芯片参数值并调整UI
                self.register_read_prepare()
                for addr in MyHID.register_addrs:
                    value = self.register_read(addr)
                    self.signal.emit([addr, value])
                    current_data[addr] = value
                    time.sleep(self.delay_time)

                self.register_load(read=False)  # 载入OTP保险丝数据
                otp_data = dict()
                self.register_read_prepare()
                for addr in MyHID.register_addrs:
                    value = self.register_read(addr)
                    otp_data[addr] = value

                if otp_data[0x13] != 0:
                    self.otp_burn_times_signal.emit(0)
                elif otp_data[0x11] != 0:
                    self.otp_burn_times_signal.emit(1)
                elif otp_data[0x30] != 0x80 or otp_data[0x31] != 0x80:
                    self.otp_burn_times_signal.emit(2)
                else:
                    self.otp_burn_times_signal.emit(3)
                    self.ui_load_queue.put(False)

                while self.ui_load_queue.empty():
                    _lock.release()
                    time.sleep(1)
                    _lock.acquire()

                choice = self.ui_load_queue.get()

                if choice:
                    print('选择load')
                    self.register_load(read=True)
                else:
                    print('选择忽略')
                    for addr in MyHID.register_addrs:  # 还原芯片接入状态参数
                        self.register_write_prepare()
                        self.register_write(addr, current_data[addr])

                self.chip_first_connect = False

            for addr in MyHID.register_addrs:
                self.register_read_prepare()
                value = self.register_read(addr)  # 读取芯片寄存器value
                self.signal.emit([addr, value])  # 根据读取值更改软件界面
                time.sleep(self.delay_time)
                while not self.ui_changed_queue.empty():
                    data = self.ui_changed_queue.get()
                    # print('UI界面调整，master开始写入参数')
                    # print(str(hex(data[0])) + ' ' + str(hex(data[1])))
                    self.register_write_prepare()
                    self.register_write(data[0], data[1])
                    # print('写入完成')

            if not self.check_chip_connect():
                return 'no_chip'

            while not self.ui_load_queue.empty():
                self.ui_load_queue.get()
                return 'load'

            while not self.ui_burn_queue.empty():
                self.ui_burn_queue.get()
                return 'burn'

            return 'connect_success'

        except Exception as e:
            # print('state_connect_success错误：' + str(e))
            return 'no_chip'
        finally:
            _lock.release()

    def run(self):
        while self.state != 'exit':
            self.state = getattr(self, 'state_' + self.state)()

    def test(self, args):
        # print([hex(i) for i in args])  # 打印读取值
        pass


class HIDSlave(QtCore.QObject):
    """master芯片及USB连接检测及读写控制类"""
    num = 3
    delay_time = 0.02
    register_addrs = [0x10, 0x11, 0x12, 0x13,
                      0x14, 0x15, 0x16, 0x17, 0x20,
                      0x21, 0x30, 0x31, 0x32, 0x33,
                      0x34, 0x35, 0x3d, 0x3e, 0x3f]
    signal = QtCore.pyqtSignal(list)  # 读取到的寄存器值
    state_signal = QtCore.pyqtSignal(str)
    otp_burn_times_signal = QtCore.pyqtSignal(int)
    otp_burn_state_signal = QtCore.pyqtSignal(str)
    ui_changed_queue = Queue(maxsize=1000)
    ui_load_queue = Queue(maxsize=1000)
    ui_burn_queue = Queue(maxsize=1000)

    def __init__(self):
        super(HIDSlave, self).__init__()
        self.state = 'no_usb'
        self.chip_first_connect = True
        self.ui_changed = []
        self.tr_flag = False

    @staticmethod
    def check_usb_connect():
        global usb_connect
        if usb_connect:
            return True
        else:
            return False

    def init_usb(self):
        """
        初始化USB连接
        :return:false 连接失败，true 连接成功
        """
        lib.HID_Connect()
        a = np.array([0x00, 0x07, 0x04, 0x03, 0x01, 0x04, 0x04, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb]).astype(np.uint8)
        a_ctypes_ptr = ctypes.cast(a.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        b = np.zeros(65).astype(np.uint8)
        b_ctypes_ptr = ctypes.cast(b.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(a_ctypes_ptr, 65)
        self.hid_read(b_ctypes_ptr, 65)

        a = np.array([0x00, 0x01, 0x05, 0x00, 0x67, 0x00, 0x00, 0x00, 0x03, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb]).astype(np.uint8)
        a_ctypes_ptr = ctypes.cast(a.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(a_ctypes_ptr, 65)
        self.hid_read(b_ctypes_ptr, 65)

        a = np.array([0x00, 0x02, 0x0c, 0x00, 0xe2, 0x00, 0x07, 0x00,
                      0x00, 0x02, 0x01, 0x02, 0x00, 0x00, 0x00, 0x00,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb]).astype(np.uint8)
        a_ctypes_ptr = ctypes.cast(a.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(a_ctypes_ptr, 65)

        return True

    def check_chip_connect(self):
        a = np.array([0x00, MyHID.num, 0x08, 0x00, 0x61, 0x00, 0x03, 0x00,
                      0x01, 0x8c, 0x20, 0x8d, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                      0xcb]).astype(np.int8)
        a_ctypes_ptr = ctypes.cast(a.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        b = np.zeros(65).astype(np.uint8)
        b_ctypes_ptr = ctypes.cast(b.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(a_ctypes_ptr, 65)
        self.hid_read(b_ctypes_ptr, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256
        if b[6] == 0x00 and b[2] == 0x06:
            return True
        else:
            return False

    def lib_hid_read(self, ctypes_ptr, num=65):
        """hid_read子线程，tr_flag = False为读取完成标志"""
        lib.HID_Read(ctypes_ptr, num)
        self.tr_flag = False

    def hid_read(self, ctypes_ptr, num=65):
        """读取芯片参数线程，当获得读取完成标志or超时2秒后结束此父线程，子线程自动结束"""
        self.tr_flag = True
        son = threading.Thread(target=self.lib_hid_read, args=(ctypes_ptr, num))
        son.setDaemon(True)
        son.start()
        time.sleep(0.004)
        start_time = time.time()
        while time.time() - start_time < 2:
            if not self.tr_flag:
                break
            else:
                time.sleep(0.1)

    @staticmethod
    def register_write_prepare():
        otp_read1 = np.array([0x00, MyHID.num, 0x08, 0x00, 0xe1, 0x00, 0x03, 0x00,
                              0x00, 0x8c, 0x20, 0x09, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb]).astype(np.int8)
        otp_read1_ctypes_ptr = ctypes.cast(otp_read1.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(otp_read1_ctypes_ptr, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256
        otp_write = np.array([0x00, MyHID.num, 0x08, 0x00, 0xe1, 0x00, 0x03, 0x00,
                              0x00, 0x8c, 0x3f, 0x02, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb]).astype(np.int8)
        otp_write_ctypes_ptr = ctypes.cast(otp_write.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(otp_write_ctypes_ptr, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256

    @staticmethod
    def register_write(addr, value):
        """
        寄存器更改函数，发送数据格式：0x00, MyHID.num, 0x08, 0x00, 0xe1, 0x00, 0x03, 0x00, 0x00, 0x8e, addr, value
        :param addr: 寄存器地址
        :param value: addr及对应的value
        :return: None
        """
        a001 = np.array([0x00, MyHID.num, 0x08, 0x00, 0xe1, 0x00, 0x03, 0x00,
                         0x00, 0x8c, addr, value, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb]).astype(np.int8)
        a_ctypes_ptr_001 = ctypes.cast(a001.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(a_ctypes_ptr_001, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256

    @staticmethod
    def register_read_prepare():
        otp_read1 = np.array([0x00, MyHID.num, 0x08, 0x00, 0xe1, 0x00, 0x03, 0x00,
                              0x00, 0x8c, 0x20, 0x09, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb]).astype(np.int8)
        otp_read1_ctypes_ptr = ctypes.cast(otp_read1.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(otp_read1_ctypes_ptr, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256

        otp_read2 = np.array([0x00, MyHID.num, 0x08, 0x00, 0xe1, 0x00, 0x03, 0x00,
                              0x00, 0x8c, 0x3f, 0x00, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                              0xcb,
                              0xcb]).astype(np.int8)
        otp_read2_ctypes_ptr = ctypes.cast(otp_read2.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(otp_read2_ctypes_ptr, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256

    def register_read(self, addr):
        """
        寄存器读取函数，发送数据读取格式：0x00, MyHID.num, 0x08, 0x00, 0x61, 0x00, 0x03, 0x00,0x01, 0x8e, addr, 0x8f,
        :param addr: 待读取的寄存器地址
        :return: 寄存器地址下对应的value
        """
        a002 = np.array([0x00, MyHID.num, 0x08, 0x00, 0x61, 0x00, 0x03, 0x00,
                         0x01, 0x8c, addr, 0x8d, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb, 0xcb,
                         0xcb]).astype(np.int8)
        a_ctypes_ptr_002 = ctypes.cast(a002.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        b = np.zeros(65).astype(np.uint8)
        b_ctypes_ptr = ctypes.cast(b.ctypes.data, ctypes.POINTER(ctypes.c_int8))
        lib.HID_Write(a_ctypes_ptr_002, 65)
        MyHID.num += 1
        MyHID.num = MyHID.num % 256
        self.hid_read(b_ctypes_ptr, 65)
        if b[6] == 0xfd and addr != 0x3f:
            raise ValueError('slave芯片连接失败')
        return b[9]  # 返回register addr对应的value

    def register_load(self, read=False):
        self.register_write(0x20, 0x09)
        self.register_write(0x3f, 0x01)
        self.register_read(0x30)
        time.sleep(0.015)
        self.register_read(0x34)
        time.sleep(0.015)
        self.register_read(0x10)
        time.sleep(0.015)
        self.register_read(0x14)
        time.sleep(0.015)
        if read:
            self.register_read_prepare()
            for addr in MyHID.register_addrs:
                value = self.register_read(addr)  # 读取芯片寄存器value
                self.signal.emit([addr, value])  # 根据读取值更改软件界面

    def register_burn(self):  # burn 不做参数检查
        self.register_write(0x20, 0x09)
        self.register_write(0x3f, 0x03)

        value = self.register_read(0x3f)
        print('3f register: ',value)
        time.sleep(0.015)

        value = self.register_read(0x30)
        # assert value == 0x00
        time.sleep(0.015)

        value = self.register_read(0x1f)
        # assert value == 0x00
        time.sleep(0.015)

        value = self.register_read(0x10)
        # assert value == 0x00
        time.sleep(0.015)

        return True

    # 槽
    def ui_changed_slot(self, data):
        self.ui_changed_queue.put(data)

    def ui_load_slot(self):
        self.ui_load_queue.put(True)

    def ui_burn_slot(self):
        self.ui_burn_queue.put(True)

    # state
    def state_no_usb(self):
        # print('检测USB中...')
        _lock.acquire()
        try:
            self.state_signal.emit('USB未连接...')
            if self.check_usb_connect():  # 连接成功
                try:
                    # self.init_usb()
                    return 'no_chip'
                except Exception as e:
                    raise IOError('USB初始化失败：\n' + str(e))

            else:  # 连接不成功，重新识别
                if lib.HID_IsConncet():
                    lib.HID_Disconnect()
                time.sleep(0.05)
                return 'no_usb'
        finally:
            _lock.release()

    def state_no_chip(self):
        # print('检测chip中...')
        _lock.acquire()
        try:
            self.state_signal.emit('slave芯片未连接...')
            time.sleep(self.delay_time)
            if self.check_usb_connect():
                if self.check_chip_connect():
                    self.chip_first_connect = True
                    return 'connect_success'
                else:
                    return 'no_chip'
            else:

                return 'no_usb'
        finally:
            _lock.release()
            time.sleep(0.1)

    def state_load(self):
        _lock.acquire()
        try:
            print('master get load signal, start load')
            self.register_load(read=True)
            return 'connect_success'
        except Exception as e:
            print('load fail:' + str(e))
            return 'connect_success'
        finally:
            _lock.release()

    def state_burn(self):
        _lock.acquire()
        try:
            print('master get burn signal, start load')
            self.register_burn()
            self.otp_burn_state_signal.emit('烧录成功')
            return 'connect_success'
        except Exception as e:
            print('burn fail:' + str(e))
            self.otp_burn_state_signal.emit('烧录失败:' + '\n' + str(e))
            return 'no_chip'
        finally:
            _lock.release()

    def state_connect_success(self):
        # print('slave芯片已连接...')
        self.state_signal.emit('slave芯片已连接...')
        _lock.acquire()
        try:
            if self.chip_first_connect:  # 第一次连接写入版本信息等
                print('第一次连接')
                current_data = dict()  # 读取当前芯片参数值并调整UI
                self.register_read_prepare()
                for addr in MyHID.register_addrs:
                    value = self.register_read(addr)
                    self.signal.emit([addr, value])
                    current_data[addr] = value
                    time.sleep(self.delay_time)

                self.register_load(read=False)  # 载入OTP保险丝数据
                otp_data = dict()
                self.register_read_prepare()
                for addr in MyHID.register_addrs:
                    value = self.register_read(addr)
                    otp_data[addr] = value

                if otp_data[0x13] != 0:
                    self.otp_burn_times_signal.emit(0)
                elif otp_data[0x11] != 0:
                    self.otp_burn_times_signal.emit(1)
                elif otp_data[0x30] != 0x80 or otp_data[0x31] != 0x80:
                    self.otp_burn_times_signal.emit(2)
                else:
                    self.otp_burn_times_signal.emit(3)
                    self.ui_load_queue.put(False)

                while self.ui_load_queue.empty():
                    _lock.release()
                    time.sleep(1)
                    _lock.acquire()

                choice = self.ui_load_queue.get()

                if choice:
                    print('选择load')
                    self.register_load(read=True)
                else:
                    print('选择忽略')
                    for addr in MyHID.register_addrs:  # 还原芯片接入状态参数
                        self.register_write_prepare()
                        self.register_write(addr, current_data[addr])

                self.chip_first_connect = False

            for addr in MyHID.register_addrs:
                self.register_read_prepare()
                value = self.register_read(addr)  # 读取芯片寄存器value
                self.signal.emit([addr, value])  # 根据读取值更改软件界面
                time.sleep(self.delay_time)
                while not self.ui_changed_queue.empty():
                    data = self.ui_changed_queue.get()
                    # print('UI界面调整，slave芯片开始写入参数')
                    # print(str(hex(data[0])) + ' ' + str(hex(data[1])))
                    self.register_write_prepare()
                    self.register_write(data[0], data[1])
                    # print('写入完成')

            if not self.check_chip_connect():
                return 'no_chip'

            while not self.ui_load_queue.empty():
                self.ui_load_queue.get()
                return 'load'

            while not self.ui_burn_queue.empty():
                self.ui_burn_queue.get()
                return 'burn'

            return 'connect_success'

        except Exception as e:
            # print('state_connect_success错误：' + str(e))
            return 'no_chip'
        finally:
            _lock.release()

    def run(self):
        while self.state != 'exit':
            self.state = getattr(self, 'state_' + self.state)()

    def test(self, args):
        # print([hex(i) for i in args])  # 打印读取值
        pass


if __name__ == '__main__':
    usb1 = MyHID()
    usb1.run()
