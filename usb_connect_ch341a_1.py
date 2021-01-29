#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2020/6/18 10:38

"""
VA6610芯片通过I2C接口读写寄存器类
USB接口芯片型号：CH341A
MyHID: 主芯片控制类
HIDSlave：从芯片控制类
"""

import os
import time
import threading
import ctypes
from queue import Queue
from PyQt5 import QtCore
import xml.etree.ElementTree as ET
from config import *

so = ctypes.windll.LoadLibrary
path = os.path.join(os.getcwd(), 'USB_I2C', 'USBIOX.DLL')
lib = so(path)
_lock = threading.Lock()


class CH341AI2CReadWrite(object):
    def __init__(self, i2c_addr):
        super(CH341AI2CReadWrite, self).__init__()
        self.i2c_addr = i2c_addr
        self.delay_time = 0.001

    def ch341a_i2c_write(self, addr, value):
        """
        寄存器更改函数
        :param addr: 寄存器地址
        :param value: addr及对应的value
        :return: None
        """
        if i2c_addr_bit_num == 8:
            addr = int(addr)
            value = int(value)
            data = ctypes.create_string_buffer(1)
            mbuffer = ctypes.create_string_buffer(32)
            mbuffer[0] = self.i2c_addr
            mbuffer[1] = addr
            mbuffer[2] = value

            lib.USBIO_StreamI2C(0, 3, mbuffer, 0, data)
        else:
            lib.USBIO_WriteI2C(0, self.i2c_addr, addr, value)

    def ch341a_i2c_read(self, addr):
        """
        寄存器读取函数
        :param addr: 待读取的寄存器地址
        :return: 寄存器地址下对应的value
        """
        if i2c_addr_bit_num == 8:
            addr = int(addr)

            data = ctypes.create_string_buffer(1)
            mbuffer = ctypes.create_string_buffer(32)
            mbuffer[0] = self.i2c_addr
            mbuffer[1] = addr

            lib.USBIO_StreamI2C(0, 2, mbuffer, 1, data)  # 处理I2C数据流函数
            a = int.from_bytes(data.value, 'big')

            return a
        else:
            data = ctypes.create_string_buffer(1)
            lib.USBIO_ReadI2C(0, self.i2c_addr, addr, data)
            a = int.from_bytes(data.value, 'big')
            return a

    def register_write_prepare(self):
        self.ch341a_i2c_write(power_addr, 0xe9)
        time.sleep(self.delay_time)
        self.ch341a_i2c_write(0x3f, 0x02)
        time.sleep(self.delay_time)

    def register_read_prepare(self):
        self.ch341a_i2c_write(0x3f, 0x00)
        time.sleep(self.delay_time)

    def VA6610_otp_write(self, addr, value):
        self.register_write_prepare()
        self.ch341a_i2c_write(addr, value)
        time.sleep(self.delay_time)

    def VA6610_otp_read(self, addr):
        self.register_read_prepare()
        a = self.ch341a_i2c_read(addr)
        time.sleep(self.delay_time)
        return a

    def otp_load(self):
        if registers_load_burn_mode == OTP_burn_model_for_VA6610:
            self.ch341a_i2c_write(power_addr, 0xe9)
            time.sleep(0.005)
            self.ch341a_i2c_write(register_addrs_list[18], 0x01)  # 0x3f
            time.sleep(0.005)
            self.ch341a_i2c_read(register_addrs_list[10])  # 0x30
            time.sleep(0.015)
            self.ch341a_i2c_read(register_addrs_list[14])  # 0x34
            time.sleep(0.015)
            self.ch341a_i2c_read(register_addrs_list[0])  # 0x10
            time.sleep(0.015)
            self.ch341a_i2c_read(register_addrs_list[4])  # 0x14
            time.sleep(0.015)
        elif registers_load_burn_mode == OTP_burn_model_for_VA6610D:
            self.ch341a_i2c_write(power_addr, 0xe9)
            time.sleep(0.005)
            self.ch341a_i2c_write(register_addrs_list[18], 0x01)
            time.sleep(0.005)
            self.ch341a_i2c_read(register_addrs_list[10])
            time.sleep(0.015)
            self.ch341a_i2c_read(register_addrs_list[14])
            time.sleep(0.015)
            self.ch341a_i2c_read(register_addrs_list[0])
            time.sleep(0.015)
            self.ch341a_i2c_read(register_addrs_list[4])
            time.sleep(0.015)

    def otp_burn(self):  # burn 不做参数检查
        if registers_load_burn_mode == OTP_burn_model_for_VA6610:
            self.ch341a_i2c_write(power_addr, 0xe9)
            self.ch341a_i2c_write(register_addrs_list[18], 0x03)
            self.ch341a_i2c_read(register_addrs_list[18])  #
            time.sleep(0.003)
            self.ch341a_i2c_read(register_addrs_list[10])
            time.sleep(0.003)
            self.ch341a_i2c_read(burn_register)
            time.sleep(0.003)
            self.ch341a_i2c_read(register_addrs_list[0])
            time.sleep(0.003)
            self.ch341a_i2c_read(register_addrs_list[14])
            time.sleep(0.015)
            self.ch341a_i2c_write(register_addrs_list[18], 0x00)
            return True
        elif registers_load_burn_mode == OTP_burn_model_for_VA6610D:
            addrs = [0x10, 0x12, 0x14, 0x34]
            for i in addrs:
                print('开始烧录:' + str(i))
                self.ch341a_i2c_write(power_addr, 0x09)  # Set bit EVAL_REG_ON in register 0x20
                self.ch341a_i2c_write(0x3f, 0x03)  # Set OTP_MODE register (0x3F bit [1:0]) to ‘11‘b
                self.ch341a_i2c_read(0x3f)  # Read register 0x3F
                time.sleep(0.005)  # waite 5ms
                self.ch341a_i2c_read(i)  # Read OTP register 0x30
                time.sleep(0.005)
                self.ch341a_i2c_write(0x3f, 0x00)  # Set OTP_MODE register (0x3F bit [1:0]) to ‘00‘b
                time.sleep(0.005)
                self.otp_load()  # load registers
            return True

    def check_chip_connect(self):
        self.register_read_prepare()
        time.sleep(self.delay_time)
        a = self.ch341a_i2c_read(power_addr)
        if a == 0xe9 or a == 0xe1:
            return True

        time.sleep(self.delay_time)
        self.ch341a_i2c_write(power_addr, 0xe9)
        time.sleep(self.delay_time)
        a = self.ch341a_i2c_read(power_addr)
        if a == 0xe9 or a == 0xe1:
            return True
        return False

    def init_registers(self):
        """芯片第一次连接时根据配置参数初始化registers"""
        try:
            tree = ET.parse(r'./default_register.xml')  # 读取xml
            root = tree.getroot()
            data = dict()
            for child in root.iter('reg'):  # 按照储存的nr数值填写value_map
                data[child.attrib['nr']] = child.attrib['val']
            self.register_write_prepare()
            for i in data.keys():
                addr = map_row2addr[int(i)]
                value = int(data[i], 16)
                self.ch341a_i2c_write(addr, value)
            print('芯片未烧录，已初始化')
        except Exception:
            print('芯片未烧录初始化失败')


