#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/10/14 10:28
import os
import sys
import time
import threading
import ctypes
import numpy as np
from PyQt5 import QtWidgets
from hid_ui import Ui_MainWindow

so = ctypes.windll.LoadLibrary
path = os.path.join(os.getcwd(), 'USB_I2C', 'USBIOX.DLL')
lib = so(path)

lib.USBIO_OpenDevice(0)


class MyCH341AIO(object):
    #  CH341A操作命令码
    mCH341_PACKET_LENGTH = 32  # 输入数据最大位数
    mCH341A_CMD_I2C_STREAM = 0xAA  # i2c命令码
    mCH341A_CMD_I2C_STM_STA = 0x74  # 起始位
    mCH341A_CMD_I2C_STM_STO = 0x75  # 停止位
    mCH341A_CMD_I2C_STM_OUT = 0x80  # 输出数据,位5-位0为长度,后续字节为数据,0长度则只发送一个字节并返回应答
    mCH341A_CMD_I2C_STM_IN = 0xC0  # 输入数据,位5-位0为长度,0长度则只接收一个字节并发送无应答
    mCH341A_CMD_I2C_STM_END = 0x00  # 命令包结束
    mCH341A_CMD_I2C_STM_MS = 0x50 | 1  # 以亳秒为单位延时,位3-位0为延时值

    # VA6610操作命令码
    VA6610_I2C_WRITE_ADDRS = 0x8e  # master 8 Bit write address
    VA6610_I2C_READ_ADDRS = 0x8f  # master 8 Bit read address

    def i2c_write_register_prepare(self):
        """控制0x3f寄存器为写入状态"""
        return self.i2c_write_register(0x3f, 0x02)

    def i2c_read_register_prepare(self):
        """控制0x3f寄存器为写入状态"""
        return self.i2c_write_register(0x3f, 0x00)

    def i2c_write_register(self, addr, value):
        """写入一个数据"""
        data = ctypes.create_string_buffer(self.mCH341_PACKET_LENGTH)
        data[0] = self.mCH341A_CMD_I2C_STREAM
        data[1] = self.mCH341A_CMD_I2C_STM_STA
        data[2] = self.mCH341A_CMD_I2C_STM_OUT | 3
        data[3] = self.VA6610_I2C_WRITE_ADDRS
        data[4] = addr
        data[5] = value
        data[6] = self.mCH341A_CMD_I2C_STM_STO
        data[7] = self.mCH341A_CMD_I2C_STM_MS
        data[8] = self.mCH341A_CMD_I2C_STM_END


        length = ctypes.create_string_buffer(1)
        length[0] = 9
        return lib.USBIO_WriteData(0, data, length)

    def i2c_read_register(self, addr):
        data = ctypes.create_string_buffer(self.mCH341_PACKET_LENGTH)
        data[0] = self.mCH341A_CMD_I2C_STREAM
        data[1] = self.mCH341A_CMD_I2C_STM_STA
        data[2] = self.mCH341A_CMD_I2C_STM_OUT | 2
        data[3] = self.VA6610_I2C_WRITE_ADDRS
        data[4] = addr
        data[5] = self.mCH341A_CMD_I2C_STM_STA
        data[6] = self.mCH341A_CMD_I2C_STM_OUT | 1
        data[7] = self.VA6610_I2C_READ_ADDRS
        data[8] = self.mCH341A_CMD_I2C_STM_IN | 1
        data[9] = self.mCH341A_CMD_I2C_STM_STO
        data[10] = self.mCH341A_CMD_I2C_STM_MS
        data[11] = self.mCH341A_CMD_I2C_STM_END

        length = ctypes.create_string_buffer(1)
        result = ctypes.create_string_buffer(1)

        if lib.USBIO_WriteRead(0, 12, data, 1, 1, length, result):
            return int(result[0].hex(), 16)
        else:
            return False

    def i2c_sequential_read_registers(self, addr, times):
        """从addr开始，连续读取times个寄存器值"""
        data = ctypes.create_string_buffer(self.mCH341_PACKET_LENGTH)
        data[0] = self.mCH341A_CMD_I2C_STREAM
        data[1] = self.mCH341A_CMD_I2C_STM_STA
        data[2] = self.mCH341A_CMD_I2C_STM_OUT | 2
        data[3] = self.VA6610_I2C_WRITE_ADDRS
        data[4] = addr
        data[5] = self.mCH341A_CMD_I2C_STM_STA
        data[6] = self.mCH341A_CMD_I2C_STM_OUT | 1
        data[7] = self.VA6610_I2C_READ_ADDRS
        data[8] = self.mCH341A_CMD_I2C_STM_IN | times
        data[9] = self.mCH341A_CMD_I2C_STM_STO
        data[10] = self.mCH341A_CMD_I2C_STM_MS
        data[11] = self.mCH341A_CMD_I2C_STM_END

        length = ctypes.create_string_buffer(1)
        result = ctypes.create_string_buffer(times)

        if lib.USBIO_WriteRead(0, 12, data, times, 1, length, result):
            return result
        else:
            return False


if __name__ == '__main__':
    usb = MyCH341AIO()
    usb.i2c_write_register(0x20, 0xe9)
    usb.i2c_write_register_prepare()
    usb.i2c_write_register(0x11, 0x84)
    usb.i2c_read_register_prepare()
    a = usb.i2c_read_register(0x11)
    print(hex(a))
    b = usb.i2c_sequential_read_registers(0x10, 6)
    print(b.raw)

