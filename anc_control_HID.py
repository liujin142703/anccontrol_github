#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/3/15 14:54
import sys
import threading
import time
import functools
from PyQt5 import QtWidgets, QtGui, QtCore
import xml.etree.ElementTree as ET

from filter_designer import FilterDesignerWindow
from register import registers_main, row_data
from usb_connect import MyHID, HIDSlave, lib

# 寄存器地址跟data行数对应表
map_addr2row = {0x10: 0, 0x11: 1, 0x12: 2, 0x13: 3, 0x14: 4, 0x15: 5, 0x16: 6, 0x17: 7,
                0x20: 8, 0x21: 9, 0x30: 10, 0x31: 11, 0x32: 12, 0x33: 13, 0x34: 14, 0x35: 15,
                0x3d: 16, 0x3e: 17, 0x3f: 18}


# 写入寄存器装饰器
def change_register(addr: int):
    """
    软件界面寄存器参数变化之后执行装饰器函数
    通过寄存器地址addr获得对应value，调用写入工具api进行芯片参数更改
    :param addr: 寄存器地址对应的行数，参照register表格
    :return: none
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            a = func(self, *args, **kwargs)
            value = self.registers_map[map_addr2row[addr]].hex_value()
            print('get register data: ' + str(hex(addr)) + ' -> ' + value)
            value = self.registers_map[map_addr2row[addr]].dec_value()
            self.write_registers([addr, int(value)])
            return a

        return wrapper

    return decorator


class AncControlWindow(FilterDesignerWindow):
    ui_changed_signal = QtCore.pyqtSignal(list)
    ui_load_signal = QtCore.pyqtSignal(bool)
    ui_burn_signal = QtCore.pyqtSignal(bool)
    ui_changed_signal_slave = QtCore.pyqtSignal(list)
    ui_load_signal_slave = QtCore.pyqtSignal(bool)
    ui_burn_signal_slave = QtCore.pyqtSignal(bool)
    usb_connected_signal = QtCore.pyqtSignal(bool)

    def __init__(self):
        super(AncControlWindow, self).__init__()
        self.setWindowTitle('ANC_control V1.0')
        self.usb = MyHID()
        self.usb_slave = HIDSlave()
        self.usb_state = 'USB未连接...'
        self.usb_slave_state = 'USB未连接...'
        self.chip_burn_times = 3
        self.chip_slave_burn_times = 3
        self.usb_run_state = True
        self.control_signals_slots()
        self.set_default_registers()
        self.usb_thread_run()

        # self.cmp_func = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_int)(self.py_cmp_func)
        # self.usb_c = lib.USBIO_SetDeviceNotify  # USB检测回调函数库
        # self.usb_c(0, 0, self.cmp_func)  # 设置USB拔插回调函数
        # self.init_usb()

    def set_default_registers(self):
        row00 = row_data.RowData(True, True, False, False, False, False, False, False)
        row01 = row_data.RowData(False, True, False, False, False, False, False, False)
        row02 = row_data.RowData(True, False, False, False, False, False, False, False)
        row03 = row_data.RowData(False, False, False, False, False, False, False, False)
        row04 = row_data.RowData(False, False, False, False, False, False, False, False)
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
        self.registers_map = [row00, row01, row02, row03, row04, row05, row06, row07, row08, row09, row10,
                              row11, row12, row13, row14, row15, row16, row17, row18]

    def control_signals_slots(self):
        self.btn_set_registers.clicked.connect(self.registers_map_dialog)  # registers map 按键
        self.pushbutton_save_registers.clicked.connect(self.save_registers)  # 保存 registers
        self.pushbutton_import_registers.clicked.connect(self.import_registers)  # 导入registers
        self.pushbutton_reset_registers.clicked.connect(self.reset_registers)  # 重置registers

        self.ui_changed_signal.connect(self.usb.ui_changed_slot)
        self.ui_changed_signal_slave.connect(self.usb_slave.ui_changed_slot)
        self.usb.signal.connect(self.read_registers_to_ui)  # 寄存器读取数值后更新UI
        self.usb.state_signal.connect(self.show_usb_connect_state)  # 连接状态提示
        self.usb_slave.signal.connect(self.read_registers_to_ui_slave)  # 寄存器读取数值后更新UI
        self.usb_slave.state_signal.connect(self.set_usb_slave_state)  # 连接状态提示

        self.usb.otp_burn_times_signal.connect(self.burn_times_slot)
        self.usb_slave.otp_burn_times_signal.connect(self.burn_times_slot)
        self.usb.otp_burn_state_signal.connect(self.burn_state_message)
        self.usb_slave.otp_burn_state_signal.connect(self.burn_state_message)

        self.pushbutton_load_registers.clicked.connect(self.load_registers)  # registers load
        self.pushbutton_burn_registers.clicked.connect(self.burn_registers)  # registers burn
        self.ui_load_signal.connect(self.usb.ui_load_slot)
        self.ui_burn_signal.connect(self.usb.ui_burn_slot)
        self.ui_load_signal_slave.connect(self.usb_slave.ui_load_slot)
        self.ui_burn_signal_slave.connect(self.usb_slave.ui_burn_slot)

        self.radiobutton_power_off.toggled.connect(self.set_registers_data_eval)  # EVAL
        self.radiobutton_anc.toggled.connect(self.set_registers_data_eval)
        self.radiobutton_monitor.toggled.connect(self.set_registers_data_eval)
        self.radiobutton_pbo.toggled.connect(self.set_registers_data_eval)
        self.checkbox_mute_l.toggled.connect(self.set_registers_data_eval)
        self.checkbox_mute_r.toggled.connect(self.set_registers_data_eval)

        self.radiobutton_hph_l_off.toggled.connect(self.set_registers_data_hph_l)  # zgmicro registers
        self.radiobutton_hph_l_on.toggled.connect(self.set_registers_data_hph_l)
        self.radiobutton_line_in_stereo.toggled.connect(self.set_registers_data_line_in)
        self.radiobutton_line_in_mono.toggled.connect(self.set_registers_data_line_in)

        self.combo_mic_gain_l.currentIndexChanged.connect(self.mic_gain_addrs_chose_l)  # ANC L
        self.combo_mic_gain_r.currentIndexChanged.connect(self.mic_gain_addrs_chose_r)  # ANC R
        self.combo_mic_gain_l_2.currentIndexChanged.connect(self.set_registers_data_mic_mon_l)  # MIC_MON_L
        self.combo_mic_gain_r_2.currentIndexChanged.connect(self.set_registers_data_mic_mon_r)  # MIC_MON_R

        self.checkbox_mic_charge_pump.toggled.connect(self.set_registers_data_mode_1)  # mode_1
        self.checkbox_mic_mics.toggled.connect(self.set_registers_data_mode_1)
        self.checkbox_mic_agc.toggled.connect(self.set_registers_data_mode_1)
        self.checkbox_mic_power.toggled.connect(self.set_registers_data_mode_1)
        self.checkbox_other_low_battery_shutdown.toggled.connect(self.set_registers_data_mode_1)
        self.checkbox_other_close_vneg.toggled.connect(self.set_registers_data_mode_1)
        self.checkbox_hph_power.toggled.connect(self.set_registers_data_mode_1)
        self.checkbox_line_power.toggled.connect(self.set_registers_data_mode_1)

        self.checkbox_line_difference.toggled.connect(self.set_registers_data_mode_2)  # mode_2
        self.checkbox_other_mic_supply.toggled.connect(self.set_registers_data_mode_2)
        self.checkbox_other_hph_delay.toggled.connect(self.set_registers_data_mode_2)
        self.radiobutton_hph_difference.toggled.connect(self.set_registers_data_mode_2)

        self.radiobutton_none.toggled.connect(self.set_registers_data_anc_mode)  # ANC MODE
        self.radiobutton_mic.toggled.connect(self.set_registers_data_anc_mode)
        self.radiobutton_op1.toggled.connect(self.set_registers_data_anc_mode)
        self.radiobutton_op2.toggled.connect(self.set_registers_data_anc_mode)
        self.checkbox_mute_line_in.toggled.connect(self.set_registers_data_anc_mode)
        self.checkbox_mute_mix.toggled.connect(self.set_registers_data_anc_mode)
        self.checkbox_op_l2.toggled.connect(self.set_registers_data_anc_mode)
        self.checkbox_op_r2.toggled.connect(self.set_registers_data_anc_mode)
        self.checkbox_op_l1.toggled.connect(self.set_registers_data_anc_mode)
        self.checkbox_op_r1.toggled.connect(self.set_registers_data_anc_mode)

        self.radiobutton_none_2.toggled.connect(self.set_registers_data_monitor_mode)  # monitor MODE
        self.radiobutton_mic_2.toggled.connect(self.set_registers_data_monitor_mode)
        self.radiobutton_op1_2.toggled.connect(self.set_registers_data_monitor_mode)
        self.radiobutton_op2_2.toggled.connect(self.set_registers_data_monitor_mode)
        self.checkbox_mute_line_in_2.toggled.connect(self.set_registers_data_monitor_mode)
        self.checkbox_mute_mix_2.toggled.connect(self.set_registers_data_monitor_mode)
        self.combo_line_gain.currentIndexChanged.connect(self.set_registers_data_monitor_mode)
        self.combo_monitor_slide.currentIndexChanged.connect(self.set_registers_data_monitor_mode)
        self.radiobutton_monitor_on.toggled.connect(self.set_registers_data_monitor_mode)
        self.radiobutton_monitor_off.toggled.connect(self.set_registers_data_monitor_mode)

        self.radiobutton_pbo_on.toggled.connect(self.set_registers_data_pbo_mode)  # PBO MODE
        self.radiobutton_pbo_off.toggled.connect(self.set_registers_data_pbo_mode)
        self.checkbox_mute_line_in_5.toggled.connect(self.set_registers_data_pbo_mode)
        self.checkbox_mute_mix_5.toggled.connect(self.set_registers_data_pbo_mode)
        self.checkbox_op_l2_5.toggled.connect(self.set_registers_data_pbo_mode)
        self.checkbox_op_r2_5.toggled.connect(self.set_registers_data_pbo_mode)
        self.checkbox_op_l1_5.toggled.connect(self.set_registers_data_pbo_mode)
        self.checkbox_op_r1_5.toggled.connect(self.set_registers_data_pbo_mode)

        self.combo_power_slide.currentIndexChanged.connect(self.set_registers_data_eco)  # ECO
        self.checkbox_other_low_battery.toggled.connect(self.set_registers_data_eco)
        self.radiobutton_led_0.toggled.connect(self.set_registers_data_eco)
        self.radiobutton_led_25.toggled.connect(self.set_registers_data_eco)
        self.radiobutton_led_50.toggled.connect(self.set_registers_data_eco)
        self.radiobutton_led_100.toggled.connect(self.set_registers_data_eco)
        self.checkbox_hph_eco.toggled.connect(self.set_registers_data_eco)
        self.checkbox_mic_eco.toggled.connect(self.set_registers_data_eco)
        self.checkbox_line_eco.toggled.connect(self.set_registers_data_eco)
        self.checkbox_op_eco.toggled.connect(self.set_registers_data_eco)

    def signals_slot_connect_control(self, state=True):
        if state:
            self.radiobutton_power_off.toggled.connect(self.set_registers_data_eval)  # EVAL
            self.radiobutton_anc.toggled.connect(self.set_registers_data_eval)
            self.radiobutton_monitor.toggled.connect(self.set_registers_data_eval)
            self.radiobutton_pbo.toggled.connect(self.set_registers_data_eval)
            self.checkbox_mute_l.toggled.connect(self.set_registers_data_eval)
            self.checkbox_mute_r.toggled.connect(self.set_registers_data_eval)

            self.radiobutton_hph_l_off.toggled.connect(self.set_registers_data_hph_l)  # zgmicro registers
            self.radiobutton_hph_l_on.toggled.connect(self.set_registers_data_hph_l)
            self.radiobutton_line_in_stereo.toggled.connect(self.set_registers_data_line_in)
            self.radiobutton_line_in_mono.toggled.connect(self.set_registers_data_line_in)

            self.combo_mic_gain_l.currentIndexChanged.connect(self.mic_gain_addrs_chose_l)  # ANC L
            self.combo_mic_gain_r.currentIndexChanged.connect(self.mic_gain_addrs_chose_r)  # ANC R
            self.combo_mic_gain_l_2.currentIndexChanged.connect(self.set_registers_data_mic_mon_l)  # MIC_MON_L
            self.combo_mic_gain_r_2.currentIndexChanged.connect(self.set_registers_data_mic_mon_r)  # MIC_MON_R

            self.checkbox_mic_charge_pump.toggled.connect(self.set_registers_data_mode_1)  # mode_1
            self.checkbox_mic_mics.toggled.connect(self.set_registers_data_mode_1)
            self.checkbox_mic_agc.toggled.connect(self.set_registers_data_mode_1)
            self.checkbox_mic_power.toggled.connect(self.set_registers_data_mode_1)
            self.checkbox_other_low_battery_shutdown.toggled.connect(self.set_registers_data_mode_1)
            self.checkbox_other_close_vneg.toggled.connect(self.set_registers_data_mode_1)
            self.checkbox_hph_power.toggled.connect(self.set_registers_data_mode_1)
            self.checkbox_line_power.toggled.connect(self.set_registers_data_mode_1)

            self.checkbox_line_difference.toggled.connect(self.set_registers_data_mode_2)  # mode_2
            self.checkbox_other_mic_supply.toggled.connect(self.set_registers_data_mode_2)
            self.checkbox_other_hph_delay.toggled.connect(self.set_registers_data_mode_2)
            self.radiobutton_hph_difference.toggled.connect(self.set_registers_data_mode_2)

            self.radiobutton_none.toggled.connect(self.set_registers_data_anc_mode)  # ANC MODE
            self.radiobutton_mic.toggled.connect(self.set_registers_data_anc_mode)
            self.radiobutton_op1.toggled.connect(self.set_registers_data_anc_mode)
            self.radiobutton_op2.toggled.connect(self.set_registers_data_anc_mode)
            self.checkbox_mute_line_in.toggled.connect(self.set_registers_data_anc_mode)
            self.checkbox_mute_mix.toggled.connect(self.set_registers_data_anc_mode)
            self.checkbox_op_l2.toggled.connect(self.set_registers_data_anc_mode)
            self.checkbox_op_r2.toggled.connect(self.set_registers_data_anc_mode)
            self.checkbox_op_l1.toggled.connect(self.set_registers_data_anc_mode)
            self.checkbox_op_r1.toggled.connect(self.set_registers_data_anc_mode)

            self.radiobutton_none_2.toggled.connect(self.set_registers_data_monitor_mode)  # monitor MODE
            self.radiobutton_mic_2.toggled.connect(self.set_registers_data_monitor_mode)
            self.radiobutton_op1_2.toggled.connect(self.set_registers_data_monitor_mode)
            self.radiobutton_op2_2.toggled.connect(self.set_registers_data_monitor_mode)
            self.checkbox_mute_line_in_2.toggled.connect(self.set_registers_data_monitor_mode)
            self.checkbox_mute_mix_2.toggled.connect(self.set_registers_data_monitor_mode)
            self.combo_line_gain.currentIndexChanged.connect(self.set_registers_data_monitor_mode)
            self.combo_monitor_slide.currentIndexChanged.connect(self.set_registers_data_monitor_mode)
            self.radiobutton_monitor_on.toggled.connect(self.set_registers_data_monitor_mode)
            self.radiobutton_monitor_off.toggled.connect(self.set_registers_data_monitor_mode)

            self.radiobutton_pbo_on.toggled.connect(self.set_registers_data_pbo_mode)  # PBO MODE
            self.radiobutton_pbo_off.toggled.connect(self.set_registers_data_pbo_mode)
            self.checkbox_mute_line_in_5.toggled.connect(self.set_registers_data_pbo_mode)
            self.checkbox_mute_mix_5.toggled.connect(self.set_registers_data_pbo_mode)
            self.checkbox_op_l2_5.toggled.connect(self.set_registers_data_pbo_mode)
            self.checkbox_op_r2_5.toggled.connect(self.set_registers_data_pbo_mode)
            self.checkbox_op_l1_5.toggled.connect(self.set_registers_data_pbo_mode)
            self.checkbox_op_r1_5.toggled.connect(self.set_registers_data_pbo_mode)

            self.combo_power_slide.currentIndexChanged.connect(self.set_registers_data_eco)  # ECO
            self.checkbox_other_low_battery.toggled.connect(self.set_registers_data_eco)
            self.radiobutton_led_0.toggled.connect(self.set_registers_data_eco)
            self.radiobutton_led_25.toggled.connect(self.set_registers_data_eco)
            self.radiobutton_led_50.toggled.connect(self.set_registers_data_eco)
            self.radiobutton_led_100.toggled.connect(self.set_registers_data_eco)
            self.checkbox_hph_eco.toggled.connect(self.set_registers_data_eco)
            self.checkbox_mic_eco.toggled.connect(self.set_registers_data_eco)
            self.checkbox_line_eco.toggled.connect(self.set_registers_data_eco)
            self.checkbox_op_eco.toggled.connect(self.set_registers_data_eco)
        else:
            self.radiobutton_power_off.toggled.disconnect(self.set_registers_data_eval)  # EVAL
            self.radiobutton_anc.toggled.disconnect(self.set_registers_data_eval)
            self.radiobutton_monitor.toggled.disconnect(self.set_registers_data_eval)
            self.radiobutton_pbo.toggled.disconnect(self.set_registers_data_eval)
            self.checkbox_mute_l.toggled.disconnect(self.set_registers_data_eval)
            self.checkbox_mute_r.toggled.disconnect(self.set_registers_data_eval)

            self.radiobutton_hph_l_off.toggled.disconnect(self.set_registers_data_hph_l)  # zgmicro registers
            self.radiobutton_hph_l_on.toggled.disconnect(self.set_registers_data_hph_l)
            self.radiobutton_line_in_stereo.toggled.disconnect(self.set_registers_data_line_in)
            self.radiobutton_line_in_mono.toggled.disconnect(self.set_registers_data_line_in)

            self.combo_mic_gain_l.currentIndexChanged.disconnect(self.mic_gain_addrs_chose_l)  # ANC L
            self.combo_mic_gain_r.currentIndexChanged.disconnect(self.mic_gain_addrs_chose_r)  # ANC R
            self.combo_mic_gain_l_2.currentIndexChanged.disconnect(self.set_registers_data_mic_mon_l)  # MIC_MON_L
            self.combo_mic_gain_r_2.currentIndexChanged.disconnect(self.set_registers_data_mic_mon_r)  # MIC_MON_R

            self.checkbox_mic_charge_pump.toggled.disconnect(self.set_registers_data_mode_1)  # mode_1
            self.checkbox_mic_mics.toggled.disconnect(self.set_registers_data_mode_1)
            self.checkbox_mic_agc.toggled.disconnect(self.set_registers_data_mode_1)
            self.checkbox_mic_power.toggled.disconnect(self.set_registers_data_mode_1)
            self.checkbox_other_low_battery_shutdown.toggled.disconnect(self.set_registers_data_mode_1)
            self.checkbox_other_close_vneg.toggled.disconnect(self.set_registers_data_mode_1)
            self.checkbox_hph_power.toggled.disconnect(self.set_registers_data_mode_1)
            self.checkbox_line_power.toggled.disconnect(self.set_registers_data_mode_1)

            self.checkbox_line_difference.toggled.disconnect(self.set_registers_data_mode_2)  # mode_2
            self.checkbox_other_mic_supply.toggled.disconnect(self.set_registers_data_mode_2)
            self.checkbox_other_hph_delay.toggled.disconnect(self.set_registers_data_mode_2)
            self.radiobutton_hph_difference.toggled.disconnect(self.set_registers_data_mode_2)

            self.radiobutton_none.toggled.disconnect(self.set_registers_data_anc_mode)  # ANC MODE
            self.radiobutton_mic.toggled.disconnect(self.set_registers_data_anc_mode)
            self.radiobutton_op1.toggled.disconnect(self.set_registers_data_anc_mode)
            self.radiobutton_op2.toggled.disconnect(self.set_registers_data_anc_mode)
            self.checkbox_mute_line_in.toggled.disconnect(self.set_registers_data_anc_mode)
            self.checkbox_mute_mix.toggled.disconnect(self.set_registers_data_anc_mode)
            self.checkbox_op_l2.toggled.disconnect(self.set_registers_data_anc_mode)
            self.checkbox_op_r2.toggled.disconnect(self.set_registers_data_anc_mode)
            self.checkbox_op_l1.toggled.disconnect(self.set_registers_data_anc_mode)
            self.checkbox_op_r1.toggled.disconnect(self.set_registers_data_anc_mode)

            self.radiobutton_none_2.toggled.disconnect(self.set_registers_data_monitor_mode)  # monitor MODE
            self.radiobutton_mic_2.toggled.disconnect(self.set_registers_data_monitor_mode)
            self.radiobutton_op1_2.toggled.disconnect(self.set_registers_data_monitor_mode)
            self.radiobutton_op2_2.toggled.disconnect(self.set_registers_data_monitor_mode)
            self.checkbox_mute_line_in_2.toggled.disconnect(self.set_registers_data_monitor_mode)
            self.checkbox_mute_mix_2.toggled.disconnect(self.set_registers_data_monitor_mode)
            self.combo_line_gain.currentIndexChanged.disconnect(self.set_registers_data_monitor_mode)
            self.combo_monitor_slide.currentIndexChanged.disconnect(self.set_registers_data_monitor_mode)
            self.radiobutton_monitor_on.toggled.disconnect(self.set_registers_data_monitor_mode)
            self.radiobutton_monitor_off.toggled.disconnect(self.set_registers_data_monitor_mode)

            self.radiobutton_pbo_on.toggled.disconnect(self.set_registers_data_pbo_mode)  # PBO MODE
            self.radiobutton_pbo_off.toggled.disconnect(self.set_registers_data_pbo_mode)
            self.checkbox_mute_line_in_5.toggled.disconnect(self.set_registers_data_pbo_mode)
            self.checkbox_mute_mix_5.toggled.disconnect(self.set_registers_data_pbo_mode)
            self.checkbox_op_l2_5.toggled.disconnect(self.set_registers_data_pbo_mode)
            self.checkbox_op_r2_5.toggled.disconnect(self.set_registers_data_pbo_mode)
            self.checkbox_op_l1_5.toggled.disconnect(self.set_registers_data_pbo_mode)
            self.checkbox_op_r1_5.toggled.disconnect(self.set_registers_data_pbo_mode)

            self.combo_power_slide.currentIndexChanged.disconnect(self.set_registers_data_eco)  # ECO
            self.checkbox_other_low_battery.toggled.disconnect(self.set_registers_data_eco)
            self.radiobutton_led_0.toggled.disconnect(self.set_registers_data_eco)
            self.radiobutton_led_25.toggled.disconnect(self.set_registers_data_eco)
            self.radiobutton_led_50.toggled.disconnect(self.set_registers_data_eco)
            self.radiobutton_led_100.toggled.disconnect(self.set_registers_data_eco)
            self.checkbox_hph_eco.toggled.disconnect(self.set_registers_data_eco)
            self.checkbox_mic_eco.toggled.disconnect(self.set_registers_data_eco)
            self.checkbox_line_eco.toggled.disconnect(self.set_registers_data_eco)
            self.checkbox_op_eco.toggled.disconnect(self.set_registers_data_eco)

    # registers
    def usb_thread_run(self):
        t1 = threading.Thread(target=self.run_hid_usb)  # I2C接口读写线程
        t1.setDaemon(True)  # 守护线程，系统退出时自动退出该线程
        t1.start()

    def registers_map_dialog(self):
        """打开registers配置对话框并开始跟踪数据改变"""
        dialog = registers_main.RegisterWindow(self.registers_map)
        dialog.tableWidget.itemDoubleClicked.connect(self.registers_dialog_control)
        dialog.exec_()

    def registers_dialog_control(self, i):
        """双击registers_map对话框时，根据返回数据更新UI"""
        self.registers_map_to_ui()

    def set_usb_slave_state(self, state):
        self.usb_slave_state = state

        if self.usb_slave_state == 'slave芯片已连接...':
            self.combo_chip_chose.setEnabled(True)
            self.label_74.setText('双芯片模式')
        else:
            self.combo_chip_chose.setCurrentIndex(0)
            self.combo_chip_chose.setEnabled(False)
            self.label_74.setText('单芯片模式')

    def write_registers(self, data=None):
        """将registers_map数据写入OTP"""
        if self.combo_chip_chose.currentIndex() == 0:
            if self.usb_state == '芯片已连接...':
                self.ui_changed_signal.emit(data)
        elif self.combo_chip_chose.currentIndex() == 1:
            if self.usb_slave_state == 'slave芯片已连接...':
                self.ui_changed_signal_slave.emit(data)

    def read_registers_to_ui(self, data):
        """
        根据usb.signal信号调整UI界面状态显示
        :param data: list[addr, value]
        :return:
        """
        if self.combo_chip_chose.currentIndex() == 0:
            r = map_addr2row[data[0]]
            self.registers_map[r].value_to_bit(data[1])  # 更新registers map
            self.signals_slot_connect_control(False)
            self.registers_map_to_ui()
            self.signals_slot_connect_control(True)

    def read_registers_to_ui_slave(self, data):
        """
        根据usb.signal信号调整UI界面状态显示
        :param data: list[addr, value]
        :return:
        """
        if self.combo_chip_chose.currentIndex() == 1:
            r = map_addr2row[data[0]]
            self.registers_map[r].value_to_bit(data[1])  # 更新registers map
            self.signals_slot_connect_control(False)
            self.registers_map_to_ui()
            self.signals_slot_connect_control(True)

    # USB
    # def init_usb(self):
    #     a = lib.USBIO_OpenDevice(0)
    #     if a != (-1):
    #         lib.USBIO_SetStream(0, 0x80)
    #         self.usb_connected_signal.emit(True)
    #         self.show_usb_connect_state('USB已连接,检测芯片中...')
    #     else:
    #         self.usb_connected_signal.emit(False)
    #         self.show_usb_connect_state('USB未连接...')

    def show_usb_connect_state(self, state):
        self.usb_state = state
        self.statusbar.showMessage(state)
        if self.usb_state == 'USB已连接,检测芯片中...':
            self.tab_5.setEnabled(False)
        else:
            self.tab_5.setEnabled(True)

    def run_hid_usb(self):
        """usb读写线程，并在状态栏提示USB状态信息"""
        t1 = threading.Thread(target=self.usb.run)
        t2 = threading.Thread(target=self.usb_slave.run)
        t1.start()
        t2.start()
        while True:
            if not self.usb_run_state:
                break
            time.sleep(0.05)

    # register load
    def load_registers(self):
        if self.usb_state == '芯片已连接...':
            if self.combo_chip_chose.currentIndex() == 0:
                self.ui_load_signal.emit(True)
            else:
                self.ui_load_signal_slave.emit(True)
            # QtWidgets.QMessageBox.information(self, '提示', '载入成功')

    def burn_registers(self):
        choice = QtWidgets.QMessageBox.question(self, '提示', '除mic gain,其余register仅可烧录一次，是否确定烧录？')
        if choice == 16384:
            if self.usb_state == '芯片已连接...':
                if self.combo_chip_chose.currentIndex() == 0:
                    self.ui_burn_signal.emit(True)
            if self.usb_slave_state == 'slave芯片已连接...':
                if self.combo_chip_chose.currentIndex() == 1:
                    self.ui_burn_signal_slave.emit(True)
            time.sleep(1)

    def burn_times_slot(self, i):
        if self.sender() == self.usb:  # 主芯片更改
            self.chip_burn_times = i
            self.lcdNumber.setProperty("value", i)
            if i != 3:
                choice = QtWidgets.QMessageBox.question(self, '提示', '主芯片OTP已编程，是否重新载入参数？')
                if choice == 16384:
                    self.usb.ui_load_queue.put(True)
                    # if i == 2:  # 启用备用gain addr
                    #     value1 = self.registers_map[10].dec_value()
                    #     value2 = self.registers_map[11].dec_value()
                    #     self.write_registers(data=[0x10, value1])
                    #     self.write_registers(data=[0x11, value2])
                    # else:
                    #     value1 = self.registers_map[0].dec_value()
                    #     value2 = self.registers_map[1].dec_value()
                    #     self.write_registers(data=[0x12, value1])
                    #     self.write_registers(data=[0x13, value2])
                else:
                    self.usb.ui_load_queue.put(False)

        else:  # 从芯片更改
            self.chip_slave_burn_times = i
            self.lcdNumber_2.setProperty("value", i)
            if i != 3:
                choice = QtWidgets.QMessageBox.question(self, '提示', 'slave芯片OTP已编程，是否重新载入参数？')
                if choice == 16384:
                    self.usb_slave.ui_load_queue.put(True)
                    # if i == 2:  # 启用备用gain addr
                    #     value1 = self.registers_map[10].dec_value()
                    #     value2 = self.registers_map[11].dec_value()
                    #     self.write_registers(data=[0x10, value1])
                    #     self.write_registers(data=[0x11, value2])
                    # else:
                    #     value1 = self.registers_map[0].dec_value()
                    #     value2 = self.registers_map[1].dec_value()
                    #     self.write_registers(data=[0x12, value1])
                    #     self.write_registers(data=[0x13, value2])
                else:
                    self.usb_slave.ui_load_queue.put(False)

    def burn_state_message(self, message):
        QtWidgets.QMessageBox.information(self, '提示', message)

    # mic增益位置选择
    def mic_gain_addrs_chose_l(self, i):
        if self.combo_chip_chose.currentIndex() == 0:
            if self.chip_burn_times == 3:
                self.set_registers_data_anc_l(i)
            elif self.chip_burn_times == 2:
                if not self.registers_map[1].bit[0]:
                    value1 = int(self.registers_map[1].dec_value())
                    value1 += 0x80
                    self.write_registers(data=[0x11, value1])
                self.set_registers_data_anc_l2(i)
            else:
                if not self.registers_map[3].bit[0]:
                    value1 = int(self.registers_map[3].dec_value())
                    value1 += 0x80
                    self.write_registers(data=[0x13, value1])
                self.set_registers_data_anc_l3(i)
        elif self.combo_chip_chose.currentIndex() == 1:
            if self.chip_slave_burn_times == 3:
                self.set_registers_data_anc_l(i)
            elif self.chip_slave_burn_times == 2:
                if not self.registers_map[1].bit[0]:
                    value1 = int(self.registers_map[1].dec_value())
                    value1 += 0x80
                    self.write_registers(data=[0x11, value1])
                self.set_registers_data_anc_l2(i)
            else:
                if not self.registers_map[3].bit[0]:
                    value1 = int(self.registers_map[3].dec_value())
                    value1 += 0x80
                    self.write_registers(data=[0x13, value1])
                self.set_registers_data_anc_l3(i)

    def mic_gain_addrs_chose_r(self, i):
        if self.combo_chip_chose.currentIndex() == 0:
            if self.chip_burn_times == 3:
                self.set_registers_data_anc_r(i)
            elif self.chip_burn_times == 2:
                self.registers_map[1].bit[0] = True
                self.set_registers_data_anc_r2(i)
            else:
                self.registers_map[3].bit[0] = True
                self.set_registers_data_anc_r3(i)
        elif self.combo_chip_chose.currentIndex() == 1:
            if self.chip_slave_burn_times == 3:
                self.set_registers_data_anc_r(i)
            elif self.chip_slave_burn_times == 2:
                self.registers_map[1].bit[0] = True
                self.set_registers_data_anc_r2(i)
            else:
                self.registers_map[3].bit[0] = True
                self.set_registers_data_anc_r3(i)

    # eval
    @change_register(0x3d)
    def set_registers_data_eval(self, i):
        if self.sender() == self.radiobutton_power_off and i:  # 暂时无power off 状态
            self.registers_map[16].bit[4] = False
            self.registers_map[16].bit[5] = False
        elif self.sender() == self.radiobutton_anc and i:
            self.registers_map[16].bit[4] = False
            self.registers_map[16].bit[5] = False
        elif self.sender() == self.radiobutton_monitor and i:
            self.registers_map[16].bit[4] = True
            self.registers_map[16].bit[5] = False
        elif self.sender() == self.radiobutton_pbo and i:
            self.registers_map[16].bit[4] = False
            self.registers_map[16].bit[5] = True

            # mic mute L
        if self.sender() == self.checkbox_mute_l and i:
            self.registers_map[16].bit[6] = True
            self.label_31.setPixmap(QtGui.QPixmap(':/control/icon/control/Mic_op_left_open.png'))
        elif self.sender() == self.checkbox_mute_l and not i:
            self.registers_map[16].bit[6] = False
            self.label_31.setPixmap(QtGui.QPixmap(':/control/icon/control/Mic_op_left.png'))
        # mic mute R
        if self.sender() == self.checkbox_mute_r and i:
            self.registers_map[16].bit[7] = True
            self.label_32.setPixmap(QtGui.QPixmap(':/control/icon/control/Mic_op_right_open.png'))
        elif self.sender() == self.checkbox_mute_r and not i:
            self.registers_map[16].bit[7] = False
            self.label_32.setPixmap(QtGui.QPixmap(':/control/icon/control/Mic_op_right.png'))

    # ANC L
    @change_register(0x30)
    def set_registers_data_anc_l(self, i):  # gain下拉菜单选项值转变为二进制数
        """i为下拉菜单索引值，范围0~61"""
        a = bin(i).replace('0b', '')
        b = '0' * (6 - len(a))
        num = b + a
        for m in range(6):
            self.registers_map[10].bit[m + 2] = bool(int(num[m]))

    # ANC R
    @change_register(0x31)
    def set_registers_data_anc_r(self, i):
        a = bin(i).replace('0b', '')
        b = '0' * (6 - len(a))
        num = b + a
        for m in range(6):
            self.registers_map[11].bit[m + 2] = bool(int(num[m]))

    # MIC_MON_L
    @change_register(0x32)
    def set_registers_data_mic_mon_l(self, i):  # gain下拉菜单选项值转变为二进制数
        """i为下拉菜单索引值，范围0~61"""
        a = bin(i).replace('0b', '')
        b = '0' * (6 - len(a))
        num = b + a
        for m in range(6):
            self.registers_map[12].bit[m + 2] = bool(int(num[m]))

    # MIC_MON_R
    @change_register(0x33)
    def set_registers_data_mic_mon_r(self, i):  # gain下拉菜单选项值转变为二进制数
        """i为下拉菜单索引值，范围0~61"""
        a = bin(i).replace('0b', '')
        b = '0' * (6 - len(a))
        num = b + a
        for m in range(6):
            self.registers_map[13].bit[m + 2] = bool(int(num[m]))

    # mode_1
    @change_register(0x34)
    def set_registers_data_mode_1(self, i):
        # print(self.sender(),i)
        if self.sender() == self.checkbox_mic_charge_pump and i:  # print('1')
            self.registers_map[14].bit[0] = True
        elif self.sender() == self.checkbox_mic_charge_pump and not i:  # print('1 0')
            self.registers_map[14].bit[0] = False
        if self.sender() == self.checkbox_mic_mics and i:  # print('2')
            self.registers_map[14].bit[1] = True
        elif self.sender() == self.checkbox_mic_mics and not i:  # print('2 0')
            self.registers_map[14].bit[1] = False
        if self.sender() == self.checkbox_mic_agc and i:  # print('3')
            self.registers_map[14].bit[2] = True
        elif self.sender() == self.checkbox_mic_agc and not i:  # print('3 0')
            self.registers_map[14].bit[2] = False
        if self.sender() == self.checkbox_mic_power and i:  # print('4')
            self.registers_map[14].bit[3] = True
            self.label_31.setEnabled(False)
            self.label_32.setEnabled(False)
        elif self.sender() == self.checkbox_mic_power and not i:  # print('4 0')
            self.registers_map[14].bit[3] = False
            self.label_31.setEnabled(True)
            self.label_32.setEnabled(True)
        if self.sender() == self.checkbox_other_low_battery_shutdown and i:  # print('5')
            self.registers_map[14].bit[4] = True
        elif self.sender() == self.checkbox_other_low_battery_shutdown and not i:  # print('5 0')
            self.registers_map[14].bit[4] = False
        if self.sender() == self.checkbox_other_close_vneg and i:  # print('6')
            self.registers_map[14].bit[5] = True
        elif self.sender() == self.checkbox_other_close_vneg and not i:  # print('6 0')
            self.registers_map[14].bit[5] = False
        if self.sender() == self.checkbox_hph_power and i:  # print('7')
            self.registers_map[14].bit[6] = True
            self.label_40.setEnabled(False)
        elif self.sender() == self.checkbox_hph_power and not i:  # print('7 0')
            self.registers_map[14].bit[6] = False
            self.label_40.setEnabled(True)
        if self.sender() == self.checkbox_line_power and i:  # print('8')
            self.registers_map[14].bit[7] = True
            self.label_39.setEnabled(False)
        elif self.sender() == self.checkbox_line_power and not i:  # print('8 0')
            self.registers_map[14].bit[7] = False
            self.label_39.setEnabled(True)

    # mode_2
    @change_register(0x35)
    def set_registers_data_mode_2(self, i):
        if self.sender() == self.checkbox_line_difference and i:
            self.registers_map[15].bit[3] = True
        elif self.sender() == self.checkbox_line_difference and not i:
            self.registers_map[15].bit[3] = False
        if self.sender() == self.checkbox_other_mic_supply and i:
            self.registers_map[15].bit[4] = True
        elif self.sender() == self.checkbox_other_mic_supply and not i:
            self.registers_map[15].bit[4] = False
        if self.sender() == self.checkbox_other_hph_delay and i:
            self.registers_map[15].bit[5] = True
        elif self.sender() == self.checkbox_other_hph_delay and not i:
            self.registers_map[15].bit[5] = False
        if self.sender() == self.radiobutton_hph_difference and i:
            self.registers_map[15].bit[6] = False
            print('差分')
        elif self.sender() == self.radiobutton_hph_difference and not i:
            self.registers_map[15].bit[6] = True
            print('单端')
        pass

    # ANC L2
    @change_register(0x10)
    def set_registers_data_anc_l2(self, i):  # gain下拉菜单选项值转变为二进制数
        """i为下拉菜单索引值，范围0~61"""
        a = bin(i).replace('0b', '')
        b = '0' * (6 - len(a))
        num = b + a
        for m in range(6):
            self.registers_map[0].bit[m + 2] = bool(int(num[m]))

    # ANC R2
    @change_register(0x11)
    def set_registers_data_anc_r2(self, i):
        a = bin(i).replace('0b', '')
        b = '0' * (6 - len(a))
        num = b + a
        for m in range(6):
            self.registers_map[1].bit[m + 2] = bool(int(num[m]))

    # ANC L3
    @change_register(0x12)
    def  set_registers_data_anc_l3(self, i):  # gain下拉菜单选项值转变为二进制数
        """i为下拉菜单索引值，范围0~61"""
        a = bin(i).replace('0b', '')
        b = '0' * (6 - len(a))
        num = b + a
        for m in range(6):
            self.registers_map[2].bit[m + 2] = bool(int(num[m]))

    # ANC R3
    @change_register(0x13)
    def set_registers_data_anc_r3(self, i):
        a = bin(i).replace('0b', '')
        b = '0' * (6 - len(a))
        num = b + a
        for m in range(6):
            self.registers_map[3].bit[m + 2] = bool(int(num[m]))

    # ANC_MODE
    @change_register(0x14)
    def set_registers_data_anc_mode(self, i):
        if self.sender() == self.radiobutton_none and i:
            self.registers_map[4].bit[0] = True
            self.registers_map[4].bit[1] = True
            self.label_35.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_open.png"))
            self.label_36.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_open.png"))
            self.label_33.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1L.png"))
            self.label_34.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1R.png"))
            self.label_42.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2L.png"))
            self.label_43.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2R.png"))
        elif self.sender() == self.radiobutton_mic and i:
            self.registers_map[4].bit[0] = False
            self.registers_map[4].bit[1] = False
            self.label_35.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_36.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_33.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_34.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_42.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_43.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
        elif self.sender() == self.radiobutton_op1 and i:
            self.registers_map[4].bit[0] = False
            self.registers_map[4].bit[1] = True
            self.label_35.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_36.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_33.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1L.png"))
            self.label_34.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1R.png"))
            self.label_42.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_43.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
        elif self.sender() == self.radiobutton_op2 and i:
            self.registers_map[4].bit[0] = True
            self.registers_map[4].bit[1] = False
            self.label_35.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_36.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_33.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1L.png"))
            self.label_34.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1R.png"))
            self.label_42.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2L.png"))
            self.label_43.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2R.png"))
        if self.sender() == self.checkbox_mute_line_in and i:
            self.registers_map[4].bit[2] = True
            self.label_39.setPixmap(QtGui.QPixmap(":/control/icon/control/line_in_off.png"))
        elif self.sender() == self.checkbox_mute_line_in and not i:
            self.registers_map[4].bit[2] = False
            self.label_39.setPixmap(QtGui.QPixmap(":/control/icon/control/line_in.png"))
        if self.sender() == self.checkbox_mute_mix and i:
            self.registers_map[4].bit[3] = True
            self.label_37.setPixmap(QtGui.QPixmap(":/control/icon/control/mix_in.png"))
        elif self.sender() == self.checkbox_mute_mix and not i:
            self.registers_map[4].bit[3] = False
            self.label_37.setPixmap(QtGui.QPixmap(":/control/icon/control/mix_in_off.png"))
        if self.sender() == self.checkbox_op_l2 and i:
            self.registers_map[4].bit[4] = True
            self.label_42.setEnabled(True)
        elif self.sender() == self.checkbox_op_l2 and not i:
            self.registers_map[4].bit[4] = False
            self.label_42.setEnabled(False)
        if self.sender() == self.checkbox_op_r2 and i:
            self.registers_map[4].bit[5] = True
            self.label_43.setEnabled(True)
        elif self.sender() == self.checkbox_op_r2 and not i:
            self.registers_map[4].bit[5] = False
            self.label_43.setEnabled(False)
        if self.sender() == self.checkbox_op_l1 and i:
            self.registers_map[4].bit[6] = True
            self.label_33.setEnabled(True)
        elif self.sender() == self.checkbox_op_l1 and not i:
            self.registers_map[4].bit[6] = False
            self.label_33.setEnabled(False)
        if self.sender() == self.checkbox_op_r1 and i:
            self.registers_map[4].bit[7] = True
            self.label_34.setEnabled(True)
        elif self.sender() == self.checkbox_op_r1 and not i:
            self.registers_map[4].bit[7] = False
            self.label_34.setEnabled(False)

    # MON_MODE
    @change_register(0x15)
    def set_registers_data_monitor_mode(self, i):
        if self.sender() == self.radiobutton_none_2 and i:
            self.registers_map[5].bit[0] = True
            self.registers_map[5].bit[1] = True
            self.label_47.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_open.png"))
            self.label_48.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_open.png"))
            self.label_52.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1L.png"))
            self.label_53.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1R.png"))
            self.label_54.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2L.png"))
            self.label_55.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2R.png"))
        elif self.sender() == self.radiobutton_mic_2 and i:
            self.registers_map[5].bit[0] = False
            self.registers_map[5].bit[1] = False
            self.label_47.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_48.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_52.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_53.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_54.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_55.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
        elif self.sender() == self.radiobutton_op1_2 and i:
            self.registers_map[5].bit[0] = False
            self.registers_map[5].bit[1] = True
            self.label_47.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_48.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_52.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1L.png"))
            self.label_53.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1R.png"))
            self.label_54.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_55.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
        elif self.sender() == self.radiobutton_op2_2 and i:
            self.registers_map[5].bit[0] = True
            self.registers_map[5].bit[1] = False
            self.label_47.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_48.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_52.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1L.png"))
            self.label_53.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1R.png"))
            self.label_54.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2L.png"))
            self.label_55.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2R.png"))
        if self.sender() == self.checkbox_mute_line_in_2 and i:
            self.registers_map[5].bit[2] = True
            self.label_44.setPixmap(QtGui.QPixmap(":/control/icon/control/line_in_off.png"))
        elif self.sender() == self.checkbox_mute_line_in_2 and not i:
            self.registers_map[5].bit[2] = False
            self.label_44.setPixmap(QtGui.QPixmap(":/control/icon/control/line_in.png"))
        if self.sender() == self.checkbox_mute_mix_2 and i:
            self.registers_map[5].bit[3] = True
            self.label_46.setPixmap(QtGui.QPixmap(":/control/icon/control/mix_in.png"))
        elif self.sender() == self.checkbox_mute_mix_2 and not i:
            self.registers_map[5].bit[3] = False
            self.label_46.setPixmap(QtGui.QPixmap(":/control/icon/control/mix_in_off.png"))
        if self.sender() == self.combo_line_gain and i == 0:
            self.registers_map[5].bit[4] = False
            self.registers_map[5].bit[5] = False
        elif self.sender() == self.combo_line_gain and i == 1:
            self.registers_map[5].bit[4] = False
            self.registers_map[5].bit[5] = True
        elif self.sender() == self.combo_line_gain and i == 2:
            self.registers_map[5].bit[4] = True
            self.registers_map[5].bit[5] = False
        elif self.sender() == self.combo_line_gain and i == 3:
            self.registers_map[5].bit[4] = True
            self.registers_map[5].bit[5] = True
        if self.sender() == self.combo_monitor_slide and i == 0:
            self.registers_map[5].bit[6] = False
        elif self.sender() == self.combo_monitor_slide and i == 1:
            self.registers_map[5].bit[6] = True
        if self.sender() == self.radiobutton_monitor_on and i:
            self.registers_map[5].bit[7] = False
        elif self.sender() == self.radiobutton_monitor_off and i:
            self.registers_map[5].bit[7] = True

    # PBO_MODE
    @change_register(0x16)
    def set_registers_data_pbo_mode(self, i):
        if self.sender() == self.radiobutton_pbo_on and i:
            self.registers_map[6].bit[1] = False
        elif self.sender() == self.radiobutton_pbo_off and i:
            self.registers_map[6].bit[1] = True
        if self.sender() == self.checkbox_mute_line_in_5 and i:
            self.registers_map[6].bit[2] = True
            self.label_80.setPixmap(QtGui.QPixmap(":/control/icon/control/line_in_off.png"))
        elif self.sender() == self.checkbox_mute_line_in_5 and not i:
            self.registers_map[6].bit[2] = False
            self.label_80.setPixmap(QtGui.QPixmap(":/control/icon/control/line_in.png"))
        if self.sender() == self.checkbox_mute_mix_5 and i:
            self.registers_map[6].bit[3] = True
            self.label_82.setPixmap(QtGui.QPixmap(":/control/icon/control/mix_in.png"))
        elif self.sender() == self.checkbox_mute_mix_5 and not i:
            self.registers_map[6].bit[3] = False
            self.label_82.setPixmap(QtGui.QPixmap(":/control/icon/control/mix_in_off.png"))
        if self.sender() == self.checkbox_op_l2_5 and i:
            self.registers_map[6].bit[4] = True
            self.label_90.setEnabled(True)
        elif self.sender() == self.checkbox_op_l2_5 and not i:
            self.registers_map[6].bit[4] = False
            self.label_90.setEnabled(False)
        if self.sender() == self.checkbox_op_r2_5 and i:
            self.registers_map[6].bit[5] = True
            self.label_91.setEnabled(True)
        elif self.sender() == self.checkbox_op_r2_5 and not i:
            self.registers_map[6].bit[5] = False
            self.label_91.setEnabled(False)
        if self.sender() == self.checkbox_op_l1_5 and i:
            self.registers_map[6].bit[6] = True
            self.label_88.setEnabled(True)
        elif self.sender() == self.checkbox_op_l1_5 and not i:
            self.registers_map[6].bit[6] = False
            self.label_88.setEnabled(False)
        if self.sender() == self.checkbox_op_r1_5 and i:
            self.registers_map[6].bit[7] = True
            self.label_89.setEnabled(True)
        elif self.sender() == self.checkbox_op_r1_5 and not i:
            self.registers_map[6].bit[7] = False
            self.label_89.setEnabled(False)

    # ECO
    @change_register(0x17)
    def set_registers_data_eco(self, i):
        if self.sender() == self.combo_power_slide and i == 0:
            self.registers_map[7].bit[0] = False
        elif self.sender() == self.combo_power_slide and i == 1:
            self.registers_map[7].bit[0] = True
        if self.sender() == self.checkbox_other_low_battery and i:
            self.registers_map[7].bit[1] = True
        elif self.sender() == self.checkbox_other_low_battery and not i:
            self.registers_map[7].bit[1] = False
        if self.sender() == self.radiobutton_led_0 and i:
            self.registers_map[7].bit[2] = False
            self.registers_map[7].bit[3] = False
        elif self.sender() == self.radiobutton_led_25 and i:
            self.registers_map[7].bit[2] = False
            self.registers_map[7].bit[3] = True
        elif self.sender() == self.radiobutton_led_50 and i:
            self.registers_map[7].bit[2] = True
            self.registers_map[7].bit[3] = False
        elif self.sender() == self.radiobutton_led_100 and i:
            self.registers_map[7].bit[2] = True
            self.registers_map[7].bit[3] = True
        if self.sender() == self.checkbox_hph_eco and i:
            self.registers_map[7].bit[4] = True
        elif self.sender() == self.checkbox_hph_eco and not i:
            self.registers_map[7].bit[4] = False
        if self.sender() == self.checkbox_mic_eco and i:
            self.registers_map[7].bit[5] = True
        elif self.sender() == self.checkbox_mic_eco and not i:
            self.registers_map[7].bit[5] = False
        if self.sender() == self.checkbox_line_eco and i:
            self.registers_map[7].bit[6] = True
        elif self.sender() == self.checkbox_line_eco and not i:
            self.registers_map[7].bit[6] = False
        if self.sender() == self.checkbox_op_eco and i:
            self.registers_map[7].bit[7] = True
        elif self.sender() == self.checkbox_op_eco and not i:
            self.registers_map[7].bit[7] = False
        # print(self.registers_map[7].bool_to_01())

    # zgmicro register
    @change_register(0x10)
    def set_registers_data_line_in(self, i):  # 0x10 bit 1, line in 差分与单端控制
        if self.sender() == self.radiobutton_line_in_mono and i:
            self.registers_map[0].bit[1] = False
        elif self.sender() == self.radiobutton_line_in_stereo and i:
            self.registers_map[0].bit[1] = True

    @change_register(0x11)
    def set_registers_data_hph_l(self, i):  # 0x11 bit 1, HPH-L开关控制
        if self.sender() == self.radiobutton_hph_l_on and i:
            self.registers_map[1].bit[1] = True
            self.label_40.setPixmap(QtGui.QPixmap(":/control/icon/control/HPH.png"))
        elif self.sender() == self.radiobutton_hph_l_off and i:
            self.registers_map[1].bit[1] = False
            self.label_40.setPixmap(QtGui.QPixmap(":/control/icon/control/HPH_1.png"))

    # save registers
    def save_registers(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'save file', '.', 'xml Files (*.xml);;All Files (*)')
        if filename[0]:
            root = ET.Element('Settings')  # 根目录设置
            root.attrib = dict(Version='1.0.0.0')

            sub1 = ET.SubElement(root, 'Registers')  # 目录1 registers
            for i in range(2):
                a = ET.SubElement(sub1, 'reg')
                addr_i = str(hex(0x20 + i))
                value = self.registers_map[i + 8].hex_value()
                a.attrib = dict(addr=addr_i, nr=str(i + 8), val=str(value))
            for i in range(3):
                a = ET.SubElement(sub1, 'reg')
                addr_i = str(hex(0x3d + i))
                value = self.registers_map[i + 16].hex_value()
                a.attrib = dict(addr=addr_i, nr=str(i + 16), val=str(value))

            sub2 = ET.SubElement(root, 'OTPRegisters')  # 目录2 OTP
            for i in range(8):  # 前八行
                b = ET.SubElement(sub2, 'reg')
                addr_i = str(hex(0x10 + i))
                value = self.registers_map[i].hex_value()
                b.attrib = dict(addr=addr_i, nr=str(i), val=str(value))
            for i in range(6):
                b = ET.SubElement(sub2, 'reg')
                addr_i = str(hex(0x30 + i))
                value = self.registers_map[i + 10].hex_value()
                b.attrib = dict(addr=addr_i, nr=str(i + 10), val=str(value))

            self.pretty_xml(root, '\t', '\n')
            # ET.dump(root)
            tree = ET.ElementTree(root)
            tree.write(filename[0])
            QtWidgets.QMessageBox.information(self, '提示', '保存成功')
        pass

    def pretty_xml(self, element, indent, newline, level=0):  # element为传进来的Element类，参数indent用于缩进，newline用于换行
        """xml格式美化函数"""
        if element:  # 判断element是否有子元素
            if element.text is None or element.text.isspace():  # 如果element的text没有内容
                element.text = newline + indent * (level + 1)
            else:
                element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * (level + 1)
        # else:  # 此处两行如果把注释去掉，Element的text也会另起一行
        # element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * level
        temp = list(element)  # 将element转成list
        for subelement in temp:
            if temp.index(subelement) < (len(temp) - 1):  # 如果不是list的最后一个元素，说明下一个行是同级别元素的起始，缩进应一致
                subelement.tail = newline + indent * (level + 1)
            else:  # 如果是list的最后一个元素， 说明下一行是母元素的结束，缩进应该少一个
                subelement.tail = newline + indent * level
            self.pretty_xml(subelement, indent, newline, level=level + 1)  # 对子元素进行递归操作

    # import registers
    def import_registers(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', '.', 'xml Files (*.xml);;All Files (*)')
        if filename[0]:
            try:
                tree = ET.parse(filename[0])  # 读取xml
                root = tree.getroot()
                data = dict()
                for child in root.iter('reg'):  # 按照储存的nr数值填写value_map
                    data[child.attrib['nr']] = child.attrib['val']
                values = list(range(len(data)))
                for k, v in data.items():
                    values[int(k)] = int(v, base=16)
                value_map = list()
                for i in values:
                    a = bin(i).replace('0b', '')
                    b = '0' * (8 - len(a))
                    num = b + a
                    value_map.append(num)
                for i in range(8):
                    for j in range(19):
                        self.registers_map[j].bit[i] = bool(int(value_map[j][i]))
                self.registers_map_to_ui()
                QtWidgets.QMessageBox.information(self, '提示', '导入成功')
            except ValueError as e:
                QtWidgets.QMessageBox.warning(self, '提示', str(e), QtWidgets.QMessageBox.Yes)

    def registers_map_to_ui(self):
        """UI界面更新函数"""
        data = self.registers_map
        # ANC MODE
        if data[4].bit[0] and data[4].bit[1]:
            self.radiobutton_none.setChecked(True)
            self.label_35.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_open.png"))
            self.label_36.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_open.png"))
            self.label_33.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1L.png"))
            self.label_34.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1R.png"))
            self.label_42.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2L.png"))
            self.label_43.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2R.png"))
        elif not data[4].bit[0] and not data[4].bit[1]:
            self.radiobutton_mic.setChecked(True)
            self.label_35.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_36.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_33.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_34.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_42.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_43.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
        elif not data[4].bit[0] and data[4].bit[1]:
            self.radiobutton_op1.setChecked(True)
            self.label_35.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_36.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_33.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1L.png"))
            self.label_34.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1R.png"))
            self.label_42.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_43.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
        elif data[4].bit[0] and not data[4].bit[1]:
            self.radiobutton_op2.setChecked(True)
            self.label_35.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_36.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_33.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1L.png"))
            self.label_34.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1R.png"))
            self.label_42.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2L.png"))
            self.label_43.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2R.png"))
        if data[4].bit[2]:
            self.checkbox_mute_line_in.setChecked(True)
            self.label_39.setPixmap(QtGui.QPixmap(":/control/icon/control/line_in_off.png"))
        else:
            self.checkbox_mute_line_in.setChecked(False)
            self.label_39.setPixmap(QtGui.QPixmap(":/control/icon/control/line_in.png"))
        if data[4].bit[3]:
            self.checkbox_mute_mix.setChecked(True)
            self.label_37.setPixmap(QtGui.QPixmap(":/control/icon/control/mix_in.png"))
        else:
            self.checkbox_mute_mix.setChecked(False)
            self.label_37.setPixmap(QtGui.QPixmap(":/control/icon/control/mix_in_off.png"))
        if data[4].bit[4]:
            self.checkbox_op_l2.setChecked(True)
            self.label_42.setEnabled(True)
        else:
            self.checkbox_op_l2.setChecked(False)
            self.label_42.setEnabled(False)
        if data[4].bit[5]:
            self.checkbox_op_r2.setChecked(True)
            self.label_43.setEnabled(True)
        else:
            self.checkbox_op_r2.setChecked(False)
            self.label_43.setEnabled(False)
        if data[4].bit[6]:
            self.checkbox_op_l1.setChecked(True)
            self.label_33.setEnabled(True)
        else:
            self.checkbox_op_l1.setChecked(False)
            self.label_33.setEnabled(False)
        if data[4].bit[7]:
            self.checkbox_op_r1.setChecked(True)
            self.label_34.setEnabled(True)
        else:
            self.checkbox_op_r1.setChecked(False)
            self.label_34.setEnabled(False)
        # MON MODE
        if data[5].bit[0] and data[5].bit[1]:
            self.radiobutton_none_2.setChecked(True)
            self.label_47.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_open.png"))
            self.label_48.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_open.png"))
            self.label_52.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1L.png"))
            self.label_53.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1R.png"))
            self.label_54.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2L.png"))
            self.label_55.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2R.png"))
        elif not data[5].bit[0] and not data[5].bit[1]:
            self.radiobutton_mic_2.setChecked(True)
            self.label_47.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_48.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_52.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_53.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_54.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_55.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
        elif not data[5].bit[0] and data[5].bit[1]:
            self.radiobutton_op1_2.setChecked(True)
            self.label_47.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_48.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_52.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1L.png"))
            self.label_53.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1R.png"))
            self.label_54.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
            self.label_55.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE_half.png"))
        elif data[5].bit[0] and not data[5].bit[1]:
            self.radiobutton_op2_2.setChecked(True)
            self.label_47.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_48.setPixmap(QtGui.QPixmap(":/control/icon/control/LINE.png"))
            self.label_52.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1L.png"))
            self.label_53.setPixmap(QtGui.QPixmap(":/control/icon/control/OP1R.png"))
            self.label_54.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2L.png"))
            self.label_55.setPixmap(QtGui.QPixmap(":/control/icon/control/OP2R.png"))
        if data[5].bit[2]:
            self.checkbox_mute_line_in_2.setChecked(True)
            self.label_44.setPixmap(QtGui.QPixmap(":/control/icon/control/line_in_off.png"))
        else:
            self.checkbox_mute_line_in_2.setChecked(False)
            self.label_44.setPixmap(QtGui.QPixmap(":/control/icon/control/line_in.png"))
        if data[5].bit[3]:
            self.checkbox_mute_mix_2.setChecked(True)
            self.label_46.setPixmap(QtGui.QPixmap(":/control/icon/control/mix_in.png"))
        else:
            self.checkbox_mute_mix_2.setChecked(False)
            self.label_46.setPixmap(QtGui.QPixmap(":/control/icon/control/mix_in_off.png"))
        if data[5].bit[4] and data[5].bit[5]:
            self.combo_line_gain.setCurrentIndex(3)
        elif data[5].bit[4] and not data[5].bit[5]:
            self.combo_line_gain.setCurrentIndex(2)
        elif not data[5].bit[4] and data[5].bit[5]:
            self.combo_line_gain.setCurrentIndex(1)
        elif not data[5].bit[4] and not data[5].bit[5]:
            self.combo_line_gain.setCurrentIndex(0)
        if data[5].bit[6]:
            self.combo_monitor_slide.setCurrentIndex(1)
        else:
            self.combo_monitor_slide.setCurrentIndex(0)
        if data[5].bit[7]:
            self.radiobutton_monitor_off.setChecked(True)
        else:
            self.radiobutton_monitor_on.setChecked(True)
        # PBO MODE
        if data[6].bit[1]:
            self.radiobutton_pbo_off.setChecked(True)
        else:
            self.radiobutton_pbo_on.setChecked(True)
        if data[6].bit[2]:
            self.checkbox_mute_line_in_5.setChecked(True)
            self.label_80.setPixmap(QtGui.QPixmap(":/control/icon/control/line_in_off.png"))
        else:
            self.checkbox_mute_line_in_5.setChecked(False)
            self.label_80.setPixmap(QtGui.QPixmap(":/control/icon/control/line_in.png"))
        if data[6].bit[3]:
            self.checkbox_mute_mix_5.setChecked(True)
            self.label_82.setPixmap(QtGui.QPixmap(":/control/icon/control/mix_in.png"))
        else:
            self.checkbox_mute_mix_5.setChecked(False)
            self.label_82.setPixmap(QtGui.QPixmap(":/control/icon/control/mix_in_off.png"))
        if data[6].bit[4]:
            self.checkbox_op_l2_5.setChecked(True)
            self.label_90.setEnabled(True)
        else:
            self.checkbox_op_l2_5.setChecked(False)
            self.label_90.setEnabled(False)
        if data[6].bit[5]:
            self.checkbox_op_r2_5.setChecked(True)
            self.label_91.setEnabled(True)
        else:
            self.checkbox_op_r2_5.setChecked(False)
            self.label_91.setEnabled(False)
        if data[6].bit[6]:
            self.checkbox_op_l1_5.setChecked(True)
            self.label_88.setEnabled(True)
        else:
            self.checkbox_op_l1_5.setChecked(False)
            self.label_88.setEnabled(False)
        if data[6].bit[7]:
            self.checkbox_op_r1_5.setChecked(True)
            self.label_89.setEnabled(True)
        else:
            self.checkbox_op_r1_5.setChecked(False)
            self.label_89.setEnabled(False)
        # ECO
        if data[7].bit[0]:
            self.combo_power_slide.setCurrentIndex(1)
        else:
            self.combo_power_slide.setCurrentIndex(0)
        if data[7].bit[1]:
            self.checkbox_other_low_battery.setChecked(True)
        else:
            self.checkbox_other_low_battery.setChecked(False)
        if data[7].bit[2] and data[7].bit[3]:
            self.radiobutton_led_100.setChecked(True)
        elif data[7].bit[2] and not data[7].bit[3]:
            self.radiobutton_led_50.setChecked(True)
        elif not data[7].bit[2] and data[7].bit[3]:
            self.radiobutton_led_25.setChecked(True)
        elif not data[7].bit[2] and not data[7].bit[3]:
            self.radiobutton_led_0.setChecked(True)
        if data[7].bit[4]:
            self.checkbox_hph_eco.setChecked(True)
        else:
            self.checkbox_hph_eco.setChecked(False)
        if data[7].bit[5]:
            self.checkbox_mic_eco.setChecked(True)
        else:
            self.checkbox_mic_eco.setChecked(False)
        if data[7].bit[6]:
            self.checkbox_line_eco.setChecked(True)
        else:
            self.checkbox_line_eco.setChecked(False)
        if data[7].bit[7]:
            self.checkbox_op_eco.setChecked(True)
        else:
            self.checkbox_op_eco.setChecked(False)

        # ANC_L
        if data[3].bit[0]:
            index = data[2].dec_value_latter_six()
            if int(index) < 62:
                self.combo_mic_gain_l.setCurrentIndex(int(index))
        elif data[1].bit[0]:
            index = data[0].dec_value_latter_six()
            if int(index) < 62:
                self.combo_mic_gain_l.setCurrentIndex(int(index))
        else:
            index = data[10].dec_value_latter_six()
            if int(index) < 62:
                self.combo_mic_gain_l.setCurrentIndex(int(index))

        # ANC_R
        if data[3].bit[0]:
            index = data[3].dec_value_latter_six()
            if int(index) < 62:
                self.combo_mic_gain_r.setCurrentIndex(int(index))
        elif data[1].bit[0]:
            index = data[1].dec_value_latter_six()
            if int(index) < 62:
                self.combo_mic_gain_r.setCurrentIndex(int(index))
        else:
            index = data[11].dec_value_latter_six()
            if int(index) < 62:
                self.combo_mic_gain_r.setCurrentIndex(int(index))

        # MIC_MON_L
        index = data[12].dec_value_latter_six()
        if int(index) < 62:
            self.combo_mic_gain_l_2.setCurrentIndex(int(index))
        # MIC_MON_R
        index = data[13].dec_value_latter_six()
        if int(index) < 62:
            self.combo_mic_gain_r_2.setCurrentIndex(int(index))
        # MODE_1
        if data[14].bit[0]:
            self.checkbox_mic_charge_pump.setChecked(True)
        else:
            self.checkbox_mic_charge_pump.setChecked(False)
        if data[14].bit[1]:
            self.checkbox_mic_mics.setChecked(True)
        else:
            self.checkbox_mic_mics.setChecked(False)
        if data[14].bit[2]:
            self.checkbox_mic_agc.setChecked(True)
        else:
            self.checkbox_mic_agc.setChecked(False)
        if data[14].bit[3]:
            self.checkbox_mic_power.setChecked(True)
            self.label_31.setEnabled(False)
            self.label_32.setEnabled(False)
        else:
            self.checkbox_mic_power.setChecked(False)
            self.label_31.setEnabled(True)
            self.label_32.setEnabled(True)
        if data[14].bit[4]:
            self.checkbox_other_low_battery_shutdown.setChecked(True)
        else:
            self.checkbox_other_low_battery_shutdown.setChecked(False)
        if data[14].bit[5]:
            self.checkbox_other_close_vneg.setChecked(True)
        else:
            self.checkbox_other_close_vneg.setChecked(False)
        if data[14].bit[6]:
            self.checkbox_hph_power.setChecked(True)
            self.label_40.setEnabled(False)
        else:
            self.checkbox_hph_power.setChecked(False)
            self.label_40.setEnabled(True)
        if data[14].bit[7]:
            self.checkbox_line_power.setChecked(True)
            self.label_39.setEnabled(False)
        else:
            self.checkbox_line_power.setChecked(False)
            self.label_39.setEnabled(True)
        # MODE_2
        if data[15].bit[3]:
            self.checkbox_line_difference.setChecked(True)
        else:
            self.checkbox_line_difference.setChecked(False)
        if data[15].bit[4]:
            self.checkbox_other_mic_supply.setChecked(True)
        else:
            self.checkbox_other_mic_supply.setChecked(False)
        if data[15].bit[5]:
            self.checkbox_other_hph_delay.setChecked(True)
        else:
            self.checkbox_other_hph_delay.setChecked(False)
        if data[15].bit[6]:
            self.radiobutton_hph_singer_ended.setChecked(True)
        else:
            self.radiobutton_hph_difference.setChecked(True)
        # EVAL
        if data[16].bit[4] and not data[16].bit[5]:
            self.radiobutton_monitor.setChecked(True)
        elif not data[16].bit[4] and data[16].bit[5]:
            self.radiobutton_pbo.setChecked(True)
        else:
            self.radiobutton_anc.setChecked(True)
        if data[16].bit[6]:
            self.checkbox_mute_l.setChecked(True)
            self.label_31.setPixmap(QtGui.QPixmap(':/control/icon/control/Mic_op_left_open.png'))
        else:
            self.checkbox_mute_l.setChecked(False)
            self.label_31.setPixmap(QtGui.QPixmap(':/control/icon/control/Mic_op_left.png'))
        if data[16].bit[7]:
            self.checkbox_mute_r.setChecked(True)
            self.label_32.setPixmap(QtGui.QPixmap(':/control/icon/control/Mic_op_right_open.png'))
        else:
            self.checkbox_mute_r.setChecked(False)
            self.label_32.setPixmap(QtGui.QPixmap(':/control/icon/control/Mic_op_right.png'))

        # zgmicro registers
        if data[0].bit[1]:
            self.radiobutton_line_in_stereo.setChecked(True)
        else:
            self.radiobutton_line_in_mono.setChecked(True)
        if data[1].bit[1]:
            self.radiobutton_hph_l_on.setChecked(True)
        else:
            self.radiobutton_hph_l_off.setChecked(True)

    # OTP
    def reset_registers(self):
        """重置registers_map数据，更新UI界面"""
        self.set_default_registers()
        self.registers_map_to_ui()

    # def py_cmp_func(self, e):
    #     """
    #     USB检测回调函数
    #     #define		CH341_DEVICE_ARRIVAL		3		// 设备插入事件,已经插入
    #     #define		CH341_DEVICE_REMOVE_PEND	1		// 设备将要拔出
    #     #define		CH341_DEVICE_REMOVE			0		// 设备拔出事件,已经拔出
    #     """
    #     if e == 0:
    #         lib.USBIO_CloseDevice(0)
    #         self.usb_connected_signal.emit(False)
    #         self.show_usb_connect_state('USB未连接...')
    #     if e == 3:
    #         lib.USBIO_OpenDevice(0)
    #         lib.USBIO_SetStream(0, 0x80)
    #         self.usb_connected_signal.emit(True)
    #         self.show_usb_connect_state('USB已连接,检测芯片中...')

    def closeEvent(self, event):
        lib.HID_Destory()

    def test(self, a):
        print(1)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myWin = AncControlWindow()
    myWin.show()
    sys.exit(app.exec_())