class MyUSB(QtCore.QObject):
    """master芯片及USB连接检测及读写控制类"""
    num = 3
    delay_time = 0.001
    register_addrs = register_addrs_list
    signal = QtCore.pyqtSignal(list)  # 读取到的寄存器值
    state_signal = QtCore.pyqtSignal(str)
    otp_burn_times_signal = QtCore.pyqtSignal(int)
    otp_burn_state_signal = QtCore.pyqtSignal(str)
    ui_changed_queue = Queue(maxsize=1000)
    ui_load_queue = Queue(maxsize=1000)
    ui_burn_queue = Queue(maxsize=1000)
    ui_registers_init_queue = Queue(maxsize=1000)
    ui_power_off_queue = Queue(maxsize=1000)
    ui_power_on_queue = Queue(maxsize=1000)

    def __init__(self):
        super(MyUSB, self).__init__()
        self.state = 'no_usb'
        self.chip_first_connect = True
        self.restart = False
        self.ui_changed = []
        self.tr_flag = False
        self.usb_connected = False
        self.chip_detect_flag = True
        self.usb_hardware = CH341AI2CReadWrite(i2c_addr)

    def usb_connect_state_slot(self, e):
        if e:
            self.usb_connected = True
            print('USB连接')
        else:
            self.usb_connected = False
            print('USB未连接')

    def ui_changed_slot(self, data):
        self.ui_changed_queue.put(data)

    def ui_load_slot(self):
        self.ui_load_queue.put(True)

    def ui_burn_slot(self):
        self.ui_burn_queue.put(True)

    def ui_registers_init_slot(self):
        self.ui_registers_init_queue.put(True)

    def ui_pause_slot(self, e):
        if e:
            self.chip_detect_flag = False
        else:
            self.chip_detect_flag = True

    # state
    def state_no_usb(self):
        # print('检测USB中...')
        _lock.acquire()
        try:
            if self.usb_connected:
                return 'no_chip'
            else:
                self.state_signal.emit('USB未连接...')
                time.sleep(0.2)
                return 'no_usb'
        finally:
            _lock.release()

    def state_no_chip(self):
        _lock.acquire()
        try:
            if self.usb_connected and self.chip_detect_flag:
                if self.usb_hardware.check_chip_connect():
                    self.usb_hardware.ch341a_i2c_write(power_addr, 0xe9)
                    self.chip_first_connect = True
                    return 'connect_success'
                else:
                    self.state_signal.emit('USB已连接,检测芯片中...')
                    time.sleep(self.delay_time)
                    return 'no_chip'
            else:
                return 'no_usb'
        finally:
            _lock.release()

    def state_load(self):
        _lock.acquire()
        try:
            print('master get load signal, start load')
            self.usb_hardware.otp_load()
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
            self.usb_hardware.otp_burn()
            self.otp_burn_state_signal.emit('烧录成功')
            self.chip_first_connect = True
            return 'connect_success'
        except Exception as e:
            print('burn fail:' + str(e))
            self.otp_burn_state_signal.emit('烧录失败:' + '\n' + str(e))
            return 'no_chip'
        finally:
            _lock.release()

    def state_power_off(self):
        print('enter power off')
        state = self.ui_power_off_queue.get()
        _lock.acquire()
        try:
            # 防止芯片被设置为slide模式
            self.usb_hardware.register_read_prepare()
            value = self.usb_hardware.ch341a_i2c_read(register_addrs_list[7])
            if value | 0x7f == 0xff:
                self.usb_hardware.register_write_prepare()
                value &= 0x7f
                self.usb_hardware.ch341a_i2c_write(register_addrs_list[7], value)
            if state == '双芯片模式':
                time.sleep(0.003)
                self.usb_hardware = CH341AI2CReadWrite(i2c_addr_slave)
                self.usb_hardware.register_read_prepare()
                value = self.usb_hardware.ch341a_i2c_read(register_addrs_list[7])
                if value | 0x7f == 0xff:
                    self.usb_hardware.register_write_prepare()
                    value &= 0x7f
                    self.usb_hardware.ch341a_i2c_write(register_addrs_list[7], value)
                self.usb_hardware = CH341AI2CReadWrite(i2c_addr)
                time.sleep(0.003)

            self.chip_power_off_action()  # 执行关机命令
            while True:
                time.sleep(0.1)
                if not self.ui_power_on_queue.empty():
                    self.ui_power_on_queue.get()
                    # self.restart = True
                    return 'no_chip'
        finally:
            _lock.release()

    def state_connect_success(self):
        self.state_signal.emit('芯片已连接...')
        _lock.acquire()
        try:
            if self.chip_first_connect:  # 第一次连接写入版本信息等
                print('chip1 first connected, load OTP')
                self.usb_hardware.otp_load()  # 载入OTP保险丝数据
                otp_data = dict()
                self.usb_hardware.register_read_prepare()
                for addr in MyUSB.register_addrs:
                    time.sleep(self.delay_time)
                    value = self.usb_hardware.ch341a_i2c_read(addr)
                    self.signal.emit([addr, value])
                    otp_data[addr] = value
                if otp_data[MyUSB.register_addrs[3]] >= 0x80:
                    self.otp_burn_times_signal.emit(0)
                elif otp_data[MyUSB.register_addrs[1]] >= 0x80:
                    self.otp_burn_times_signal.emit(1)
                elif otp_data[MyUSB.register_addrs[12]] > 0x80 or otp_data[MyUSB.register_addrs[13]] > 0x80:
                    self.otp_burn_times_signal.emit(2)
                else:
                    self.otp_burn_times_signal.emit(3)
                    if otp_data[MyUSB.register_addrs[12]] == 0x00 or otp_data[MyUSB.register_addrs[13]] == 0x00:
                        self.usb_hardware.init_registers()
                self.chip_first_connect = False

            if self.chip_detect_flag:
                for addr in MyUSB.register_addrs:
                    self.usb_hardware.register_read_prepare()
                    value = self.usb_hardware.ch341a_i2c_read(addr)  # 读取芯片寄存器value
                    self.signal.emit([addr, value])  # 根据读取值更改软件界面

                    while not self.ui_changed_queue.empty():
                        data = self.ui_changed_queue.get()
                        self.usb_hardware.register_write_prepare()
                        self.usb_hardware.ch341a_i2c_write(data[0], data[1])

                if not self.usb_hardware.check_chip_connect():
                    return 'no_chip'
            else:
                while not self.ui_changed_queue.empty():
                    data = self.ui_changed_queue.get()
                    self.usb_hardware.register_write_prepare()
                    self.usb_hardware.ch341a_i2c_write(data[0], data[1])

            if not self.ui_registers_init_queue.empty():
                self.ui_registers_init_queue.get()
                self.usb_hardware.init_registers()

            if not self.ui_load_queue.empty():
                self.ui_load_queue.get()
                return 'load'

            if not self.ui_burn_queue.empty():
                self.ui_burn_queue.get()
                return 'burn'

            if not self.ui_power_off_queue.empty():  # 主芯片在芯片连接成功状态检测UI power off信号
                self.ui_power_off_queue.get()
                return 'power_off'

            return 'connect_success'

        except Exception as e:
            print('state_connect_success错误：' + str(e))
            return 'no_chip'
        finally:
            time.sleep(0.0006)
            _lock.release()

    def run(self):
        while self.state != 'exit':
            self.state = getattr(self, 'state_' + self.state)()

    def chip_power_off_action(self):
        lib.USBIO_SetOutput(0, 0b10000, 0, 0)
        time.sleep(0.5)
        lib.USBIO_SetOutput(0, 0b10000, 0, 0b11000000000000000000)
        time.sleep(2.6)


