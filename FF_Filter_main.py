#!/usr/bin/env python
# -*- coding:utf-8 -*-
import math
import sys

import control
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QSettings

from main_UI import Ui_MainWindow  # 导入UI
# 导入私有模块
from get_capacitance_value import c_value2map, c_value2map_dubble  # 计数器to电容容值
from get_resistance_value import get_R_value, get_Rb_value, R_value2map, R_value2map_2  # 滑块数值to电阻阻值
from includes.my_ANC_excel_read import My_ANC_ExcelRead  # excel模板读取类
from includes.my_filter_simulator import MyFilterSimulator  # netlist仿真计算机绘图类
from includes.my_netlist_create import MyNetlistCreate  # 根据UI界面参数创建电路图
from value_tuning.notch_tuning_main import MyNotchFilterTuningDialog
from value_tuning.peak_tuning_main import MyPeakFilterTuningDialog
from value_tuning.two_order_lowpass_tuning_main import MyTwoOrderLowpassTuningDialog


class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """FF_Filter设计主运行程序
    1.用Subcircuit拼装电路
    2.参考曲线导入及仿真计算跟notchFilter2cir方法相同
    """

    def __init__(self, parent=None):

        super(MyWindow, self).__init__(parent)
        self.setupUi(self)
        # self.showMaximized() # 窗口最大化显示
        self.set_default_data()
        self.set_default_module()
        self.signals_slot()

    def set_default_data(self):

        self.aim_curve_data = None  # 默认参考曲线参数

        self.mic_op_gain_data = dict(Ra_value=22000, Rb_value=0)
        self.two_order_filter_data = dict(C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k',
                                          R2_value='2.2k', R_half_value='1.1k', R_gain_value=0)
        self.two_order_filter_data_02 = dict(C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k',
                                             R2_value='2.2k', R_half_value='1.1k', R_gain_value=0)
        self.one_order_highpass_data = dict(C_value='68n', R_value='2.2k')
        self.one_order_lowpass_data = dict(C_value='68n', R_value='2.2k')

        self.op_gain_data = dict(Ra_value='20k', Rb_value='20k')
        self.op_lowpass_data = dict(C_value='8.2n')

        self.high_shelf_data = dict(C_value='680p', R_value='220k')
        self.low_shelf_data = dict(C_value='680p', R_value='220k')
        self.op_peak_data = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k', R2_value='20k',
                                 R_half_value='10k', R_gain_value=0, R_high_cut='39k')
        self.two_order_lowpass_data = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                                           C2_value='12n')

        # 默认module01参数
        self.pixmapLabel.setPixmap(QtGui.QPixmap('./icon/Bypass.png'))
        self.amplitudeSlider.setHidden(True)
        self.frequencySpin.setHidden(True)
        self.frequencySpin_highpass.setHidden(True)
        self.label_Slider_value.setText('None')
        # 默认module02参数
        self.pixmapLabel_2.setPixmap(QtGui.QPixmap('./icon/Bypass.png'))
        self.amplitudeSlider_2.setHidden(True)
        self.frequencySpin_2.setHidden(True)
        self.frequencySpin_lowpass.setHidden(True)
        self.label_Slider_value_2.setText('None')
        # 默认module03参数
        self.label_15.setPixmap(QtGui.QPixmap(':/mic/icon/lowpass.png'))
        # module 08 peak filter参数
        self.label_11.setPixmap(QtGui.QPixmap(':/mic/icon/peak.png'))

    def set_default_module(self):
        self.module01 = 'bypass'
        self.module02 = 'bypass'
        self.module03 = 'op_one_order'
        self.module04 = None
        self.module05 = None
        self.module06 = None
        self.module07 = None

        self.notch01_status = False  # 手动调整增益开关
        self.notch02_status = False
        self.peak01_status = False
        self.two_order_lowpass_status = False

    def signals_slot(self):
        """
        UI界面信号与槽连接
        :return:
        """

        # Mic增益输入模块
        self.mic_gain_spin.valueChanged.connect(self.create_mic_op_gain_data)
        # filter_01模块单元按键
        self.filter01_radioButton_notch.toggled.connect(
            lambda: self.set_module_01(self.filter01_radioButton_notch))  # 功能复选框
        self.filter01_radioButton_bypass.toggled.connect(
            lambda: self.set_module_01(self.filter01_radioButton_bypass))
        self.filter01_radioButton_highpass.toggled.connect(
            lambda: self.set_module_01(self.filter01_radioButton_highpass))
        self.frequencySpin.valueChanged.connect(self.setupC_value)  # 计数器改变时调整电容值
        self.amplitudeSlider.valueChanged.connect(self.setupR_value)  # 滑块位置改变时调整电阻值
        self.frequencySpin_highpass.valueChanged.connect(self.setupC_value_highpass)  # 高通电容调整信号槽

        # filter_02模块单元按键
        self.filter01_radioButton_notch_2.toggled.connect(
            lambda: self.set_module_02(self.filter01_radioButton_notch_2))  # 功能复选框
        self.filter01_radioButton_bypass_2.toggled.connect(
            lambda: self.set_module_02(self.filter01_radioButton_bypass_2))
        self.filter01_radioButton_lowpass.toggled.connect(
            lambda: self.set_module_02(self.filter01_radioButton_lowpass))
        self.frequencySpin_2.valueChanged.connect(self.setupC_value_2)  # 计数器改变时调整电容值
        self.amplitudeSlider_2.valueChanged.connect(self.setupR_value_2)  # 滑块位置改变时调整电阻值
        self.frequencySpin_lowpass.valueChanged.connect(self.setupC_value_lowpass)  # 低通电容调整信号槽

        # OP1增益模块
        self.OP_lowpass_filter_enable.toggled.connect(self.set_module_03)
        self.OP_lowpass_order_radio_two.toggled.connect(self.set_module_03)  # 设置1阶/2阶模式
        self.OP_lowpass_order_radio_chebyshev.toggled.connect(self.set_module_03)
        self.OP_gain_spin.valueChanged.connect(self.set_module_03)  # 设置Rb电阻阻值
        self.OP_gain_spin.valueChanged.connect(self.set_module_04)  # 控制module04参数
        self.OP_gain_spin.valueChanged.connect(self.set_module_05)  # 控制module05参数
        self.OP_gain_spin.valueChanged.connect(self.set_module_07)  # 控制module07参数
        # self.OP_gain_spin.valueChanged.connect(self.set_module_08)  # 控制module08参数
        # high shelf
        self.OP_highshelf_filter_enable.toggled.connect(self.set_module_04)
        self.high_shelf_gain_spin.valueChanged.connect(self.set_module04_data)
        self.high_shelf_frequency_spin.valueChanged.connect(self.set_module04_data)
        # low shelf
        self.OP_lowshelf_filter_enable.toggled.connect(self.set_module_05)
        self.low_shelf_gain_spin.valueChanged.connect(self.setup_module05_data)
        self.low_shelf_frequency_spin.valueChanged.connect(self.setup_module05_data)
        # op low pass
        self.frequencySpin_OP_lowpass.valueChanged.connect(self.set_module_06_data)
        # self.OP_gain_spin.valueChanged.connect(self.set_module_06_data)
        # op peak
        self.OP_peak_filter_enable.toggled.connect(self.set_module_07)
        self.peak_frequency_spin.valueChanged.connect(self.set_module_07_data)
        self.peak_gain_spin.valueChanged.connect(self.set_module_07_data)
        self.peak_lowpass_slider.valueChanged.connect(self.set_module_07_data)
        self.peak_attenuation_slider.valueChanged.connect(self.set_module_07_data)
        # two order lowpass
        # self.OP_lowpass_order_radio_two.toggled.connect(self.set_module_08)
        self.OP_lowpass_order_radio_bessel.toggled.connect(self.set_module_08)
        self.OP_lowpass_order_radio_butterworth.toggled.connect(self.set_module_08)
        self.OP_lowpass_order_radio_chebyshev.toggled.connect(self.set_module_08)
        self.chebyshev_1dB.toggled.connect(self.set_module_08)
        self.chebyshev_1dB_2.toggled.connect(self.set_module_08)
        self.chebyshev_1dB_3.toggled.connect(self.set_module_08)
        self.frequencySpin_OP_lowpass.valueChanged.connect(self.set_module_08)

        self.outputButton.clicked.connect(self.create_netlist)  # 仿真 创建circuit并开始仿真计算窗口
        self.AimCurveInButton.clicked.connect(self.import_aim_curve)  # 参考曲线 导入曲线按键时触发导入excel操作
        self.export_bom_button.clicked.connect(self.export_bom)

        self.ImportSettings_FF.clicked.connect(self.ImportSettings_FF_clicked)  # 配置 信息导入
        self.SaveSettings_FF.clicked.connect(self.SaveSettings_FF_clicked)  # 配置 信息保存
        self.test_button.clicked.connect(self.reset_settings)  # 重置配置信息

        self.btn_notch01_tuning.clicked.connect(self.notch01_tuning)  # tuning
        self.btn_notch02_tuning.clicked.connect(self.notch02_tuning)
        self.btn_peak01_tuning.clicked.connect(self.peak01_tuning)
        self.btn_two_order_lowpass_tuning.clicked.connect(self.two_order_lowpass_tuning)

    # mic增益设置
    def create_mic_op_gain_data(self):
        gain = self.mic_gain_spin.value()
        Ra_value = int(22000 / (10 ** (gain / 20)))
        Rb_value = 22000 - Ra_value
        self.mic_op_gain_data['Ra_value'] = Ra_value
        self.mic_op_gain_data['Rb_value'] = Rb_value

    # module01模块参数设置
    def setupC_value(self):
        """
        根据选择的中心频率设置电容容值
        """
        f = self.frequencySpin.value()  # 用户设置频率数值
        c_value = 1 / (2 * math.pi * 2200 * f)  # 默认电阻2.2k，c_value为浮点进度数值
        self.two_order_filter_data['C1_value'] = c_value2map(c_value)  # E12电容标准取值，str格式,ex:33nf
        self.two_order_filter_data['C2_value'] = c_value2map(c_value)
        self.two_order_filter_data['C_value_double'] = c_value2map_dubble(c_value)  # 接地电容取并联值，str格式,ex:66nf
        # print(self.two_order_filter_data.items())#接地电容容值

    def setupR_value(self):
        """
        根据幅值滑块位置设置幅值调整电阻阻值
        :return:
        """
        v = self.amplitudeSlider.value()
        self.two_order_filter_data['R_gain_value'] = get_R_value(v)

        self.label_Slider_value.setText(self.two_order_filter_data['R_gain_value'])  # 设置UI界面label显示数值

    def set_module_01(self, btn):
        """设置module01工作模式
        :param btn:三种模式选择按键
        :return:self.module01参数调整
        """
        if btn.text() == '带阻' and btn.isChecked():
            self.module01 = 'notch'
            self.amplitudeSlider.setHidden(False)  # UI界面调整
            self.frequencySpin.setHidden(False)
            self.frequencySpin_highpass.setHidden(True)
            if self.notch01_status:
                self.pixmapLabel.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            else:
                self.pixmapLabel.setPixmap(QtGui.QPixmap(':/mic/icon/Filter.png'))
        if btn.text() == '直通' and btn.isChecked():
            self.pixmapLabel.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
            self.module01 = 'bypass'
            self.amplitudeSlider.setHidden(True)
            self.frequencySpin.setHidden(True)
            self.frequencySpin_highpass.setHidden(True)
            self.label_Slider_value.setText('None')
        if btn.text() == '高通' and btn.isChecked():
            self.pixmapLabel.setPixmap(QtGui.QPixmap(":/mic/icon/HighPass.png"))
            self.module01 = 'highpass'
            self.amplitudeSlider.setHidden(True)
            self.frequencySpin.setHidden(True)
            self.frequencySpin_highpass.setHidden(False)
            self.label_Slider_value.setText('None')

    def setupC_value_highpass(self):
        """根据选择的中心频率设置电容容值"""
        f = self.frequencySpin_highpass.value()  # 用户设置频率数值
        c_value = 1 / (2 * math.pi * 2200 * f)  # 默认电阻2.2k，c_value为浮点进度数值
        self.one_order_highpass_data['C_value'] = c_value2map(c_value)  # E12电容标准取值，str格式,ex:33nf
        # print(self.one_order_highpass_data.items())

    # module02模块参数设置
    def setupC_value_2(self):

        f = self.frequencySpin_2.value()  # 用户设置频率数值
        c_value = 1 / (2 * math.pi * 2200 * f)  # 默认电阻2.2k，c_value为浮点进度数值
        self.two_order_filter_data_02['C1_value'] = c_value2map(c_value)  # E12电容标准取值，str格式,ex:33nf
        self.two_order_filter_data_02['C2_value'] = c_value2map(c_value)
        self.two_order_filter_data_02['C_value_double'] = c_value2map_dubble(c_value)  # 接地电容取并联值，str格式,ex:66nf

    def setupR_value_2(self):

        v = self.amplitudeSlider_2.value()
        self.two_order_filter_data_02['R_gain_value'] = get_R_value(v)
        self.label_Slider_value_2.setText(self.two_order_filter_data_02['R_gain_value'])  # 设置UI界面label显示数值
        # print(self.two_order_filter_data_02.items())  # 接地电容容值

    def set_module_02(self, btn):

        if btn.text() == '带阻' and btn.isChecked():
            self.module02 = 'notch'
            self.amplitudeSlider_2.setHidden(False)  # UI界面调整
            self.frequencySpin_2.setHidden(False)
            self.frequencySpin_lowpass.setHidden(True)
            if self.notch02_status:
                self.pixmapLabel_2.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            else:
                self.pixmapLabel_2.setPixmap(QtGui.QPixmap(':/mic/icon/Filter.png'))
        if btn.text() == '直通' and btn.isChecked():
            self.pixmapLabel_2.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
            self.module02 = 'bypass'
            self.amplitudeSlider_2.setHidden(True)
            self.frequencySpin_2.setHidden(True)
            self.frequencySpin_lowpass.setHidden(True)
            self.label_Slider_value_2.setText('None')
        if btn.text() == '低通' and btn.isChecked():
            self.pixmapLabel_2.setPixmap(QtGui.QPixmap(':/mic/icon/lowpass.png'))
            self.module02 = 'lowpass'
            self.amplitudeSlider_2.setHidden(True)
            self.frequencySpin_2.setHidden(True)
            self.frequencySpin_lowpass.setHidden(False)
            self.label_Slider_value_2.setText('None')

    def setupC_value_lowpass(self):
        """根据选择的中心频率设置电容容值"""
        f = self.frequencySpin_lowpass.value()  # 用户设置频率数值
        c_value = 1 / (2 * math.pi * 2200 * f)  # 默认电阻2.2k，c_value为浮点进度数值
        self.one_order_lowpass_data['C_value'] = c_value2map(c_value)  # E12电容标准取值，str格式,ex:33nf

    # module 03
    def set_module_03(self):
        if self.OP_lowpass_filter_enable.isChecked():  # module 06 on
            self.OP_lowshelf_filter_enable.setChecked(False)  # 关闭 module 05
            self.OP_peak_filter_enable.setChecked(False)  # 关闭 module 07
            self.groupBox_8.setEnabled(True)
            if self.OP_lowpass_order_radio_one.isChecked():  # 1阶
                self.label_16.setEnabled(True)  # 启用module06低通模块
                self.frequencySpin_OP_lowpass.setEnabled(True)
                self.set_module_06()
            else:  # 2阶
                self.set_module_08()

        else:  # module 06 off
            self.groupBox_4.setEnabled(True)  # 启用low shelf, high shelf, peak
            self.groupBox_5.setEnabled(True)
            self.groupBox_6.setEnabled(True)
            self.label_16.setEnabled(False)  # 停用module06 低通模块
            self.frequencySpin_OP_lowpass.setEnabled(False)
            self.groupBox_8.setEnabled(False)
            self.groupBox_9.setEnabled(False)
            self.groupBox_10.setEnabled(False)

            self.module06 = None
            self.module03 = 'op_one_order'
            if self.OP_lowshelf_filter_enable.isChecked():  # 关闭module03时根据判断重置Rb值,防止module05打开状态误调Rb
                pass
            else:
                self.set_module03_data()

    def set_module03_data(self):
        gain = self.OP_gain_spin.value()
        if self.OP_lowshelf_filter_enable.isChecked():  # 限制low shelf最低增益
            self.low_shelf_gain_spin.setMinimum(gain)
        if self.OP_highshelf_filter_enable.isChecked():  # 限制high shelf最低增益
            self.high_shelf_gain_spin.setMinimum(gain)

        self.op_gain_data['Rb_value'] = get_Rb_value(gain)[0]

    # module 04 high shelf
    def set_module_04(self):
        if self.OP_highshelf_filter_enable.isChecked():
            self.high_shelf_frequency_spin.setEnabled(True)  # 启用gain及frequency调整
            self.high_shelf_gain_spin.setEnabled(True)
            self.label_14.setEnabled(True)
            self.label_Slider_value_8.setEnabled(True)
            self.high_shelf_gain_spin.setMinimum(self.OP_gain_spin.value())  # 重置最小增益
            self.set_module04_data()
        else:
            self.high_shelf_frequency_spin.setEnabled(False)  # 停用gain及frequency调整
            self.high_shelf_gain_spin.setEnabled(False)
            self.label_14.setEnabled(False)
            self.label_Slider_value_8.setEnabled(False)
            self.module04 = None  # 设置模式

    def set_module04_data(self):
        gain = self.high_shelf_gain_spin.value()
        gain_op = self.OP_gain_spin.value()
        if gain - gain_op > 0:
            R1 = 20000 / (10 ** ((gain - gain_op) / 20) - 1)  # 反相放大器增益计算法
            self.high_shelf_data['R_value'] = R_value2map(R1)

            f = self.high_shelf_frequency_spin.value()
            c_value = 1 / (2 * math.pi * R1 * f)
            self.high_shelf_data['C_value'] = c_value2map(c_value)
            self.module04 = 'high_shelf'
        else:
            self.module04 = None

    # module 05 low shelf
    def set_module_05(self):
        if self.OP_lowshelf_filter_enable.isChecked():
            self.low_shelf_frequency_spin.setEnabled(True)  # 启用gain及frequency调整
            self.low_shelf_gain_spin.setEnabled(True)
            self.label_10.setEnabled(True)
            self.label_Slider_value_6.setEnabled(True)
            self.low_shelf_gain_spin.setMinimum(self.OP_gain_spin.value())  # 重置最小增益
            self.OP_gain_spin.setMinimum(0)  # 限制op gain最小增益
            self.OP_lowpass_filter_enable.setChecked(False)  # 关闭 module03
            self.OP_peak_filter_enable.setChecked(False)  # 关闭 module 07
            self.setup_module05_data()
        else:
            self.low_shelf_frequency_spin.setEnabled(False)  # 关闭gain及frequency调整
            self.low_shelf_gain_spin.setEnabled(False)
            self.label_10.setEnabled(False)
            self.label_Slider_value_6.setEnabled(False)
            self.module05 = None
            self.set_module03_data()  # 交还OP_R_value控制权
            self.OP_gain_spin.setMinimum(-10)  # 重置op gain最小增益

    def setup_module05_data(self):
        gain2 = self.low_shelf_gain_spin.value()
        gain_op = self.OP_gain_spin.value()
        if gain2 - gain_op > 0:
            Rb = 20000 * (10 ** (gain2 / 20))  # Rb_value 阻值计算
            R2 = 20000 * (10 ** ((gain2 + gain_op) / 20) / (
                    10 ** (gain2 / 20) - 10 ** (gain_op / 20)))  # low shelf R_value 阻值计算
            self.op_gain_data['Rb_value'] = R_value2map(Rb)
            self.low_shelf_data['R_value'] = R_value2map(R2)

            f = self.low_shelf_frequency_spin.value()
            c_value = 1 / (2 * math.pi * R2 * f)
            self.low_shelf_data['C_value'] = c_value2map(c_value)
            self.module05 = 'low_shelf'
        else:
            self.module05 = None
            self.set_module03_data()

    # module 06 op lowpass
    def set_module_06(self):
        self.groupBox_9.setEnabled(False)
        self.groupBox_10.setEnabled(False)
        self.groupBox_4.setEnabled(True)  # 启用low shelf, high shelf, peak
        self.groupBox_5.setEnabled(True)
        self.groupBox_6.setEnabled(True)
        self.label_15.setPixmap(QtGui.QPixmap(':/mic/icon/lowpass.png'))
        self.module03 = 'op_one_order'
        self.module06 = 'op_lowpass'
        self.set_module_06_data()

    def set_module_06_data(self):
        gain = self.OP_gain_spin.value()
        f = self.frequencySpin_OP_lowpass.value()
        r_value = get_Rb_value(gain)[1]
        c_value = 1 / (2 * math.pi * r_value * f)
        self.op_lowpass_data['C_value'] = c_value2map(c_value)

    # op peak module 07
    def set_module_07(self):
        if self.OP_peak_filter_enable.isChecked():
            self.OP_lowpass_filter_enable.setChecked(False)  # 关闭 module03
            self.OP_lowshelf_filter_enable.setChecked(False)  # 关闭 module 05
            self.peak_gain_spin.setValue(self.OP_gain_spin.value())  # 同步op gain & peak gain
            # self.OP_gain_spin.setEnabled(False)
            self.set_module_07_data()
            if self.peak01_status is False:
                self.label_Slider_value_4.setEnabled(True)
                self.peak_attenuation_slider.setEnabled(True)
                self.label_Slider_value_3.setEnabled(True)
                self.peak_lowpass_slider.setEnabled(True)
                self.label_Slider_value_7.setEnabled(True)
                self.peak_gain_spin.setEnabled(True)
                self.label_9.setEnabled(True)
                self.peak_frequency_spin.setEnabled(True)
            else:
                self.label_Slider_value_4.setEnabled(False)
                self.peak_attenuation_slider.setEnabled(False)
                self.label_Slider_value_3.setEnabled(False)
                self.peak_lowpass_slider.setEnabled(False)
                self.label_Slider_value_7.setEnabled(False)
                self.peak_gain_spin.setEnabled(False)
                self.label_9.setEnabled(False)
                self.peak_frequency_spin.setEnabled(False)
        else:
            self.label_Slider_value_4.setEnabled(False)
            self.peak_attenuation_slider.setEnabled(False)
            self.label_Slider_value_3.setEnabled(False)
            self.peak_lowpass_slider.setEnabled(False)
            self.label_Slider_value_7.setEnabled(False)
            self.peak_gain_spin.setEnabled(False)
            self.label_9.setEnabled(False)
            self.peak_frequency_spin.setEnabled(False)
            # self.OP_gain_spin.setEnabled(True)

            self.module07 = None
            if self.sender() == self.OP_peak_filter_enable:
                self.OP_gain_spin.setValue(0)

    def set_module_07_data(self):
        self.OP_gain_spin.setValue(self.peak_gain_spin.value())  # 同步op gain & peak gain
        gain = self.peak_gain_spin.value()
        f = self.peak_frequency_spin.value()
        pos_r_high = self.peak_lowpass_slider.value()
        pos_r_gain = self.peak_attenuation_slider.value()
        if self.peak01_status is False:
            if gain == 0:
                self.module07 = None
            else:
                Rb = get_Rb_value(gain)[1]
                R1 = 10000 * Rb / (Rb - 20000)
                c_value = 1 / (1.414 * math.pi * R1 * f)  # 中心频率有1.414倍偏移
                R3 = 2 * R1
                r_high_cut = R3 / (R3 ** (pos_r_high / 61))

                self.op_peak_data['R1_value'] = R_value2map(R1)
                self.op_peak_data['R2_value'] = R_value2map(R1)
                self.op_peak_data['R_half_value'] = R_value2map(R1 / 2)
                self.op_peak_data['C1_value'] = c_value2map(c_value)
                self.op_peak_data['C2_value'] = c_value2map(c_value)
                self.op_peak_data['C_value_double'] = c_value2map_dubble(c_value)
                self.op_peak_data['R_gain_value'] = get_R_value(pos_r_gain)
                self.op_peak_data['R_high_cut'] = R_value2map_2(r_high_cut)
                if self.OP_peak_filter_enable.isChecked():
                    self.module07 = 'peak'

                # print(self.op_peak_data)
        else:
            if self.OP_peak_filter_enable.isChecked():
                self.module07 = 'peak'

    # module 08 two order lowpass
    def set_module_08(self):
        if self.OP_lowpass_filter_enable.isChecked() and self.OP_lowpass_order_radio_two.isChecked():

            self.OP_lowshelf_filter_enable.setChecked(False)  # 关闭low shelf,high shelf,peak
            self.OP_highshelf_filter_enable.setChecked(False)
            self.OP_peak_filter_enable.setChecked(False)
            self.groupBox_4.setEnabled(False)
            self.groupBox_5.setEnabled(False)
            self.groupBox_6.setEnabled(False)

            self.module03 = 'op_two_order'
            self.module06 = None

            if self.two_order_lowpass_status is False:
                self.groupBox_9.setEnabled(True)  # 二阶类型选择框
                self.frequencySpin_OP_lowpass.setEnabled(True)
                self.label_16.setEnabled(True)
                if self.OP_lowpass_order_radio_bessel.isChecked():
                    self.groupBox_10.setEnabled(False)
                    module08 = 'bessel'
                elif self.OP_lowpass_order_radio_butterworth.isChecked():
                    self.groupBox_10.setEnabled(False)
                    module08 = 'butterworth'
                else:
                    self.groupBox_10.setEnabled(True)
                    if self.chebyshev_1dB.isChecked():
                        module08 = 'chebyshev-1'
                    elif self.chebyshev_1dB_2.isChecked():
                        module08 = 'chebyshev-2'
                    else:
                        module08 = 'chebyshev-3'
                self.label_15.setPixmap(QtGui.QPixmap(':/mic/icon/lowpass.png'))
                self.set_module_08_data(module08)
            else:
                self.label_15.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
                self.groupBox_9.setEnabled(False)
                self.groupBox_10.setEnabled(False)
                self.frequencySpin_OP_lowpass.setEnabled(False)
                self.label_16.setEnabled(False)
        else:
            pass

    def set_module_08_data(self, module=None):

        gain = self.OP_gain_spin.value()
        f = self.frequencySpin_OP_lowpass.value()
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
            self.two_order_lowpass_data['R1_value'] = R_value2map_2(r1)
            self.two_order_lowpass_data['R2_value'] = R_value2map_2(r2)
            self.two_order_lowpass_data['R3_value'] = R_value2map_2(r3)
            self.two_order_lowpass_data['C2_value'] = c_value2map(C2)
        elif module == 'butterworth':
            K = k * 0.9
            r1 = R1 * K
            r2 = R2 * K
            r3 = R3 * K
            C2 = C * 18 / 68 * 1e-9
            self.two_order_lowpass_data['R1_value'] = R_value2map_2(r1)
            self.two_order_lowpass_data['R2_value'] = R_value2map_2(r2)
            self.two_order_lowpass_data['R3_value'] = R_value2map_2(r3)
            self.two_order_lowpass_data['C2_value'] = c_value2map(C2)
        elif module == 'chebyshev-1':
            K = k * 0.85
            r1 = R1 * K
            r2 = R2 * K
            r3 = R3 * K
            C2 = C * 24 / 68 * 1e-9
            self.two_order_lowpass_data['R1_value'] = R_value2map_2(r1)
            self.two_order_lowpass_data['R2_value'] = R_value2map_2(r2)
            self.two_order_lowpass_data['R3_value'] = R_value2map_2(r3)
            self.two_order_lowpass_data['C2_value'] = c_value2map(C2)
        elif module == 'chebyshev-2':
            K = k * 0.8
            r1 = R1 * K
            r2 = R2 * K
            r3 = R3 * K
            C2 = C * 50 / 68 * 1e-9
            self.two_order_lowpass_data['R1_value'] = R_value2map_2(r1)
            self.two_order_lowpass_data['R2_value'] = R_value2map_2(r2)
            self.two_order_lowpass_data['R3_value'] = R_value2map_2(r3)
            self.two_order_lowpass_data['C2_value'] = c_value2map(C2)
        elif module == 'chebyshev-3':
            K = k * 0.75
            r1 = R1 * K
            r2 = R2 * K
            r3 = R3 * K
            C2 = C * 1e-9
            self.two_order_lowpass_data['R1_value'] = R_value2map_2(r1)
            self.two_order_lowpass_data['R2_value'] = R_value2map_2(r2)
            self.two_order_lowpass_data['R3_value'] = R_value2map_2(r3)
            self.two_order_lowpass_data['C2_value'] = c_value2map(C2)
        else:
            pass

    # 理想滤波器曲线导入函数
    def import_aim_curve(self):
        """导入参考Filter目标曲线,参数保存为self.air_curve_data
        :return: OK
        """
        excel_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', '.',
                                                              'excel Files (*.xls *.xlsx);;All Files (*)')
        if excel_file:
            try:
                excel_data = My_ANC_ExcelRead(excel_file)
                self.aim_curve_data = excel_data
                self.AimCurveInButton.setDefault(True)
                QtWidgets.QMessageBox.information(self, '提示', '导入成功')
            except ValueError as e:
                QtWidgets.QMessageBox.warning(self, '提示', str(e), QtWidgets.QMessageBox.Yes)

    # 创建circuit
    def create_netlist(self):
        """调用MyNetlistCreat类，创建电路图并进行仿真运算"""
        my_netlist = MyNetlistCreate(mic_op_gain_data=self.mic_op_gain_data,
                                     two_order_filter_data=self.two_order_filter_data, module_01=self.module01,
                                     two_order_filter_data_02=self.two_order_filter_data_02, module_02=self.module02,
                                     one_order_lowpass_data=self.one_order_lowpass_data,
                                     one_order_highpass_data=self.one_order_highpass_data,
                                     two_order_lowpass_data=self.two_order_lowpass_data,
                                     op_gain_data=self.op_gain_data, module_03=self.module03,
                                     high_shelf_data=self.high_shelf_data, module_04=self.module04,
                                     low_shelf_data=self.low_shelf_data, module_05=self.module05,
                                     op_lowpass_data=self.op_lowpass_data, module_06=self.module06,
                                     op_peak_data=self.op_peak_data, module_07=self.module07)

        my_netlist.create_netlist()
        print(str(my_netlist.circuit))
        self.run_simulator(my_netlist.circuit)

    def run_simulator(self, netlist):
        """根据电路网表图进行仿真计算
        :param netlist:
        :return:
        """
        simulator = MyFilterSimulator(_netlist=netlist, aim_curve_data=self.aim_curve_data)
        analysis = simulator.my_simulator()  # 仿真计算
        simulator.my_bode_diagram(analysis, self.aim_curve_data)  # 绘制伯德图

    # 导出BOM
    def export_bom(self):
        # self.mic_op_gain_data = dict(Ra_value=22000, Rb_value=0)
        # self.two_order_filter_data = dict(C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k',
        #                                   R2_value='2.2k', R_half_value='1.1k', R_gain_value=0)
        # self.two_order_filter_data_02 = dict(C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k',
        #                                      R2_value='2.2k', R_half_value='1.1k', R_gain_value=0)
        # self.one_order_highpass_data = dict(C_value='68n', R_value='2.2k')
        # self.one_order_lowpass_data = dict(C_value='68n', R_value='2.2k')
        #
        # self.op_gain_data = dict(Ra_value='20k', Rb_value='20k')
        # self.op_lowpass_data = dict(C_value='8.2n')
        #
        # self.high_shelf_data = dict(C_value='680p', R_value='220k')
        # self.low_shelf_data = dict(C_value='680p', R_value='220k')
        # self.op_peak_data = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k', R2_value='20k',
        #                          R_half_value='10k', R_gain_value=0, R_high_cut='39k')
        # self.two_order_lowpass_data = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
        #                                    C2_value='12n')
        # self.module01 = 'bypass'
        # self.module02 = 'bypass'
        # self.module03 = 'op_one_order'
        # self.module04 = None
        # self.module05 = None
        # self.module06 = None
        # self.module07 = None
        #
        # self.notch01_status = False  # 手动调整增益开关
        # self.notch02_status = False
        # self.peak01_status = False
        # self.two_order_lowpass_status = False

        bom = list()
        # module 01
        if self.module01 == 'notch':
            # postil = ['C2', 'C5', 'C4', 'R4', 'R7', 'R6', 'R5']
            bom.append('C2' + ' ' + self.two_order_filter_data['C1_value'] + '\n')
            bom.append('C5' + ' ' + self.two_order_filter_data['C2_value'] + '\n')
            bom.append('C4' + ' ' + self.two_order_filter_data['C_value_double'] + '\n')
            bom.append('R4' + ' ' + self.two_order_filter_data['R1_value'] + '\n')
            bom.append('R7' + ' ' + self.two_order_filter_data['R2_value'] + '\n')
            bom.append('R6' + ' ' + self.two_order_filter_data['R_half_value'] + '\n')
            bom.append('R5' + ' ' + str(self.two_order_filter_data['R_gain_value']) + '\n')
        elif self.module01 == 'highpass':
            bom.append('C3' + ' ' + self.one_order_highpass_data['C_value'] + '\n')
            bom.append('R8' + ' ' + self.one_order_highpass_data['R_value'] + '\n')
        else:
            bom.append('J01 short' + '\n')
        # module 02
        if self.module02 == 'notch':
            # postil = ['C6', 'C9', 'C7', 'R9', 'R13', 'R12', 'R11']
            bom.append('C6' + ' ' + self.two_order_filter_data_02['C1_value'] + '\n')
            bom.append('C9' + ' ' + self.two_order_filter_data_02['C2_value'] + '\n')
            bom.append('C7' + ' ' + self.two_order_filter_data_02['C_value_double'] + '\n')
            bom.append('R9' + ' ' + self.two_order_filter_data_02['R1_value'] + '\n')
            bom.append('R13' + ' ' + self.two_order_filter_data_02['R2_value'] + '\n')
            bom.append('R12' + ' ' + self.two_order_filter_data_02['R_half_value'] + '\n')
            bom.append('R11' + ' ' + str(self.two_order_filter_data_02['R_gain_value']) + '\n')
        elif self.module02 == 'lowpass':
            bom.append('C8' + ' ' + self.one_order_lowpass_data['C_value'] + '\n')
            bom.append('R10' + ' ' + self.one_order_lowpass_data['R_value'] + '\n')
        else:
            bom.append('J02 short' + '\n')
        # module 03
        if self.module03 == 'op_one_order':
            # self.op_gain_data = dict(Ra_value='20k', Rb_value='20k')
            bom.append('R14' + ' ' + '0' + '\n')
            bom.append('R15' + ' ' + self.op_gain_data['Ra_value'] + '\n')
            bom.append('R20' + ' ' + self.op_gain_data['Rb_value'] + '\n')
            bom.append('R18' + ' ' + '0' + '\n')
        else:
            # self.two_order_lowpass_data = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
            #                                    C2_value='12n')
            bom.append('R14' + ' ' + self.two_order_lowpass_data['R1_value'] + '\n')
            bom.append('R15' + ' ' + '0' + '\n')
            bom.append('R18' + ' ' + self.two_order_lowpass_data['R3_value'] + '\n')
            bom.append('R19' + ' ' + self.two_order_lowpass_data['R2_value'] + '\n')
            bom.append('C10' + ' ' + self.two_order_lowpass_data['C2_value'] + '\n')
            bom.append('C12' + ' ' + self.two_order_lowpass_data['C1_value'] + '\n')
        # module 04
        if self.module04 == 'high_shelf':
            # self.high_shelf_data = dict(C_value='680p', R_value='220k')
            bom.append('R16' + ' ' + self.high_shelf_data['R_value'] + '\n')
            bom.append('C11' + ' ' + self.high_shelf_data['C_value'] + '\n')
        # module 05
        if self.module05 == 'low_shelf':
            # self.low_shelf_data = dict(C_value='680p', R_value='220k')
            bom.append('C13' + ' ' + self.low_shelf_data['C_value'] + '\n')
            bom.append('R25' + ' ' + self.low_shelf_data['R_value'] + '\n')
        # module 06
        if self.module06 == 'op_lowpass':
            # self.op_lowpass_data = dict(C_value='8.2n')
            bom.append('C14' + ' ' + self.op_lowpass_data['C_value'] + '\n')
        # module 07
        if self.module07 == 'peak':
            # self.op_peak_data = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k',
            #                          R2_value='20k',R_half_value='10k', R_gain_value=0, R_high_cut='39k')
            bom.append('C15' + ' ' + self.op_peak_data['C1_value'] + '\n')
            bom.append('C16' + ' ' + self.op_peak_data['C_value_double'] + '\n')
            bom.append('C17' + ' ' + self.op_peak_data['C2_value'] + '\n')
            bom.append('R21' + ' ' + self.op_peak_data['R1_value'] + '\n')
            bom.append('R24' + ' ' + self.op_peak_data['R2_value'] + '\n')
            bom.append('R23' + ' ' + self.op_peak_data['R_half_value'] + '\n')
            bom.append('R22' + ' ' + str(self.op_peak_data['R_gain_value']) + '\n')
            bom.append('R17' + ' ' + self.op_peak_data['R_high_cut'] + '\n')
            bom.append('R26' + ' ' + '0' + '\n')
            bom.append('R27' + ' ' + '0' + '\n')

        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'save file', '.', 'txt Files (*.txt);;All Files (*)')
        if filename[0]:
            with open(filename[0], 'w') as f:
                f.writelines(bom)

    # 配置信息导入导出
    def ImportSettings_FF_clicked(self):
        """导入配置信息"""
        # 设置目录
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', '.', 'ini Files (*.ini);;All Files (*)')
        if filename[0]:
            self.peak_frequency_spin.valueChanged.disconnect(self.set_module_07_data)
            self.peak_gain_spin.valueChanged.disconnect(self.set_module_07_data)
            self.peak_lowpass_slider.valueChanged.disconnect(self.set_module_07_data)
            self.peak_attenuation_slider.valueChanged.disconnect(self.set_module_07_data)

            settings = QSettings(filename[0], QSettings.IniFormat)
            # mic 增益配置
            self.mic_gain_spin.setValue(settings.value('mic_gain', 0, type=int))
            # module01配置
            self.notch01_status = settings.value('module01/tuning_status', False, type=bool)
            self.frequencySpin.setValue(settings.value('module01/notch_frequency', 1000, type=int))  # 无数据时导入1000默认值
            self.amplitudeSlider.setValue(settings.value('module01/notch_amplitude', 0, type=int))
            self.filter01_radioButton_notch.setChecked(settings.value('module01/radioButton_notch', type=bool))
            self.filter01_radioButton_highpass.setChecked(settings.value('module01/radioButton_highpass', type=bool))
            self.filter01_radioButton_bypass.setChecked(settings.value('module01/radioButton_bypass', type=bool))
            self.frequencySpin_highpass.setValue(settings.value('module01/highpass_frequency', 1000, type=int))
            if self.notch01_status:
                self.two_order_filter_data = settings.value('module01/tuning_data', self.two_order_filter_data,
                                                            type=dict)
                self.set_notch01_parameter(self.two_order_filter_data, self.notch01_status)

            # module02配置
            self.notch02_status = settings.value('module02/tuning_status', False, type=bool)
            self.frequencySpin_2.setValue(settings.value('module02/notch_frequency', 1000, type=int))  # 无数据时导入1000默认值
            self.amplitudeSlider_2.setValue(settings.value('module02/notch_amplitude', 0, type=int))
            self.filter01_radioButton_notch_2.setChecked(settings.value('module02/radioButton_notch', type=bool))
            self.filter01_radioButton_lowpass.setChecked(settings.value('module02/radioButton_lowpass', type=bool))
            self.filter01_radioButton_bypass_2.setChecked(settings.value('module02/radioButton_bypass', type=bool))
            self.frequencySpin_lowpass.setValue(settings.value('module02/lowpass_frequency', 1000, type=int))
            if self.notch02_status:
                self.two_order_filter_data_02 = settings.value('module02/tuning_data', self.two_order_filter_data_02,
                                                               type=dict)
                self.set_notch02_parameter(self.two_order_filter_data_02, self.notch02_status)

            # module03
            self.two_order_lowpass_status = settings.value('module03/tuning_status', False, type=bool)
            self.OP_lowpass_filter_enable.setChecked(settings.value('module03/filter_enable', type=bool))
            self.OP_lowpass_order_radio_one.setChecked(settings.value('module03/order', type=bool))
            self.OP_lowpass_order_radio_two.setChecked(settings.value('module03/order_2', type=bool))
            self.OP_lowpass_order_radio_bessel.setChecked(settings.value('module03/filter_type', type=bool))
            self.OP_lowpass_order_radio_butterworth.setChecked(settings.value('module03/filter_type2', type=bool))
            self.OP_lowpass_order_radio_chebyshev.setChecked(settings.value('module03/filter_type3', type=bool))
            self.chebyshev_1dB.setChecked(settings.value('module03/ripple_1', type=bool))
            self.chebyshev_1dB_2.setChecked(settings.value('module03/ripple_2', type=bool))
            self.chebyshev_1dB_3.setChecked(settings.value('module03/ripple_3', type=bool))
            self.OP_gain_spin.setValue(settings.value('module03/gain', 0, type=int))
            self.frequencySpin_OP_lowpass.setValue(settings.value('module03/frequency', 1000, type=int))
            if self.two_order_lowpass_status:
                self.two_order_lowpass_data = settings.value('module03/tuning_data', self.two_order_lowpass_data,
                                                             type=dict)
                self.set_two_order_lowpass_parameter(self.two_order_lowpass_data, self.two_order_lowpass_status)

            # module04
            self.OP_highshelf_filter_enable.setChecked(settings.value('module04/filter_enable', type=bool))
            self.high_shelf_gain_spin.setValue(settings.value('module04/gain', 0, type=int))
            self.high_shelf_frequency_spin.setValue(settings.value('module04/frequency', 1000, type=int))

            # module05
            self.OP_lowshelf_filter_enable.setChecked(settings.value('module05/filter_enable', type=bool))
            self.low_shelf_gain_spin.setValue(settings.value('module05/gain', 0, type=int))
            self.low_shelf_frequency_spin.setValue(settings.value('module05/frequency', 1000, type=int))

            # module07
            self.peak01_status = settings.value('module07/tuning_status', False, type=bool)
            self.OP_peak_filter_enable.setChecked(settings.value('module07/filter_enable', type=bool))
            self.peak_gain_spin.setValue(settings.value('module07/gain', 0, type=int))
            self.peak_frequency_spin.setValue(settings.value('module07/frequency', 1000, type=int))
            self.peak_lowpass_slider.setValue(settings.value('module07/high_reject', 0, type=int))
            self.peak_attenuation_slider.setValue(settings.value('module07/amplitude_attenuation', 0, type=int))
            if self.peak01_status:
                self.op_peak_data = settings.value('module07/tuning_data', self.op_peak_data, type=dict)
                self.set_peak01_parameter(self.op_peak_data, self.peak01_status)  # 重置ICON及界面

            # 窗口尺寸及位置配置
            self.restoreGeometry(settings.value("geometry"))
            self.restoreState(settings.value("windowState"))

            self.peak_frequency_spin.valueChanged.connect(self.set_module_07_data)
            self.peak_gain_spin.valueChanged.connect(self.set_module_07_data)
            self.peak_lowpass_slider.valueChanged.connect(self.set_module_07_data)
            self.peak_attenuation_slider.valueChanged.connect(self.set_module_07_data)

    def SaveSettings_FF_clicked(self):
        """保存filter模块配置信息"""

        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'save file', '.', 'ini Files (*.ini);;All Files (*)')
        if filename[0]:

            settings = QSettings(filename[0], QSettings.IniFormat)
            # mic 输入增益
            settings.setValue('mic_gain', self.mic_gain_spin.value())
            # module01
            settings.beginGroup('module01')
            settings.setValue('notch_frequency', self.frequencySpin.value())
            settings.setValue('notch_amplitude', self.amplitudeSlider.value())
            settings.setValue('radioButton_notch', self.filter01_radioButton_notch.isChecked())
            settings.setValue('radioButton_bypass', self.filter01_radioButton_bypass.isChecked())
            settings.setValue('radioButton_highpass', self.filter01_radioButton_highpass.isChecked())
            settings.setValue('highpass_frequency', self.frequencySpin_highpass.value())
            settings.setValue('tuning_status', self.notch01_status)
            settings.setValue('tuning_data', self.two_order_filter_data)
            settings.endGroup()
            # module02
            settings.beginGroup('module02')
            settings.setValue('notch_frequency', self.frequencySpin_2.value())
            settings.setValue('notch_amplitude', self.amplitudeSlider_2.value())
            settings.setValue('radioButton_notch', self.filter01_radioButton_notch_2.isChecked())
            settings.setValue('radioButton_bypass', self.filter01_radioButton_bypass_2.isChecked())
            settings.setValue('radioButton_lowpass', self.filter01_radioButton_lowpass.isChecked())
            settings.setValue('lowpass_frequency', self.frequencySpin_lowpass.value())
            settings.setValue('tuning_status', self.notch02_status)
            settings.setValue('tuning_data', self.two_order_filter_data_02)
            settings.endGroup()
            # module03
            settings.beginGroup('module03')
            settings.setValue('tuning_status', self.two_order_lowpass_status)
            settings.setValue('tuning_data', self.two_order_lowpass_data)
            settings.setValue('filter_enable', self.OP_lowpass_filter_enable.isChecked())
            settings.setValue('order', self.OP_lowpass_order_radio_one.isChecked())
            settings.setValue('order_2', self.OP_lowpass_order_radio_two.isChecked())
            settings.setValue('filter_type', self.OP_lowpass_order_radio_bessel.isChecked())
            settings.setValue('filter_type2', self.OP_lowpass_order_radio_butterworth.isChecked())
            settings.setValue('filter_type3', self.OP_lowpass_order_radio_chebyshev.isChecked())
            settings.setValue('ripple_1', self.chebyshev_1dB.isChecked())
            settings.setValue('ripple_2', self.chebyshev_1dB_2.isChecked())
            settings.setValue('ripple_3', self.chebyshev_1dB_3.isChecked())
            settings.setValue('gain', self.OP_gain_spin.value())
            settings.setValue('frequency', self.frequencySpin_OP_lowpass.value())
            settings.endGroup()
            # module04
            settings.beginGroup('module04')
            settings.setValue('filter_enable', self.OP_highshelf_filter_enable.isChecked())
            settings.setValue('gain', self.high_shelf_gain_spin.value())
            settings.setValue('frequency', self.high_shelf_frequency_spin.value())
            settings.endGroup()
            # module05
            settings.beginGroup('module05')
            settings.setValue('filter_enable', self.OP_lowshelf_filter_enable.isChecked())
            settings.setValue('gain', self.low_shelf_gain_spin.value())
            settings.setValue('frequency', self.low_shelf_frequency_spin.value())
            settings.endGroup()
            # module07
            settings.beginGroup('module07')
            settings.setValue('filter_enable', self.OP_peak_filter_enable.isChecked())
            settings.setValue('gain', self.peak_gain_spin.value())
            settings.setValue('frequency', self.peak_frequency_spin.value())
            settings.setValue('high_reject', self.peak_lowpass_slider.value())
            settings.setValue('amplitude_attenuation', self.peak_attenuation_slider.value())
            settings.setValue('tuning_status', self.peak01_status)
            settings.setValue('tuning_data', self.op_peak_data)
            settings.endGroup()
            # 窗口尺寸及位置配置
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())

            del settings
            if True:
                QtWidgets.QMessageBox.information(self, '提示', '保存成功')

    def reset_settings(self):
        # mic 增益配置
        self.mic_gain_spin.setValue(0)
        # module01配置
        self.notch01_status = False
        self.frequencySpin.setValue(1000)  # 无数据时导入1000默认值
        self.amplitudeSlider.setValue(0)
        self.filter01_radioButton_bypass.setChecked(True)
        self.frequencySpin_highpass.setValue(1000)

        # module02配置
        self.notch02_status = False
        self.frequencySpin_2.setValue(1000)  # 无数据时导入1000默认值
        self.amplitudeSlider_2.setValue(0)
        self.filter01_radioButton_bypass_2.setChecked(True)
        self.frequencySpin_lowpass.setValue(1000)

        # module03
        self.two_order_lowpass_status = False
        self.OP_lowpass_filter_enable.setChecked(False)
        self.OP_lowpass_order_radio_one.setChecked(True)
        self.OP_lowpass_order_radio_bessel.setChecked(True)
        self.chebyshev_1dB.setChecked(True)
        self.OP_gain_spin.setValue(0)
        self.OP_gain_spin.setMinimum(-10)
        self.frequencySpin_OP_lowpass.setValue(1000)

        # module04
        self.OP_highshelf_filter_enable.setChecked(False)
        self.high_shelf_gain_spin.setValue(0)
        self.high_shelf_frequency_spin.setValue(1000)

        # module05
        self.OP_lowshelf_filter_enable.setChecked(False)
        self.low_shelf_gain_spin.setValue(0)
        self.low_shelf_frequency_spin.setValue(1000)

        # module07
        self.peak01_status = False
        self.OP_peak_filter_enable.setChecked(False)
        self.peak_gain_spin.setValue(0)
        self.peak_frequency_spin.setValue(1000)
        self.peak_lowpass_slider.setValue(0)
        self.peak_attenuation_slider.setValue(0)

        # set default data
        self.set_default_data()
        self.set_default_module()
        self.set_notch01_parameter(self.two_order_filter_data, False)
        self.set_notch02_parameter(self.two_order_filter_data_02, False)
        self.set_peak01_parameter(self.op_peak_data, False)
        self.set_two_order_lowpass_parameter(self.two_order_lowpass_data, False)
        self.set_module_07()

    # tuning
    # module 01
    def set_notch01_parameter(self, data, status):
        """根据tuning对话框返回值设置参数及UI界面"""
        self.notch01_status = status
        if status:
            self.amplitudeSlider.setEnabled(False)
            self.label_2.setEnabled(False)
            self.label.setEnabled(False)
            self.frequencySpin.setEnabled(False)
            self.btn_notch01_tuning.setDefault(True)  # 按键标记

            self.two_order_filter_data = data
            if self.filter01_radioButton_notch.isChecked():
                self.pixmapLabel.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            elif self.filter01_radioButton_bypass.isChecked():
                self.pixmapLabel.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
            else:
                self.pixmapLabel.setPixmap(QtGui.QPixmap(":/mic/icon/HighPass.png"))

        else:
            self.amplitudeSlider.setEnabled(True)
            self.label_2.setEnabled(True)
            self.label.setEnabled(True)
            self.frequencySpin.setEnabled(True)
            self.btn_notch01_tuning.setDefault(False)  # 取消按键标记

            self.setupC_value()  # 重新设置阻容参数
            self.setupR_value()
            if self.filter01_radioButton_notch.isChecked():
                self.pixmapLabel.setPixmap(QtGui.QPixmap(':/mic/icon/Filter.png'))
            elif self.filter01_radioButton_bypass.isChecked():
                self.pixmapLabel.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
            else:
                self.pixmapLabel.setPixmap(QtGui.QPixmap(":/mic/icon/HighPass.png"))

    def notch01_tuning(self):
        dialog = MyNotchFilterTuningDialog(self.two_order_filter_data, self.notch01_status)
        dialog.signal.connect(self.set_notch01_parameter)
        dialog.exec_()
        # print('对话框结束01', self.two_order_filter_data, self.notch01_status)

    # module 02
    def set_notch02_parameter(self, data, status):
        """根据tuning对话框返回值设置参数及UI界面"""
        self.notch02_status = status
        if status:
            self.amplitudeSlider_2.setEnabled(False)
            self.label_3.setEnabled(False)
            self.label_4.setEnabled(False)
            self.frequencySpin_2.setEnabled(False)
            self.btn_notch02_tuning.setDefault(True)  # 按键标记

            self.two_order_filter_data_02 = data
            if self.filter01_radioButton_notch_2.isChecked():
                self.pixmapLabel_2.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            elif self.filter01_radioButton_bypass_2.isChecked():
                self.pixmapLabel_2.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
            else:
                self.pixmapLabel_2.setPixmap(QtGui.QPixmap(":/mic/icon/HighPass.png"))
        else:
            self.amplitudeSlider_2.setEnabled(True)
            self.label_3.setEnabled(True)
            self.label_4.setEnabled(True)
            self.frequencySpin_2.setEnabled(True)
            self.btn_notch02_tuning.setDefault(False)  # 取消按键标记

            self.setupC_value_2()  # 重新设置阻容参数
            self.setupR_value_2()
            if self.filter01_radioButton_notch_2.isChecked():
                self.pixmapLabel_2.setPixmap(QtGui.QPixmap(':/mic/icon/Filter.png'))
            elif self.filter01_radioButton_bypass_2.isChecked():
                self.pixmapLabel_2.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
            else:
                self.pixmapLabel_2.setPixmap(QtGui.QPixmap(":/mic/icon/HighPass.png"))

    def notch02_tuning(self):
        dialog = MyNotchFilterTuningDialog(self.two_order_filter_data_02, self.notch02_status)
        dialog.signal.connect(self.set_notch02_parameter)
        dialog.exec_()
        # print('对话框结束02', self.two_order_filter_data_02, self.notch01_status)

    # peak 01
    def set_peak01_parameter(self, data, status):
        """根据tuning对话框返回值设置参数及UI界面"""
        self.peak01_status = status
        if status:
            self.btn_peak01_tuning.setDefault(True)  # 按键标记
            self.label_11.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            self.set_module_07()
            self.op_peak_data = data
        else:
            self.btn_peak01_tuning.setDefault(False)  # 按键标记
            self.label_11.setPixmap(QtGui.QPixmap(':/mic/icon/peak.png'))
            self.set_module_07()

    def peak01_tuning(self):
        dialog = MyPeakFilterTuningDialog(self.op_peak_data, self.peak01_status)
        dialog.signal.connect(self.set_peak01_parameter)
        dialog.exec_()
        # print('对话框结束03', self.op_peak_data, self.peak01_status)

    # two order lowpass
    def set_two_order_lowpass_parameter(self, data, status):
        """根据二阶tuning对话框返回值设置参数及UI界面"""
        self.two_order_lowpass_status = status
        if status:
            # self.label_16.setEnabled(False)
            # self.frequencySpin_OP_lowpass.setEnabled(False)
            # self.groupBox_9.setEnabled(False)
            # self.groupBox_10.setEnabled(False)
            self.btn_two_order_lowpass_tuning.setDefault(True)  # 按键标记
            self.set_module_08()
            self.two_order_lowpass_data = data
        else:
            self.btn_two_order_lowpass_tuning.setDefault(False)  # 取消按键标记
            self.set_module_08()

    def two_order_lowpass_tuning(self):
        dialog = MyTwoOrderLowpassTuningDialog(self.two_order_lowpass_data, self.two_order_lowpass_status)
        dialog.signal.connect(self.set_two_order_lowpass_parameter)
        dialog.exec_()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myWin = MyWindow()
    myWin.show()
    sys.exit(app.exec_())
