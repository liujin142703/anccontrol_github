#!/usr/bin/env python
# -*- coding:utf-8 -*-
import numpy as np
import sys

import control
from PyQt5 import QtGui, QtWidgets

from main_UI import Ui_MainWindow  # 导入UI
# 导入私有模块
from get_capacitance_value import c_value2map, c_value2map_dubble  # 计数器to电容容值
from get_resistance_value import get_R_value, R_value2map, R_value2map_2  # 滑块数值to电阻阻值
from value_tuning.notch_tuning_main import MyNotchFilterTuningDialog
from value_tuning.peak_tuning_main import MyPeakFilterTuningDialog
from value_tuning.two_order_lowpass_tuning_main import MyTwoOrderLowpassTuningDialog


class SetOp2Window(QtWidgets.QMainWindow, Ui_MainWindow):
    """FF_Filter设计主运行程序
    1.用Subcircuit拼装电路
    2.参考曲线导入及仿真计算跟notchFilter2cir方法相同
    """
    default_notch_r_value = 6800
    default_peak_r_value = 30000
    default_op_gain_r_value = 30000

    def __init__(self, parent=None):

        super(SetOp2Window, self).__init__(parent)
        if __name__ == '__main__':
            self.setupUi(self)
        # self.showMaximized() # 窗口最大化显示
        self.set_op2_default_data()
        self.set_op2_default_module()
        self.set_op2_signals_slots()

        self.op2_gain = self.OP_gain_spin_2.value()  # 初始化OP gain，实现动态记录
        self.peak02_gain = self.peak_gain_spin_2.value()

    def get_Rb_value(self, gain=0):
        """
        OP增益电阻Rb取值，增益范围-20-20dB，Ra默认200k
        第一个返回值为map_str值，第二个范围值为Rb阻值对应的float数值
        """
        if -20 <= gain <= 20:
            Rb_value = self.default_op_gain_r_value * (10 ** (gain / 20))
            R_value = np.array([2000., 2200., 2400., 2700., 3000., 3300., 3600.,
                                3900., 4300., 4700., 5100., 5600., 6200., 6800.,
                                7500., 8200., 9100., 10000., 11000., 12000., 13000.,
                                15000., 16000., 18000., 20000., 22000., 24000., 27000.,
                                30000., 33000., 36000., 39000., 43000., 47000., 51000.,
                                56000., 62000., 68000., 75000., 82000., 91000., 100000.,
                                110000., 120000., 130000., 150000., 160000., 180000., 200000.,
                                220000., 240000., 270000.,
                                300000., 330000., 360000., 390000., 430000., 470000., 510000.,
                                560000., 620000., 680000., 750000., 820000., 910000., 1000000.,
                                1100000., 1200000., 1300000., 1500000., 1600000., 1800000., 2000000., 2200000.,
                                2400000., 2700000.,
                                3000000., 3300000., 3600000., 3900000., 4300000., 4700000., 5100000.,
                                5600000., 6200000., 6800000., 7500000., 8200000., 9100000., 10000000.,
                                11000000., 12000000., 13000000., 15000000., 16000000., 18000000., 20000000.])
            D_value = abs(R_value - Rb_value)
            pos = np.where(D_value == D_value.min())
            # E12系列电容容值标准
            Rb_valueMap = ['2k', '2.2k', '2.4k', '2.7k', '3k', '3.3k', '3.6k',
                           '3.9k', '4.3k', '4.7k', '5.1k', '5.6k', '6.2k', '6.8k',
                           '7.5k', '8.2k', '9.1k', '10k', '11k', '12k', '13k',
                           '15k', '16k', '18k', '20k', '22k', '24k', '27k',
                           '30k', '33k', '36k', '39k', '43k', '47k', '51k',
                           '56k', '62k', '68k', '75k', '82k', '91k', '100k',
                           '110k', '120k', '130k', '150k', '160k', '180k', '200k',
                           '220k', '240k', '270k',
                           '300k', '330k', '360k', '390k', '430k', '470k', '510k',
                           '560k', '620k', '680k', '750k', '820k', '910k', '1000k',
                           '1100k', '1200k', '1300k', '1500k', '1600k', '1800k', '2200k',
                           '2400k', '2700k',
                           '3000k', '3300k', '3600k', '3900k', '4300k', '4700k', '5100k',
                           '5600k', '6200k', '6800k', '7500k', '8200k', '9100k', '10000k',
                           '11000k', '12000k', '13000k', '15000k', '16000k', '18000k', '20000k']
            return Rb_valueMap[pos[0][0]], Rb_value
        else:
            raise ValueError('gain mast be -20~20dB')

    def set_op2_default_data(self):
        r_notch = R_value2map_2(self.default_notch_r_value)
        r_notch_half = R_value2map_2(self.default_notch_r_value * 0.5)
        r_peak = R_value2map_2(self.default_peak_r_value)
        r_peak_half = R_value2map_2(self.default_peak_r_value * 0.5)
        r_peak_double = R_value2map_2(self.default_peak_r_value * 2)
        r_peak_shelf = R_value2map_2(self.default_peak_r_value * 11)
        r_op_gain = R_value2map_2(self.default_op_gain_r_value)

        self.two_order_filter_data_11 = dict(C1_value='22n', C2_value='22n', C_value_double='47n', R1_value=r_notch,
                                          R2_value=r_notch, R_half_value=r_notch_half, R_gain_value=0)
        self.two_order_filter_data_12 = dict(C1_value='22n', C2_value='22n', C_value_double='47n', R1_value=r_notch,
                                          R2_value=r_notch, R_half_value=r_notch_half, R_gain_value=0)
        self.one_order_highpass_data_2 = dict(C_value='22n', R_value=r_notch)
        self.one_order_lowpass_data_2 = dict(C_value='22n', R_value=r_notch)

        self.op_gain_data_2 = dict(Ra_value=r_op_gain, Rb_value=r_op_gain)
        self.op_lowpass_data_2 = dict(C_value='4.7n')

        self.high_shelf_data_2 = dict(C_value='470p', R_value=r_peak_shelf)
        self.low_shelf_data_2 = dict(C_value='470p', R_value=r_peak_shelf)
        self.op_peak_data_2 = dict(C1_value='8.2n', C2_value='8.2n', C_value_double='15n', R1_value=r_peak,
                                 R2_value=r_peak, R_half_value=r_peak_half, R_gain_value=0, R_high_cut=r_peak_double)
        self.two_order_lowpass_data_2 = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                                             C2_value='12n')

        # 默认module11参数
        self.pixmapLabel_4.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
        self.amplitudeSlider_4.setHidden(True)
        self.frequencySpin_4.setHidden(True)
        self.frequencySpin_highpass_2.setHidden(True)
        self.label_Slider_value_14.setText('None')
        # 默认module12参数
        self.pixmapLabel_3.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
        self.amplitudeSlider_3.setHidden(True)
        self.frequencySpin_3.setHidden(True)
        self.frequencySpin_lowpass_2.setHidden(True)
        self.label_Slider_value_5.setText('None')
        # 默认module13参数
        self.label_24.setPixmap(QtGui.QPixmap(':/mic/icon/lowpass.png'))
        # module 08 peak filter参数
        self.label_26.setPixmap(QtGui.QPixmap(':/mic/icon/peak.png'))

    def set_op2_default_module(self):
        self.module11 = 'bypass'
        self.module12 = 'bypass'
        self.module13 = 'op_one_order'
        self.module14 = None
        self.module15 = None
        self.module16 = None
        self.module17 = None

        self.notch11_status = False  # 手动调整增益开关
        self.notch12_status = False
        self.peak17_status = False
        self.two_order_lowpass_18_status = False

    def set_op2_signals_slots(self):
        """
        UI界面信号与槽连接
        :return:
        """

        # filter_11模块单元按键
        self.filter01_radioButton_notch_4.toggled.connect(
            lambda: self.set_module_11(self.filter01_radioButton_notch_4))  # 功能复选框
        self.filter01_radioButton_bypass_4.toggled.connect(
            lambda: self.set_module_11(self.filter01_radioButton_bypass_4))
        self.filter01_radioButton_highpass_2.toggled.connect(
            lambda: self.set_module_11(self.filter01_radioButton_highpass_2))
        self.frequencySpin_4.valueChanged.connect(self.setupC_value_11)  # 计数器改变时调整电容值
        self.amplitudeSlider_4.valueChanged.connect(self.setupR_value_11)  # 滑块位置改变时调整电阻值
        self.frequencySpin_highpass_2.valueChanged.connect(self.setupC_value_highpass_11)  # 高通电容调整信号槽

        # filter_12模块单元按键
        self.filter01_radioButton_notch_3.toggled.connect(
            lambda: self.set_module_12(self.filter01_radioButton_notch_3))  # 功能复选框
        self.filter01_radioButton_bypass_3.toggled.connect(
            lambda: self.set_module_12(self.filter01_radioButton_bypass_3))
        self.filter01_radioButton_lowpass_2.toggled.connect(
            lambda: self.set_module_12(self.filter01_radioButton_lowpass_2))
        self.frequencySpin_3.valueChanged.connect(self.setupC_value_12)  # 计数器改变时调整电容值
        self.amplitudeSlider_3.valueChanged.connect(self.setupR_value_12)  # 滑块位置改变时调整电阻值
        self.frequencySpin_lowpass_2.valueChanged.connect(self.setupC_value_lowpass_12)  # 低通电容调整信号槽

        # OP2增益模块
        self.OP_lowpass_filter_enable_2.toggled.connect(self.set_module_13)
        self.OP_lowpass_order_radio_one_2.toggled.connect(self.set_module_13)  # 设置1阶/2阶模式
        self.OP_lowpass_order_radio_chebyshev_2.toggled.connect(self.set_module_13)
        self.OP_gain_spin_2.valueChanged.connect(self.set_module_13)  # 设置Rb电阻阻值
        self.OP_gain_spin_2.valueChanged.connect(self.set_module_14)  # 控制module14参数
        self.OP_gain_spin_2.valueChanged.connect(self.set_module_15)  # 控制module15参数
        self.OP_gain_spin_2.valueChanged.connect(self.set_module_17)  # 控制module17参数

        # high shelf
        self.OP_highshelf_filter_enable_2.toggled.connect(self.set_module_14)
        self.high_shelf_gain_spin_2.valueChanged.connect(self.set_module14_data)
        self.high_shelf_frequency_spin_2.valueChanged.connect(self.set_module14_data)
        # low shelf
        self.OP_lowshelf_filter_enable_2.toggled.connect(self.set_module_15)
        self.low_shelf_gain_spin_2.valueChanged.connect(self.setup_module15_data)
        self.low_shelf_frequency_spin_2.valueChanged.connect(self.setup_module15_data)
        # op low pass
        self.frequencySpin_OP_lowpass_2.valueChanged.connect(self.set_module_16_data)

        # op peak
        self.OP_peak_filter_enable_2.toggled.connect(self.set_module_17)
        self.peak_frequency_spin_2.valueChanged.connect(self.set_module_17_data)
        self.peak_gain_spin_2.valueChanged.connect(self.set_module_17_data)
        self.peak_lowpass_slider_2.valueChanged.connect(self.set_module_17_data)
        self.peak_attenuation_slider_2.valueChanged.connect(self.set_module_17_data)

        # two order lowpass
        self.OP_lowpass_order_radio_bessel_2.toggled.connect(self.set_module_18)
        self.OP_lowpass_order_radio_butterworth_2.toggled.connect(self.set_module_18)
        self.OP_lowpass_order_radio_chebyshev_2.toggled.connect(self.set_module_18)
        self.chebyshev_1dB_4.toggled.connect(self.set_module_18)
        self.chebyshev_1dB_5.toggled.connect(self.set_module_18)
        self.chebyshev_1dB_6.toggled.connect(self.set_module_18)
        self.frequencySpin_OP_lowpass_2.valueChanged.connect(self.set_module_18)

        self.btn_notch11_tuning.clicked.connect(self.notch11_tuning)  # tuning
        self.btn_notch12_tuning.clicked.connect(self.notch12_tuning)
        self.btn_peak17_tuning.clicked.connect(self.peak17_tuning)
        self.btn_two_order_lowpass_tuning_2.clicked.connect(self.two_order_lowpass_tuning_2)

    # module11模块参数设置
    def setupC_value_11(self):
        """
        根据选择的中心频率设置电容容值
        """
        f = self.frequencySpin_4.value()  # 用户设置频率数值
        c_value = 1 / (2 * np.pi * self.default_notch_r_value * f)  # 默认电阻2.2k，c_value为浮点进度数值
        self.two_order_filter_data_11['C1_value'] = c_value2map(c_value)  # E12电容标准取值，str格式,ex:33nf
        self.two_order_filter_data_11['C2_value'] = c_value2map(c_value)
        self.two_order_filter_data_11['C_value_double'] = c_value2map_dubble(c_value)  # 接地电容取并联值，str格式,ex:66nf
        # print(self.two_order_filter_data_11.items())#接地电容容值

    def setupR_value_11(self):
        """
        根据幅值滑块位置设置幅值调整电阻阻值
        :return:
        """
        v = self.amplitudeSlider_4.value()
        self.two_order_filter_data_11['R_gain_value'] = get_R_value(v)

        self.label_Slider_value_14.setText(self.two_order_filter_data_11['R_gain_value'])  # 设置UI界面label显示数值

    def set_module_11(self, btn):
        """设置module11工作模式
        :param btn:三种模式选择按键
        :return:self.module11参数调整
        """
        if btn.text() == '带阻' and btn.isChecked():
            self.module11 = 'notch'
            self.amplitudeSlider_4.setHidden(False)  # UI界面调整
            self.frequencySpin_4.setHidden(False)
            self.frequencySpin_highpass_2.setHidden(True)
            if self.notch11_status:
                self.pixmapLabel_4.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            else:
                self.pixmapLabel_4.setPixmap(QtGui.QPixmap(':/mic/icon/Filter.png'))
        if btn.text() == '直通' and btn.isChecked():
            self.pixmapLabel_4.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
            self.module11 = 'bypass'
            self.amplitudeSlider_4.setHidden(True)
            self.frequencySpin_4.setHidden(True)
            self.frequencySpin_highpass_2.setHidden(True)
            self.label_Slider_value_14.setText('None')
        if btn.text() == '高通' and btn.isChecked():
            self.pixmapLabel_4.setPixmap(QtGui.QPixmap(":/mic/icon/HighPass.png"))
            self.module11 = 'highpass'
            self.amplitudeSlider_4.setHidden(True)
            self.frequencySpin_4.setHidden(True)
            self.frequencySpin_highpass_2.setHidden(False)
            self.label_Slider_value_14.setText('None')

    def setupC_value_highpass_11(self):
        """根据选择的中心频率设置电容容值"""
        f = self.frequencySpin_highpass_2.value()  # 用户设置频率数值
        c_value = 1 / (2 * np.pi * self.default_notch_r_value * f)  # 默认电阻2.2k，c_value为浮点进度数值
        self.one_order_highpass_data_2['C_value'] = c_value2map(c_value)  # E12电容标准取值，str格式,ex:33nf
        # print(self.one_order_highpass_data_2.items())

    # module12模块参数设置
    def setupC_value_12(self):

        f = self.frequencySpin_3.value()  # 用户设置频率数值
        c_value = 1 / (2 * np.pi * self.default_notch_r_value * f)  # 默认电阻2.2k，c_value为浮点进度数值
        self.two_order_filter_data_12['C1_value'] = c_value2map(c_value)  # E12电容标准取值，str格式,ex:33nf
        self.two_order_filter_data_12['C2_value'] = c_value2map(c_value)
        self.two_order_filter_data_12['C_value_double'] = c_value2map_dubble(c_value)  # 接地电容取并联值，str格式,ex:66nf

    def setupR_value_12(self):

        v = self.amplitudeSlider_3.value()
        self.two_order_filter_data_12['R_gain_value'] = get_R_value(v)
        self.label_Slider_value_5.setText(self.two_order_filter_data_12['R_gain_value'])  # 设置UI界面label显示数值
        # print(self.two_order_filter_data_12.items())  # 接地电容容值

    def set_module_12(self, btn):

        if btn.text() == '带阻' and btn.isChecked():
            self.module12 = 'notch'
            self.amplitudeSlider_3.setHidden(False)  # UI界面调整
            self.frequencySpin_3.setHidden(False)
            self.frequencySpin_lowpass_2.setHidden(True)
            if self.notch12_status:
                self.pixmapLabel_3.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            else:
                self.pixmapLabel_3.setPixmap(QtGui.QPixmap(':/mic/icon/Filter.png'))
        if btn.text() == '直通' and btn.isChecked():
            self.pixmapLabel_3.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
            self.module12 = 'bypass'
            self.amplitudeSlider_3.setHidden(True)
            self.frequencySpin_3.setHidden(True)
            self.frequencySpin_lowpass_2.setHidden(True)
            self.label_Slider_value_5.setText('None')
        if btn.text() == '低通' and btn.isChecked():
            self.pixmapLabel_3.setPixmap(QtGui.QPixmap(':/mic/icon/lowpass.png'))
            self.module12 = 'lowpass'
            self.amplitudeSlider_3.setHidden(True)
            self.frequencySpin_3.setHidden(True)
            self.frequencySpin_lowpass_2.setHidden(False)
            self.label_Slider_value_5.setText('None')

    def setupC_value_lowpass_12(self):
        """根据选择的中心频率设置电容容值"""
        f = self.frequencySpin_lowpass_2.value()  # 用户设置频率数值
        c_value = 1 / (2 * np.pi * self.default_notch_r_value * f)  # 默认电阻2.2k，c_value为浮点进度数值
        self.one_order_lowpass_data_2['C_value'] = c_value2map(c_value)  # E12电容标准取值，str格式,ex:33nf

    # module 13
    def set_module_13(self):
        if self.OP_lowpass_filter_enable_2.isChecked():  # module 16 on
            self.OP_lowshelf_filter_enable_2.setChecked(False)  # 关闭 module 15
            self.OP_peak_filter_enable_2.setChecked(False)  # 关闭 module 17
            self.groupBox_15.setEnabled(True)
            if self.OP_lowpass_order_radio_one_2.isChecked():  # 1阶
                self.label_25.setEnabled(True)  # 启用module16低通模块
                self.frequencySpin_OP_lowpass_2.setEnabled(True)
                self.set_module_16()
            else:  # 2阶
                self.set_module_18()

        else:  # module 06 off
            self.groupBox_18.setEnabled(True)  # 启用low shelf, high shelf, peak
            self.groupBox_13.setEnabled(True)
            self.groupBox_12.setEnabled(True)
            self.label_25.setEnabled(False)  # 停用module16 低通模块
            self.frequencySpin_OP_lowpass_2.setEnabled(False)
            self.groupBox_15.setEnabled(False)
            self.groupBox_16.setEnabled(False)
            self.groupBox_17.setEnabled(False)

            self.module16 = None
            self.module13 = 'op_one_order'
            if self.OP_lowshelf_filter_enable_2.isChecked():  # 关闭module13时根据判断重置Rb值,防止module15打开状态误调Rb
                pass
            else:
                self.set_module13_data()

    def set_module13_data(self):
        gain = self.OP_gain_spin_2.value()
        if self.OP_lowshelf_filter_enable_2.isChecked():  # 限制low shelf最低增益
            self.low_shelf_gain_spin_2.setMinimum(gain)
        if self.OP_highshelf_filter_enable_2.isChecked():  # 限制high shelf最低增益
            self.high_shelf_gain_spin_2.setMinimum(gain)

        self.op_gain_data_2['Rb_value'] = self.get_Rb_value(gain)[0]

    # module 14 high shelf
    def set_module_14(self):
        if self.OP_highshelf_filter_enable_2.isChecked():
            self.high_shelf_frequency_spin_2.setEnabled(True)  # 启用gain及frequency调整
            self.high_shelf_gain_spin_2.setEnabled(True)
            self.label_20.setEnabled(True)
            self.label_Slider_value_9.setEnabled(True)
            self.high_shelf_gain_spin_2.setMinimum(self.OP_gain_spin_2.value())  # 重置最小增益
            self.set_module14_data()
        else:
            self.high_shelf_frequency_spin_2.setEnabled(False)  # 停用gain及frequency调整
            self.high_shelf_gain_spin_2.setEnabled(False)
            self.label_20.setEnabled(False)
            self.label_Slider_value_9.setEnabled(False)
            self.module14 = None  # 设置模式

    def set_module14_data(self):
        gain = self.high_shelf_gain_spin_2.value()
        gain_op = self.OP_gain_spin_2.value()
        if gain - gain_op > 0:
            R1 = self.default_op_gain_r_value / (10 ** ((gain - gain_op) / 20) - 1)  # 反相放大器增益计算法
            self.high_shelf_data_2['R_value'] = R_value2map(R1)

            f = self.high_shelf_frequency_spin_2.value()
            c_value = 1 / (2 * np.pi * R1 * f)
            self.high_shelf_data_2['C_value'] = c_value2map(c_value)
            if self.OP_highshelf_filter_enable_2.isChecked():
                self.module14 = 'high_shelf'
        else:
            self.module14 = None

    # module 15 low shelf
    def set_module_15(self):
        if self.OP_lowshelf_filter_enable_2.isChecked():
            self.low_shelf_frequency_spin_2.setEnabled(True)  # 启用gain及frequency调整
            self.low_shelf_gain_spin_2.setEnabled(True)
            self.label_22.setEnabled(True)
            self.label_Slider_value_10.setEnabled(True)
            self.low_shelf_gain_spin_2.setMinimum(self.OP_gain_spin_2.value())  # 重置最小增益
            self.OP_gain_spin_2.setMinimum(0)  # 限制op gain最小增益
            self.OP_lowpass_filter_enable_2.setChecked(False)  # 关闭 module13
            self.OP_peak_filter_enable_2.setChecked(False)  # 关闭 module 07
            self.setup_module15_data()
        else:
            self.low_shelf_frequency_spin_2.setEnabled(False)  # 关闭gain及frequency调整
            self.low_shelf_gain_spin_2.setEnabled(False)
            self.label_22.setEnabled(False)
            self.label_Slider_value_10.setEnabled(False)
            self.module15 = None
            self.set_module13_data()  # 交还OP_R_value控制权
            self.OP_gain_spin_2.setMinimum(-10)  # 重置op gain最小增益

    def setup_module15_data(self):
        gain2 = self.low_shelf_gain_spin_2.value()
        gain_op = self.OP_gain_spin_2.value()
        if gain2 - gain_op > 0:
            Rb = self.default_op_gain_r_value * (10 ** (gain2 / 20))  # Rb_value 阻值计算
            R2 = self.default_op_gain_r_value * (10 ** ((gain2 + gain_op) / 20) / (
                    10 ** (gain2 / 20) - 10 ** (gain_op / 20)))  # low shelf R_value 阻值计算
            self.op_gain_data_2['Rb_value'] = R_value2map(Rb)
            self.low_shelf_data_2['R_value'] = R_value2map(R2)

            f = self.low_shelf_frequency_spin_2.value()
            c_value = 1 / (2 * np.pi * R2 * f)
            self.low_shelf_data_2['C_value'] = c_value2map(c_value)
            if self.OP_lowshelf_filter_enable_2.isChecked():
                self.module15 = 'low_shelf'
        else:
            self.module15 = None
            self.set_module13_data()

    # module 16 op lowpass
    def set_module_16(self):
        self.groupBox_16.setEnabled(False)
        self.groupBox_17.setEnabled(False)
        self.groupBox_18.setEnabled(True)  # 启用low shelf, high shelf, peak
        self.groupBox_13.setEnabled(True)
        self.groupBox_12.setEnabled(True)
        self.label_24.setPixmap(QtGui.QPixmap(':/mic/icon/lowpass.png'))
        self.module13 = 'op_one_order'
        self.module16 = 'op_lowpass'
        self.set_module_16_data()

    def set_module_16_data(self):
        gain = self.OP_gain_spin_2.value()
        f = self.frequencySpin_OP_lowpass_2.value()
        r_value = self.get_Rb_value(gain)[1]
        c_value = 1 / (2 * np.pi * r_value * f)
        self.op_lowpass_data_2['C_value'] = c_value2map(c_value)

    # op peak module 17
    def set_module_17(self):
        if self.sender() == self.OP_gain_spin_2 and not self.OP_peak_filter_enable_2.isChecked():
            self.op2_gain = self.OP_gain_spin_2.value()  # 记录op gain

        if self.OP_peak_filter_enable_2.isChecked():
            self.OP_lowpass_filter_enable_2.setChecked(False)  # 关闭 module13
            self.OP_lowshelf_filter_enable_2.setChecked(False)  # 关闭 module 05
            self.peak_gain_spin_2.setValue(self.peak02_gain)  # gain设置为记录值
            self.OP_gain_spin_2.setEnabled(False)
            self.set_module_17_data()
            if self.peak17_status is False:
                self.label_Slider_value_11.setEnabled(True)
                self.peak_attenuation_slider_2.setEnabled(True)
                self.label_Slider_value_12.setEnabled(True)
                self.peak_lowpass_slider_2.setEnabled(True)
                self.label_Slider_value_13.setEnabled(True)
                self.peak_gain_spin_2.setEnabled(True)
                self.label_27.setEnabled(True)
                self.peak_frequency_spin_2.setEnabled(True)
            else:
                self.label_Slider_value_11.setEnabled(False)
                self.peak_attenuation_slider_2.setEnabled(False)
                self.label_Slider_value_12.setEnabled(False)
                self.peak_lowpass_slider_2.setEnabled(False)
                self.label_Slider_value_13.setEnabled(False)
                self.peak_gain_spin_2.setEnabled(False)
                self.label_27.setEnabled(False)
                self.peak_frequency_spin_2.setEnabled(False)
        else:
            self.label_Slider_value_11.setEnabled(False)
            self.peak_attenuation_slider_2.setEnabled(False)
            self.label_Slider_value_12.setEnabled(False)
            self.peak_lowpass_slider_2.setEnabled(False)
            self.label_Slider_value_13.setEnabled(False)
            self.peak_gain_spin_2.setEnabled(False)
            self.label_27.setEnabled(False)
            self.peak_frequency_spin_2.setEnabled(False)
            self.OP_gain_spin_2.setEnabled(True)

            self.module17 = None
            if self.sender() == self.OP_peak_filter_enable_2:
                self.OP_gain_spin_2.setValue(self.op2_gain)  # 恢复记录值

    def set_module_17_data(self):
        self.peak02_gain = self.peak_gain_spin_2.value()  # 记录peak01 gain
        self.OP_gain_spin_2.setValue(self.peak_gain_spin_2.value())  # 同步op gain & peak gain

        gain = self.peak_gain_spin_2.value()
        f = self.peak_frequency_spin_2.value()
        pos_r_high = self.peak_lowpass_slider_2.value()
        pos_r_gain = self.peak_attenuation_slider_2.value()
        if self.peak17_status is False:
            if gain == 0:
                self.module17 = None
            else:
                Rb = self.get_Rb_value(gain)[1]
                R1 = self.default_peak_r_value * Rb / (Rb - self.default_peak_r_value) / 2
                c_value = 1 / (1.414 * np.pi * R1 * f)  # 中心频率有1.414倍偏移
                R3 = 2 * R1
                r_high_cut = R3 / (R3 ** (pos_r_high / 61))

                self.op_peak_data_2['R1_value'] = R_value2map(R1)
                self.op_peak_data_2['R2_value'] = R_value2map(R1)
                self.op_peak_data_2['R_half_value'] = R_value2map(R1 / 2)
                self.op_peak_data_2['C1_value'] = c_value2map(c_value)
                self.op_peak_data_2['C2_value'] = c_value2map(c_value)
                self.op_peak_data_2['C_value_double'] = c_value2map_dubble(c_value)
                self.op_peak_data_2['R_gain_value'] = get_R_value(pos_r_gain)
                self.op_peak_data_2['R_high_cut'] = R_value2map_2(r_high_cut)
                if self.OP_peak_filter_enable_2.isChecked():
                    self.module17 = 'peak'
        else:
            if self.OP_peak_filter_enable_2.isChecked():
                self.module17 = 'peak'

    # module 18 two order lowpass
    def set_module_18(self):
        if self.OP_lowpass_filter_enable_2.isChecked() and self.OP_lowpass_order_radio_two_2.isChecked():

            self.OP_lowshelf_filter_enable_2.setChecked(False)  # 关闭low shelf,high shelf,peak
            self.OP_highshelf_filter_enable_2.setChecked(False)
            self.OP_peak_filter_enable_2.setChecked(False)
            self.groupBox_18.setEnabled(False)
            self.groupBox_13.setEnabled(False)
            self.groupBox_12.setEnabled(False)

            self.module13 = 'op_two_order'
            self.module16 = None

            if self.two_order_lowpass_18_status is False:
                self.groupBox_16.setEnabled(True)  # 二阶类型选择框
                self.frequencySpin_OP_lowpass_2.setEnabled(True)
                self.label_25.setEnabled(True)
                if self.OP_lowpass_order_radio_bessel_2.isChecked():
                    self.groupBox_17.setEnabled(False)
                    module18 = 'bessel'
                elif self.OP_lowpass_order_radio_butterworth_2.isChecked():
                    self.groupBox_17.setEnabled(False)
                    module18 = 'butterworth'
                else:
                    self.groupBox_17.setEnabled(True)
                    if self.chebyshev_1dB_4.isChecked():
                        module18 = 'chebyshev-1'
                    elif self.chebyshev_1dB_5.isChecked():
                        module18 = 'chebyshev-2'
                    else:
                        module18 = 'chebyshev-3'
                self.label_24.setPixmap(QtGui.QPixmap(':/mic/icon/lowpass.png'))
                self.set_module_18_data(module18)
            else:
                self.label_24.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
                self.groupBox_16.setEnabled(False)
                self.groupBox_17.setEnabled(False)
                self.frequencySpin_OP_lowpass_2.setEnabled(False)
                self.label_25.setEnabled(False)
        else:
            pass

    def set_module_18_data(self, module=None):

        gain = self.OP_gain_spin_2.value()
        f = self.frequencySpin_OP_lowpass_2.value()
        C1 = 4.7e-3
        k = 100 / (f * C1)
        R2 = 1.306e3
        R1 = R2 / (10 ** (gain / 20))
        R3 = R1 * R2 / (R1 + R2)
        num = [-764.6, 0, 1.111e5]  # 构造根据gain获得C2电容值传递函数
        den = [1, 0, 1528]
        Gd = control.tf(num, den)
        x = list(range(21))
        y = control.frd(Gd, x)
        C = float(y.eval(gain).real)

        if module == 'bessel':
            K = k * 1
            r1 = R1 * K
            r2 = R2 * K
            r3 = R3 * K
            C2 = C * 13 / 68 * 1e-9
            self.two_order_lowpass_data_2['R1_value'] = R_value2map_2(r1)
            self.two_order_lowpass_data_2['R2_value'] = R_value2map_2(r2)
            self.two_order_lowpass_data_2['R3_value'] = R_value2map_2(r3)
            self.two_order_lowpass_data_2['C2_value'] = c_value2map(C2)
        elif module == 'butterworth':
            K = k * 0.9
            r1 = R1 * K
            r2 = R2 * K
            r3 = R3 * K
            C2 = C * 18 / 68 * 1e-9
            self.two_order_lowpass_data_2['R1_value'] = R_value2map_2(r1)
            self.two_order_lowpass_data_2['R2_value'] = R_value2map_2(r2)
            self.two_order_lowpass_data_2['R3_value'] = R_value2map_2(r3)
            self.two_order_lowpass_data_2['C2_value'] = c_value2map(C2)
        elif module == 'chebyshev-1':
            K = k * 0.85
            r1 = R1 * K
            r2 = R2 * K
            r3 = R3 * K
            C2 = C * 24 / 68 * 1e-9
            self.two_order_lowpass_data_2['R1_value'] = R_value2map_2(r1)
            self.two_order_lowpass_data_2['R2_value'] = R_value2map_2(r2)
            self.two_order_lowpass_data_2['R3_value'] = R_value2map_2(r3)
            self.two_order_lowpass_data_2['C2_value'] = c_value2map(C2)
        elif module == 'chebyshev-2':
            K = k * 0.8
            r1 = R1 * K
            r2 = R2 * K
            r3 = R3 * K
            C2 = C * 50 / 68 * 1e-9
            self.two_order_lowpass_data_2['R1_value'] = R_value2map_2(r1)
            self.two_order_lowpass_data_2['R2_value'] = R_value2map_2(r2)
            self.two_order_lowpass_data_2['R3_value'] = R_value2map_2(r3)
            self.two_order_lowpass_data_2['C2_value'] = c_value2map(C2)
        elif module == 'chebyshev-3':
            K = k * 0.75
            r1 = R1 * K
            r2 = R2 * K
            r3 = R3 * K
            C2 = C * 1e-9
            self.two_order_lowpass_data_2['R1_value'] = R_value2map_2(r1)
            self.two_order_lowpass_data_2['R2_value'] = R_value2map_2(r2)
            self.two_order_lowpass_data_2['R3_value'] = R_value2map_2(r3)
            self.two_order_lowpass_data_2['C2_value'] = c_value2map(C2)
        else:
            pass

    # tuning
    # module 11
    def set_notch11_parameter(self, data, status):
        """根据tuning对话框返回值设置参数及UI界面"""
        self.notch11_status = status
        if status:
            self.amplitudeSlider_4.setEnabled(False)
            self.label_28.setEnabled(False)
            self.label_29.setEnabled(False)
            self.frequencySpin_4.setEnabled(False)
            self.btn_notch11_tuning.setDefault(True)  # 按键标记

            self.two_order_filter_data_11 = data
            if self.filter01_radioButton_notch_4.isChecked():
                self.pixmapLabel_4.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            elif self.filter01_radioButton_bypass_4.isChecked():
                self.pixmapLabel_4.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
            else:
                self.pixmapLabel_4.setPixmap(QtGui.QPixmap(":/mic/icon/HighPass.png"))

        else:
            r_notch = R_value2map_2(self.default_notch_r_value)
            r_notch_half = R_value2map_2(self.default_notch_r_value * 0.5)
            self.amplitudeSlider_4.setEnabled(True)
            self.label_28.setEnabled(True)
            self.label_29.setEnabled(True)
            self.frequencySpin_4.setEnabled(True)
            self.btn_notch11_tuning.setDefault(False)  # 取消按键标记

            self.two_order_filter_data_11 = dict(C1_value='22n', C2_value='22n', C_value_double='47n', R1_value=r_notch,
                                              R2_value=r_notch, R_half_value=r_notch_half, R_gain_value=0)
            self.setupC_value_11()  # 重新设置阻容参数
            self.setupR_value_11()
            if self.filter01_radioButton_notch_4.isChecked():
                self.pixmapLabel_4.setPixmap(QtGui.QPixmap(':/mic/icon/Filter.png'))
            elif self.filter01_radioButton_bypass_4.isChecked():
                self.pixmapLabel_4.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
            else:
                self.pixmapLabel_4.setPixmap(QtGui.QPixmap(":/mic/icon/HighPass.png"))

    def notch11_tuning(self):
        dialog = MyNotchFilterTuningDialog(self.two_order_filter_data_11, self.notch11_status)
        dialog.signal.connect(self.set_notch11_parameter)
        dialog.exec_()
        # print('对话框结束01', self.two_order_filter_data_11, self.notch11_status)

    # module 12
    def set_notch12_parameter(self, data, status):
        """根据tuning对话框返回值设置参数及UI界面"""
        self.notch12_status = status
        if status:
            self.amplitudeSlider_3.setEnabled(False)
            self.label_5.setEnabled(False)
            self.label_18.setEnabled(False)
            self.frequencySpin_3.setEnabled(False)
            self.btn_notch12_tuning.setDefault(True)  # 按键标记

            self.two_order_filter_data_12 = data
            if self.filter01_radioButton_notch_3.isChecked():
                self.pixmapLabel_3.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            elif self.filter01_radioButton_bypass_3.isChecked():
                self.pixmapLabel_3.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
            else:
                self.pixmapLabel_3.setPixmap(QtGui.QPixmap(":/mic/icon/HighPass.png"))
        else:
            r_notch = R_value2map_2(self.default_notch_r_value)
            r_notch_half = R_value2map_2(self.default_notch_r_value * 0.5)
            self.amplitudeSlider_3.setEnabled(True)
            self.label_5.setEnabled(True)
            self.label_18.setEnabled(True)
            self.frequencySpin_3.setEnabled(True)
            self.btn_notch12_tuning.setDefault(False)  # 取消按键标记

            self.two_order_filter_data_12 = dict(C1_value='22n', C2_value='22n', C_value_double='47n', R1_value=r_notch,
                                              R2_value=r_notch, R_half_value=r_notch_half, R_gain_value=0)
            self.setupC_value_12()  # 重新设置阻容参数
            self.setupR_value_12()
            if self.filter01_radioButton_notch_3.isChecked():
                self.pixmapLabel_3.setPixmap(QtGui.QPixmap(':/mic/icon/Filter.png'))
            elif self.filter01_radioButton_bypass_3.isChecked():
                self.pixmapLabel_3.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
            else:
                self.pixmapLabel_3.setPixmap(QtGui.QPixmap(":/mic/icon/HighPass.png"))

    def notch12_tuning(self):
        dialog = MyNotchFilterTuningDialog(self.two_order_filter_data_12, self.notch12_status)
        dialog.signal.connect(self.set_notch12_parameter)
        dialog.exec_()
        # print('对话框结束02', self.two_order_filter_data_12, self.notch11_status)

    # peak 17
    def set_peak17_parameter(self, data, status):
        """根据tuning对话框返回值设置参数及UI界面"""
        self.peak17_status = status
        if status:
            self.btn_peak17_tuning.setDefault(True)  # 按键标记
            self.label_26.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            self.set_module_17()
            self.op_peak_data_2 = data
        else:
            r_peak = R_value2map_2(self.default_peak_r_value)
            r_peak_half = R_value2map_2(self.default_peak_r_value * 0.5)
            r_peak_double = R_value2map_2(self.default_peak_r_value * 2)
            self.btn_peak17_tuning.setDefault(False)  # 按键标记
            self.label_26.setPixmap(QtGui.QPixmap(':/mic/icon/peak.png'))
            self.op_peak_data_2 = dict(C1_value='8.2n', C2_value='8.2n', C_value_double='15n', R1_value=r_peak,
                                 R2_value=r_peak, R_half_value=r_peak_half, R_gain_value=0, R_high_cut=r_peak_double)
            self.set_module_17()

    def peak17_tuning(self):
        dialog = MyPeakFilterTuningDialog(self.op_peak_data_2, self.peak17_status)
        dialog.signal.connect(self.set_peak17_parameter)
        dialog.exec_()

    # two order lowpass 18
    def set_two_order_lowpass_parameter_2(self, data, status):
        """根据二阶tuning对话框返回值设置参数及UI界面"""
        self.two_order_lowpass_18_status = status
        if status:
            # self.label_25.setEnabled(False)
            # self.frequencySpin_OP_lowpass_2.setEnabled(False)
            # self.groupBox_16.setEnabled(False)
            # self.groupBox_17.setEnabled(False)
            self.btn_two_order_lowpass_tuning_2.setDefault(True)  # 按键标记
            self.set_module_18()
            self.two_order_lowpass_data_2 = data
        else:
            self.btn_two_order_lowpass_tuning_2.setDefault(False)  # 取消按键标记
            self.two_order_lowpass_data_2 = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                                                 C2_value='12n')
            self.set_module_18()

    def two_order_lowpass_tuning_2(self):
        dialog = MyTwoOrderLowpassTuningDialog(self.two_order_lowpass_data_2, self.two_order_lowpass_18_status)
        dialog.signal.connect(self.set_two_order_lowpass_parameter_2)
        dialog.exec_()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myWin = SetOp2Window()
    myWin.show()
    sys.exit(app.exec_())