class MyUSBSlave(QtCore.QObject):
    """master芯片及USB连接检测及读写控制类"""
    num = 3
    delay_time = 0.001
    register_addrs = register_addrs_list
    signal = QtCore.pyqtSignal(list)  # 读取到的寄存器值
    state_signal = QtCore.pyqtSignal(str)
    otp_burn_times_signal = QtCore.pyqtSignal(int)
    otp_burn_state_signal = QtCore.pyqtSignal(str)
    ui_changed_queue = Queue(maxsize=1000)
    ui_load_queue = Queue(maxsize=1000)
    ui_burn_queue = Queue(maxsize=1000)
    ui_registers_init_queue = Queue(maxsize=1000)
    ui_power_off_queue = Queue(maxsize=1000)
    ui_power_on_queue = Queue(maxsize=1000)

    def __init__(self):
        super(MyUSBSlave, self).__init__()
        self.state = 'no_usb'
        self.chip_first_connect = True
        self.restart = False
        self.ui_changed = []
        self.tr_flag = False
        self.usb_connected = False
        self.chip_detect_flag = True
        self.usb_hardware = CH341AI2CReadWrite(i2c_addr_slave)

    def usb_connect_state_slot(self, e):
        if e:
            self.usb_connected = True
            print('USB连接')
        else:
            self.usb_connected = False
            print('USB未连接')

    def ui_changed_slot(self, data):
        self.ui_changed_queue.put(data)

    def ui_load_slot(self):
        self.ui_load_queue.put(True)

    def ui_burn_slot(self):
        self.ui_burn_queue.put(True)

    def ui_registers_init_slot(self):
        self.ui_registers_init_queue.put(True)

    def ui_pause_slot(self, e):
        if e:
            self.chip_detect_flag = False
        else:
            self.chip_detect_flag = True

    # state
    def state_no_usb(self):
        # print('检测USB中...')
        _lock.acquire()
        try:
            if self.usb_connected:
                return 'no_chip'
            else:
                self.state_signal.emit('USB未连接...')
                time.sleep(0.2)
                return 'no_usb'
        finally:
            _lock.release()

    def state_no_chip(self):
        _lock.acquire()
        try:
            if self.usb_connected and self.chip_detect_flag:
                if self.usb_hardware.check_chip_connect():
                    self.usb_hardware.ch341a_i2c_write(power_addr, 0xe9)
                    self.chip_first_connect = True
                    return 'connect_success'
                else:
                    self.state_signal.emit('USB已连接,检测芯片中...')
                    time.sleep(self.delay_time)
                    return 'no_chip'
            else:
                return 'no_usb'
        finally:
            _lock.release()

    def state_load(self):
        _lock.acquire()
        try:
            print('slave get load signal, start load')
            self.usb_hardware.otp_load()
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
            self.usb_hardware.otp_burn()
            self.otp_burn_state_signal.emit('烧录成功')
            self.chip_first_connect = True
            return 'connect_success'
        except Exception as e:
            print('burn fail:' + str(e))
            self.otp_burn_state_signal.emit('烧录失败:' + '\n' + str(e))
            return 'no_chip'
        finally:
            _lock.release()

    def state_power_off(self):
        print('enter power off')
        state = self.ui_power_off_queue.get()
        _lock.acquire()
        try:
            # 防止芯片被设置为slide模式
            self.usb_hardware.register_read_prepare()
            value = self.usb_hardware.ch341a_i2c_read(register_addrs_list[7])
            if value | 0x7f == 0xff:
                self.usb_hardware.register_write_prepare()
                value &= 0x7f
                self.usb_hardware.ch341a_i2c_write(register_addrs_list[7], value)
            if state == '双芯片模式':
                time.sleep(0.003)
                self.usb_hardware = CH341AI2CReadWrite(i2c_addr_slave)
                self.usb_hardware.register_read_prepare()
                value = self.usb_hardware.ch341a_i2c_read(register_addrs_list[7])
                if value | 0x7f == 0xff:
                    self.usb_hardware.register_write_prepare()
                    value &= 0x7f
                    self.usb_hardware.ch341a_i2c_write(register_addrs_list[7], value)
                self.usb_hardware = CH341AI2CReadWrite(i2c_addr)
                time.sleep(0.003)

            self.chip_power_off_action()  # 执行关机命令
            while True:
                time.sleep(0.1)
                if not self.ui_power_on_queue.empty():
                    self.ui_power_on_queue.get()
                    return 'no_chip'
        finally:
            _lock.release()

    def state_connect_success(self):
        self.state_signal.emit('slave芯片已连接...')
        _lock.acquire()
        try:
            if self.chip_first_connect:  # 第一次连接写入版本信息等
                print('chip2 first connected, load OTP')
                self.usb_hardware.otp_load()  # 载入OTP保险丝数据
                otp_data = dict()
                self.usb_hardware.register_read_prepare()
                for addr in MyUSB.register_addrs:
                    time.sleep(self.delay_time)
                    value = self.usb_hardware.ch341a_i2c_read(addr)
                    otp_data[addr] = value
                if otp_data[MyUSB.register_addrs[3]] >= 0x80:
                    self.otp_burn_times_signal.emit(0)
                elif otp_data[MyUSB.register_addrs[1]] >= 0x80:
                    self.otp_burn_times_signal.emit(1)
                elif otp_data[MyUSB.register_addrs[12]] > 0x80 or otp_data[MyUSB.register_addrs[13]] > 0x80:
                    self.otp_burn_times_signal.emit(2)
                else:
                    self.otp_burn_times_signal.emit(3)
                    if otp_data[MyUSB.register_addrs[12]] == 0x00 or otp_data[MyUSB.register_addrs[13]] == 0x00:
                        self.usb_hardware.init_registers()
                self.chip_first_connect = False

            if self.chip_detect_flag:
                for addr in MyUSB.register_addrs:
                    self.usb_hardware.register_read_prepare()
                    value = self.usb_hardware.ch341a_i2c_read(addr)  # 读取芯片寄存器value
                    self.signal.emit([addr, value])  # 根据读取值更改软件界面

                    while not self.ui_changed_queue.empty():
                        data = self.ui_changed_queue.get()
                        self.usb_hardware.register_write_prepare()
                        self.usb_hardware.ch341a_i2c_write(data[0], data[1])

                if not self.usb_hardware.check_chip_connect():
                    return 'no_chip'
            else:
                while not self.ui_changed_queue.empty():
                    data = self.ui_changed_queue.get()
                    self.usb_hardware.register_write_prepare()
                    self.usb_hardware.ch341a_i2c_write(data[0], data[1])

            if not self.ui_registers_init_queue.empty():
                self.ui_registers_init_queue.get()
                self.usb_hardware.init_registers()

            if not self.ui_load_queue.empty():
                self.ui_load_queue.get()
                return 'load'

            if not self.ui_burn_queue.empty():
                self.ui_burn_queue.get()
                return 'burn'

            if not self.ui_power_off_queue.empty():  # 主芯片在芯片连接成功状态检测UI power off信号
                self.ui_power_off_queue.get()
                return 'power_off'

            return 'connect_success'

        except Exception as e:
            print('state_connect_success错误：' + str(e))
            return 'no_chip'
        finally:
            time.sleep(0.0006)
            _lock.release()

    def run(self):
        while self.state != 'exit':
            self.state = getattr(self, 'state_' + self.state)()

    def chip_power_off_action(self):
        lib.USBIO_SetOutput(0, 0b10000, 0, 0)
        time.sleep(0.5)
        lib.USBIO_SetOutput(0, 0b10000, 0, 0b11000000000000000000)
        time.sleep(2.6)


if __name__ == '__main__':
    usb1 = MyUSB()
    usb1.run()
