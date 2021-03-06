#!/usr/bin/env python
# -*- coding:utf-8 -*-
import math
import control
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QSettings

# 导入私有模块
from get_capacitance_value import c_value2map, c_value2map_dubble  # 计数器to电容容值
from get_resistance_value import get_R_value, R_value2map, R_value2map_2  # 滑块数值to电阻阻值
from includes.my_ideal_filter_import import FilterImport
from includes.my_filter_simulator import MyFilterSimulator  # netlist仿真计算机绘图类
from includes.my_netlist_create import *  # 根据UI界面参数创建电路图
from value_tuning.notch_tuning_main import MyNotchFilterTuningDialog
from value_tuning.peak_tuning_main import MyPeakFilterTuningDialog
from value_tuning.two_order_lowpass_tuning_main import MyTwoOrderLowpassTuningDialog
from value_tuning.peak_tuning_all_main import MyPeakFilterTuningAllDialog
from FB_Filter_main import SetOp2Window
from EQ_Filter_main import SetEqWindow
from config import BOM_version


class FilterDesignerWindow(SetOp2Window, SetEqWindow):
    """FF_Filter设计主运行程序
    1.用Subcircuit拼装电路
    2.参考曲线导入及仿真计算跟notchFilter2cir方法相同
    """

    def __init__(self, parent=None):

        super(FilterDesignerWindow, self).__init__(parent)
        # self.showMaximized() # 窗口最大化显示
        self.aim_curve_file_path = None
        self.project_file = None
        self.aim_curve_data = None  # 默认参考曲线参数
        self.spk_fb_data = None
        self.spk_artificial_ear_data = None
        self.fb_artificial_ear_data = None

        self.set_default_data()
        self.set_default_module()
        self.signals_slot()
        self.set_default_font()
        self.ff_fb_design_chose()

        self.simulator = MyFilterSimulator()
        self.op1_gain = self.OP_gain_spin.value()
        self.peak01_gain = self.peak_gain_spin.value()


    def set_default_data(self):
        r_notch = R_value2map_2(self.default_notch_r_value)
        r_notch_half = R_value2map_2(self.default_notch_r_value * 0.5)
        r_peak = R_value2map_2(self.default_peak_r_value)
        r_peak_half = R_value2map_2(self.default_peak_r_value * 0.5)
        r_peak_double = R_value2map_2(self.default_peak_r_value * 2)
        r_peak_shelf = R_value2map_2(self.default_peak_r_value * 11)
        r_op_gain = R_value2map_2(self.default_op_gain_r_value)
        self.mic_op_gain_data = dict(Ra_value=22000, Rb_value=0)
        self.two_order_filter_data = dict(C1_value='22n', C2_value='22n', C_value_double='47n', R1_value=r_notch,
                                          R2_value=r_notch, R_half_value=r_notch_half, R_gain_value=0)
        self.two_order_filter_data_02 = dict(C1_value='22n', C2_value='22n', C_value_double='47n', R1_value=r_notch,
                                             R2_value=r_notch, R_half_value=r_notch_half, R_gain_value=0)
        self.one_order_highpass_data = dict(C_value='22n', R_value=r_notch)
        self.one_order_highpass_data_mode2 = dict(C_value='22n', R_value=r_notch, R2_value='1000k')
        self.one_order_lowpass_data = dict(C_value='22n', R_value=r_notch)

        self.op_gain_data = dict(Ra_value=r_op_gain, Rb_value=r_op_gain)
        self.op_lowpass_data = dict(C_value='4.7n')
        self.high_shelf_data = dict(C_value='470p', R_value=r_peak_shelf)
        self.low_shelf_data = dict(C_value='470p', R_value=r_peak_shelf)
        self.op_peak_data = dict(C1_value='8.2n', C2_value='8.2n', C_value_double='15n', R1_value=r_peak,
                                 R2_value=r_peak, R_half_value=r_peak_half, R_gain_value=0, R_high_cut=r_peak_double)
        self.two_order_lowpass_data = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                                           C2_value='12n')

        # 默认module01参数
        self.pixmapLabel.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
        self.amplitudeSlider.setHidden(True)
        self.frequencySpin.setHidden(True)
        self.frequencySpin_highpass.setHidden(True)
        self.highpass_gain_spin.setHidden(True)
        self.label_76.setHidden(True)
        self.label_Slider_value.setText('None')
        # 默认module02参数
        self.pixmapLabel_2.setPixmap(QtGui.QPixmap(':/mic/icon/Bypass.png'))
        self.amplitudeSlider_2.setHidden(True)
        self.frequencySpin_2.setHidden(True)
        self.frequencySpin_lowpass.setHidden(True)
        self.label_Slider_value_2.setText('None')
        # 默认module03参数
        self.label_15.setPixmap(QtGui.QPixmap(':/mic/icon/lowpass.png'))
        # module 08 peak filter参数
        self.label_11.setPixmap(QtGui.QPixmap(':/mic/icon/peak.png'))

    def set_default_module(self):
        self.op_model = 'two_op'
        self.ac_source = 'DC 2 AC 1 0'

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
        self.hs01_status = False
        self.ls01_status = False
        self.lp01_status = False
        self.two_order_lowpass_status = False

    def set_default_font(self):
        font = QtGui.QFont("SimSun", 9, QtGui.QFont.Normal)
        font.setPixelSize(12)
        self.setFont(font)

    def set_font(self):
        font, ok = QtWidgets.QFontDialog.getFont()
        if ok:
            self.setFont(font)

    def signals_slot(self):
        """
        UI界面信号与槽连接
        :return:
        """

        self.btn_set_font.clicked.connect(self.set_font)
        # Mic增益输入模块
        self.mic_gain_spin.valueChanged.connect(self.create_mic_op_gain_data)
        # AC信号源相位
        self.radioButton_noninverting_phase.toggled.connect(self.set_source)
        # OP02 是否启用控制，默认启用
        self.radioButton_one_op.toggled.connect(self.set_op_model)
        # FF FB设计选择，默认FF
        self.radioButton_ff_design.toggled.connect(self.ff_fb_design_chose)
        # filter_01模块单元按键
        self.filter01_radioButton_notch.toggled.connect(
            lambda: self.set_module_01(self.filter01_radioButton_notch))  # 功能复选框
        self.filter01_radioButton_bypass.toggled.connect(
            lambda: self.set_module_01(self.filter01_radioButton_bypass))
        self.filter01_radioButton_highpass.toggled.connect(
            lambda: self.set_module_01(self.filter01_radioButton_highpass))
        self.frequencySpin.valueChanged.connect(self.setupC_value)  # 计数器改变时调整电容值
        self.amplitudeSlider.valueChanged.connect(self.setupR_value)  # 滑块位置改变时调整电阻值
        self.frequencySpin_highpass.valueChanged.connect(self.setupC_value_highpass_mode2)  # 高通电容调整信号槽
        self.highpass_gain_spin.valueChanged.connect(self.setupR2_value_highpass_mode2)  # 高通电容调整信号槽

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
        # op peak
        self.OP_peak_filter_enable.toggled.connect(self.set_module_07)
        self.peak_frequency_spin.valueChanged.connect(self.set_module_07_data)
        self.peak_gain_spin.valueChanged.connect(self.set_module_07_data)
        self.peak_lowpass_slider.valueChanged.connect(self.set_module_07_data)
        self.peak_attenuation_slider.valueChanged.connect(self.set_module_07_data)
        # two order lowpass
        self.OP_lowpass_order_radio_bessel.toggled.connect(self.set_module_08)
        self.OP_lowpass_order_radio_butterworth.toggled.connect(self.set_module_08)
        self.OP_lowpass_order_radio_chebyshev.toggled.connect(self.set_module_08)
        self.chebyshev_1dB.toggled.connect(self.set_module_08)
        self.chebyshev_1dB_2.toggled.connect(self.set_module_08)
        self.chebyshev_1dB_3.toggled.connect(self.set_module_08)
        self.frequencySpin_OP_lowpass.valueChanged.connect(self.set_module_08)

        self.outputButton.clicked.connect(self.run_simulator)  # 仿真 创建circuit并开始仿真计算窗口
        self.AimCurveInButton.clicked.connect(self.import_aim_curve)  # 参考曲线 导入曲线按键时触发导入excel操作
        self.SPKFBInButton.clicked.connect(self.import_spk_fb)
        self.SPKArtEarInButton.clicked.connect(self.import_spk_artificial_ear)
        self.FbArtEarInButton.clicked.connect(self.import_fb_artificial_ear)
        self.ClosedLoopResultButton.clicked.connect(self.fb_result_forecast)
        self.export_bom_button.clicked.connect(self.export_bom)

        self.ImportSettings_FF.clicked.connect(self.ImportSettings_FF_clicked)  # 配置 信息导入
        self.SaveSettings_FF.clicked.connect(self.SaveSettings_FF_clicked)  # 配置 信息保存
        self.test_button.clicked.connect(self.reset_settings)  # 重置配置信息

        self.btn_notch01_tuning.clicked.connect(self.notch01_tuning)  # tuning
        self.btn_notch02_tuning.clicked.connect(self.notch02_tuning)
        self.btn_peak01_tuning.clicked.connect(self.peak01_tuning_all)
        self.btn_two_order_lowpass_tuning.clicked.connect(self.two_order_lowpass_tuning)

    # FF/FB设计选择
    def ff_fb_design_chose(self):
        if self.radioButton_ff_design.isChecked():
            self.PAInButton.setHidden(True)
            self.SPKFBInButton.setHidden(True)
            self.SPKArtEarInButton.setHidden(True)
            self.FbArtEarInButton.setHidden(True)
            self.ClosedLoopResultButton.setHidden(True)
        else:
            self.PAInButton.setHidden(True)
            self.SPKFBInButton.setHidden(False)
            self.SPKArtEarInButton.setHidden(False)
            self.FbArtEarInButton.setHidden(False)
            self.ClosedLoopResultButton.setHidden(False)

    # op02启用设置
    def set_op_model(self):
        """设置仿真计算是否启用OP02"""
        if self.radioButton_one_op.isChecked():
            self.op_model = 'one_op'
            self.tab_2.setEnabled(False)
        else:
            self.op_model = 'two_op'
            self.tab_2.setEnabled(True)

    # input信号源设置
    def set_source(self):
        if self.radioButton_noninverting_phase.isChecked():
            self.ac_source = 'DC 2 AC 1 0'
        else:
            self.ac_source = 'DC 2 AC 1 180'

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
        c_value = 1 / (2 * math.pi * self.default_notch_r_value * f)  # 默认电阻6.8k，c_value为浮点进度数值
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
            self.highpass_gain_spin.setHidden(True)
            self.label_76.setHidden(True)
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
            self.highpass_gain_spin.setHidden(True)
            self.label_76.setHidden(True)
            self.label_Slider_value.setText('None')
        if btn.text() == '高通' and btn.isChecked():
            self.pixmapLabel.setPixmap(QtGui.QPixmap(":/mic/icon/HighPass.png"))
            self.module01 = 'highpass'
            self.amplitudeSlider.setHidden(True)
            self.frequencySpin.setHidden(True)
            self.frequencySpin_highpass.setHidden(False)
            self.highpass_gain_spin.setHidden(False)
            self.label_76.setHidden(False)
            self.label_Slider_value.setText('None')

    def setupC_value_highpass(self):
        """根据选择的中心频率设置电容容值"""
        f = self.frequencySpin_highpass.value()  # 用户设置频率数值
        c_value = 1 / (2 * math.pi * self.default_notch_r_value * f)  # 默认电阻2.2k，c_value为浮点进度数值
        self.one_order_highpass_data['C_value'] = c_value2map(c_value)  # E12电容标准取值，str格式,ex:33nf
        # print(self.one_order_highpass_data.items())

    def setupC_value_highpass_mode2(self):
        """根据选择的中心频率设置电容容值"""
        f = self.frequencySpin_highpass.value()  # 用户设置频率数值
        c_value = 1 / (2 * math.pi * self.default_notch_r_value * f)  # 默认电阻2.2k，c_value为浮点进度数值
        self.one_order_highpass_data_mode2['C_value'] = c_value2map(c_value)  # E12电容标准取值，str格式,ex:33nf
        # print(self.one_order_highpass_data.items())

    def setupR2_value_highpass_mode2(self):
        """根据选择的中心频率设置电容容值"""
        gain = self.highpass_gain_spin.value()  # 用户设置频率数值
        rate = (10 ** (gain / 20))
        R2_value = self.default_notch_r_value * (1-rate) / rate
        self.one_order_highpass_data_mode2['R2_value'] = R_value2map(R2_value)  # E12电容标准取值，str格式,ex:33nf

    # module02模块参数设置
    def setupC_value_2(self):

        f = self.frequencySpin_2.value()  # 用户设置频率数值
        c_value = 1 / (2 * math.pi * self.default_notch_r_value * f)  # 默认电阻2.2k，c_value为浮点进度数值
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
        c_value = 1 / (2 * math.pi * self.default_notch_r_value * f)  # 默认电阻2.2k，c_value为浮点进度数值
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

        self.op_gain_data['Rb_value'] = self.get_Rb_value(gain)[0]

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
            R1 = self.default_peak_r_value / (10 ** ((gain - gain_op) / 20) - 1)  # 反相放大器增益计算法
            self.high_shelf_data['R_value'] = R_value2map(R1)

            f = self.high_shelf_frequency_spin.value()
            c_value = 1 / (2 * math.pi * R1 * f)
            self.high_shelf_data['C_value'] = c_value2map(c_value)
            if self.OP_highshelf_filter_enable.isChecked():
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
            Rb = self.default_peak_r_value * (10 ** (gain2 / 20))  # Rb_value 阻值计算
            R2 = self.default_peak_r_value * (10 ** ((gain2 + gain_op) / 20) / (
                    10 ** (gain2 / 20) - 10 ** (gain_op / 20)))  # low shelf R_value 阻值计算
            self.op_gain_data['Rb_value'] = R_value2map(Rb)
            self.low_shelf_data['R_value'] = R_value2map(R2)

            f = self.low_shelf_frequency_spin.value()
            c_value = 1 / (2 * math.pi * R2 * f)
            self.low_shelf_data['C_value'] = c_value2map(c_value)
            if self.OP_lowshelf_filter_enable.isChecked():
                self.module05 = 'low_shelf'
        else:
            self.module05 = None
            self.set_module03_data()

    # module 06 op lowpass
    def set_module_06(self):
        if self.OP_lowpass_filter_enable.isChecked() and self.OP_lowpass_order_radio_one.isChecked():
            self.groupBox_9.setEnabled(False)
            self.groupBox_10.setEnabled(False)
            self.groupBox_4.setEnabled(True)  # 启用low shelf, high shelf, peak
            self.groupBox_5.setEnabled(True)
            self.groupBox_6.setEnabled(True)
            self.label_15.setPixmap(QtGui.QPixmap(':/mic/icon/lowpass.png'))
            self.module03 = 'op_one_order'
            self.module06 = 'op_lowpass'
            self.set_module_06_data()
        elif self.OP_lowpass_filter_enable.isChecked() and self.OP_lowpass_order_radio_two.isChecked():
            self.module03 = 'op_two_order'
            self.module06 = None
        else:
            self.module03 = 'op_one_order'
            self.module06 = None

    def set_module_06_data(self):
        gain = self.OP_gain_spin.value()
        f = self.frequencySpin_OP_lowpass.value()
        r_value = self.get_Rb_value(gain)[1]
        c_value = 1 / (2 * math.pi * r_value * f)
        self.op_lowpass_data['C_value'] = c_value2map(c_value)

    # op peak module 07
    def set_module_07(self):
        if self.sender() == self.OP_gain_spin and not self.OP_peak_filter_enable.isChecked():
            self.op1_gain = self.OP_gain_spin.value()  # 记录op gain

        if self.OP_peak_filter_enable.isChecked():
            self.OP_lowpass_filter_enable.setChecked(False)  # 关闭 module03
            self.OP_lowshelf_filter_enable.setChecked(False)  # 关闭 module 05
            self.peak_gain_spin.setValue(self.peak01_gain)  # gain设置为记录值
            self.OP_gain_spin.setEnabled(False)
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
            self.OP_gain_spin.setEnabled(True)

            self.module07 = None
            if self.sender() == self.OP_peak_filter_enable:
                self.OP_gain_spin.setValue(self.op1_gain)  # 恢复记录值

    def set_module_07_data(self):
        self.peak01_gain = self.peak_gain_spin.value()  # 记录peak01 gain
        self.OP_gain_spin.setValue(self.peak_gain_spin.value())  # 同步op gain & peak gain
        gain = self.peak_gain_spin.value()  # 滤波器峰值增益
        f = self.peak_frequency_spin.value()  # 中心频率
        pos_r_high = self.peak_lowpass_slider.value()  # 高频抑制电阻阻值
        pos_r_gain = self.peak_attenuation_slider.value()  # Q值控制电阻阻值
        if self.peak01_status is False:
            if gain == 0:
                self.module07 = None
            else:
                Rb = self.get_Rb_value(gain)[1]
                R1 = self.default_peak_r_value * Rb / (Rb - self.default_peak_r_value) / 2
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

        gain = self.OP_gain_spin.value()  # 用户设置的增益
        f = self.frequencySpin_OP_lowpass.value()  # 用户设置的截止频率
        C1 = 4.7e-3
        k = 100 / (f * C1)  # 电阻换标系数
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
        if self.aim_curve_file_path:
            excel_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', self.aim_curve_file_path,
                                                                  'excel Files (*.xls *.xlsx);;txt Files (*.txt)')
        else:
            excel_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', '.',
                                                                  'excel Files (*.xls *.xlsx);;txt Files (*.txt)')
        self.aim_curve_file_path = excel_file
        if excel_file:
            try:
                excel_data = FilterImport(excel_file)
                self.aim_curve_data = excel_data
                self.AimCurveInButton.setDefault(True)
                QtWidgets.QMessageBox.information(self, '提示', '导入成功')
            except ValueError as e:
                QtWidgets.QMessageBox.warning(self, '提示', str(e), QtWidgets.QMessageBox.Yes)

    def import_spk_fb(self):
        """导入参考Filter目标曲线,参数保存为self.air_curve_data
        :return: OK
        """
        if self.aim_curve_file_path:
            excel_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', self.aim_curve_file_path,
                                                                  'excel Files (*.xls *.xlsx);;txt Files (*.txt)')
        else:
            excel_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', '.',
                                                                  'excel Files (*.xls *.xlsx);;txt Files (*.txt)')
        self.aim_curve_file_path = excel_file
        if excel_file:
            try:
                excel_data = FilterImport(excel_file)
                self.spk_fb_data = excel_data
                QtWidgets.QMessageBox.information(self, '提示', '导入成功')
            except ValueError as e:
                QtWidgets.QMessageBox.warning(self, '提示', str(e), QtWidgets.QMessageBox.Yes)

    def import_spk_artificial_ear(self):
        """导入参考Filter目标曲线,参数保存为self.air_curve_data
        :return: OK
        """
        if self.aim_curve_file_path:
            excel_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', self.aim_curve_file_path,
                                                                  'excel Files (*.xls *.xlsx);;txt Files (*.txt)')
        else:
            excel_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', '.',
                                                                  'excel Files (*.xls *.xlsx);;txt Files (*.txt)')
        self.aim_curve_file_path = excel_file
        if excel_file:
            try:
                excel_data = FilterImport(excel_file)
                self.spk_artificial_ear_data = excel_data
                QtWidgets.QMessageBox.information(self, '提示', '导入成功')
            except ValueError as e:
                QtWidgets.QMessageBox.warning(self, '提示', str(e), QtWidgets.QMessageBox.Yes)

    def import_fb_artificial_ear(self):
        """导入参考Filter目标曲线,参数保存为self.air_curve_data
        :return: OK
        """
        if self.aim_curve_file_path:
            excel_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', self.aim_curve_file_path,
                                                                  'excel Files (*.xls *.xlsx);;txt Files (*.txt)')
        else:
            excel_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', '.',
                                                                  'excel Files (*.xls *.xlsx);;txt Files (*.txt)')
        self.aim_curve_file_path = excel_file
        if excel_file:
            try:
                excel_data = FilterImport(excel_file)
                self.fb_artificial_ear_data = excel_data
                QtWidgets.QMessageBox.information(self, '提示', '导入成功')
            except ValueError as e:
                QtWidgets.QMessageBox.warning(self, '提示', str(e), QtWidgets.QMessageBox.Yes)

    # 创建circuit
    def create_netlist(self):
        """调用MyNetlistCreat类，创建电路图并进行仿真运算"""
        my_netlist = MyNetlistCreate(op_model=self.op_model, ac_source=self.ac_source,
                                     mic_op_gain_data=self.mic_op_gain_data,
                                     two_order_filter_data=self.two_order_filter_data, module_01=self.module01,
                                     two_order_filter_data_02=self.two_order_filter_data_02, module_02=self.module02,
                                     one_order_lowpass_data=self.one_order_lowpass_data,
                                     one_order_highpass_data=self.one_order_highpass_data_mode2,
                                     two_order_lowpass_data=self.two_order_lowpass_data,
                                     op_gain_data=self.op_gain_data, module_03=self.module03,
                                     high_shelf_data=self.high_shelf_data, module_04=self.module04,
                                     low_shelf_data=self.low_shelf_data, module_05=self.module05,
                                     op_lowpass_data=self.op_lowpass_data, module_06=self.module06,
                                     op_peak_data=self.op_peak_data, module_07=self.module07,
                                     two_order_filter_data_11=self.two_order_filter_data_11, module_11=self.module11,
                                     two_order_filter_data_12=self.two_order_filter_data_12, module_12=self.module12,
                                     one_order_highpass_data_2=self.one_order_highpass_data_2,
                                     one_order_lowpass_data_2=self.one_order_lowpass_data_2,
                                     two_order_lowpass_data_2=self.two_order_lowpass_data_2,
                                     op_gain_data_2=self.op_gain_data_2, module_13=self.module13,
                                     op_lowpass_data_2=self.op_lowpass_data_2, module_16=self.module16,
                                     high_shelf_data_2=self.high_shelf_data_2, module_14=self.module14,
                                     low_shelf_data_2=self.low_shelf_data_2, module_15=self.module15,
                                     op_peak_data_2=self.op_peak_data_2, module_17=self.module17)

        my_netlist.create_netlist()
        # print(self.module14)
        print(my_netlist.circuit)
        return my_netlist
        # self.run_simulator(my_netlist.circuit)

    def run_simulator(self):
        """根据电路网表图进行仿真计算
        :param netlist:
        :return:
        """
        my_netlist = self.create_netlist()
        analysis = self.simulator.my_simulator(my_netlist.circuit)  # 仿真计算
        self.simulator.my_bode_diagram(analysis, self.aim_curve_data, self.op_model)  # 绘制伯德图

    def fb_result_forecast(self):
        if self.spk_fb_data:
            my_netlist = self.create_netlist()
            analysis = self.simulator.my_simulator(my_netlist.circuit)  # 仿真计算
            self.simulator.my_fb_result_forecast(analysis, self.spk_fb_data, self.spk_artificial_ear_data,
                                                 self.fb_artificial_ear_data)

    # 导出BOM
    def export_bom(self):
        left_channel_01 = True
        right_channel_01 = True
        # left_channel_02 = False
        # right_channel_02 = False
        bom = list()
        if BOM_version == 1.0:  # L
            if left_channel_01:
                bom.append('LEFT CHANNEL 01: ' + '\n')
                bom.append('J31 short' + '\n')
                # module 01
                if self.module01 == 'notch':
                    # postil = ['C2', 'C5', 'C4', 'R4', 'R7', 'R6', 'R5']
                    bom.append('C127' + ' ' + self.two_order_filter_data['C1_value'] + '\n')
                    bom.append('C128' + ' ' + self.two_order_filter_data['C2_value'] + '\n')
                    bom.append('C126' + ' ' + self.two_order_filter_data['C_value_double'] + '\n')
                    bom.append('R139' + ' ' + self.two_order_filter_data['R1_value'] + '\n')
                    bom.append('R140' + ' ' + self.two_order_filter_data['R2_value'] + '\n')
                    bom.append('R142' + ' ' + self.two_order_filter_data['R_half_value'] + '\n')
                    bom.append('R141' + ' ' + str(self.two_order_filter_data['R_gain_value']) + '\n')
                elif self.module01 == 'highpass':
                    bom.append('C145' + ' ' + self.one_order_highpass_data_mode2['C_value'] + '\n')
                    bom.append('R159' + ' ' + self.one_order_highpass_data_mode2['R_value'] + '\n')
                    bom.append('R139' + ' ' + self.one_order_highpass_data_mode2['R2_value'] + '\n')
                    bom.append('R140' + ' ' + '0' + '\n')
                else:
                    bom.append('J29 short' + '\n')
                # module 02
                if self.module02 == 'notch':
                    # postil = ['C6', 'C9', 'C7', 'R9', 'R13', 'R12', 'R11']
                    bom.append('C130' + ' ' + self.two_order_filter_data_02['C1_value'] + '\n')
                    bom.append('C131' + ' ' + self.two_order_filter_data_02['C2_value'] + '\n')
                    bom.append('C139' + ' ' + self.two_order_filter_data_02['C_value_double'] + '\n')
                    bom.append('R143' + ' ' + self.two_order_filter_data_02['R1_value'] + '\n')
                    bom.append('R144' + ' ' + self.two_order_filter_data_02['R2_value'] + '\n')
                    bom.append('R146' + ' ' + self.two_order_filter_data_02['R_half_value'] + '\n')
                    bom.append('R145' + ' ' + str(self.two_order_filter_data_02['R_gain_value']) + '\n')
                elif self.module02 == 'lowpass':
                    bom.append('C146' + ' ' + self.one_order_lowpass_data['C_value'] + '\n')
                    bom.append('R160' + ' ' + self.one_order_lowpass_data['R_value'] + '\n')
                else:
                    bom.append('J30 short' + '\n')
                # module 03
                if self.module03 == 'op_one_order':
                    # self.op_gain_data = dict(Ra_value='20k', Rb_value='20k')
                    bom.append('R147' + ' ' + '0' + '\n')
                    bom.append('R148' + ' ' + self.op_gain_data['Ra_value'] + '\n')
                    bom.append('R161' + ' ' + self.op_gain_data['Rb_value'] + '\n')
                    bom.append('R157' + ' ' + '0' + '\n')
                else:
                    # self.two_order_lowpass_data = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                    #                                    C2_value='12n')
                    bom.append('R147' + ' ' + self.two_order_lowpass_data['R1_value'] + '\n')
                    bom.append('R148' + ' ' + '0' + '\n')
                    bom.append('R157' + ' ' + self.two_order_lowpass_data['R3_value'] + '\n')
                    bom.append('R158' + ' ' + self.two_order_lowpass_data['R2_value'] + '\n')
                    bom.append('C132' + ' ' + self.two_order_lowpass_data['C2_value'] + '\n')
                    bom.append('C138' + ' ' + self.two_order_lowpass_data['C1_value'] + '\n')
                # module 04
                if self.module04 == 'high_shelf':
                    # self.high_shelf_data = dict(C_value='680p', R_value='220k')
                    bom.append('R149' + ' ' + self.high_shelf_data['R_value'] + '\n')
                    bom.append('C133' + ' ' + self.high_shelf_data['C_value'] + '\n')
                # module 05
                if self.module05 == 'low_shelf':
                    # self.low_shelf_data = dict(C_value='680p', R_value='220k')
                    bom.append('C139' + ' ' + self.low_shelf_data['C_value'] + '\n')
                    bom.append('R162' + ' ' + self.low_shelf_data['R_value'] + '\n')
                # module 06
                if self.module06 == 'op_lowpass':
                    # self.op_lowpass_data = dict(C_value='8.2n')
                    bom.append('C140' + ' ' + self.op_lowpass_data['C_value'] + '\n')
                # module 07
                if self.module07 == 'peak':
                    # self.op_peak_data = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k',
                    #                          R2_value='20k',R_half_value='10k', R_gain_value=0, R_high_cut='39k')
                    bom.append('C136' + ' ' + self.op_peak_data['C1_value'] + '\n')
                    bom.append('C137' + ' ' + self.op_peak_data['C2_value'] + '\n')
                    bom.append('C134' + ' ' + self.op_peak_data['C_value_double'] + '\n')
                    bom.append('R150' + ' ' + self.op_peak_data['R1_value'] + '\n')
                    bom.append('R151' + ' ' + self.op_peak_data['R2_value'] + '\n')
                    bom.append('R154' + ' ' + self.op_peak_data['R_half_value'] + '\n')
                    bom.append('R152' + ' ' + str(self.op_peak_data['R_gain_value']) + '\n')
                    bom.append('R153' + ' ' + self.op_peak_data['R_high_cut'] + '\n')
                    bom.append('R155' + ' ' + '0' + '\n')
                    bom.append('R156' + ' ' + '0' + '\n')

                # OP 02
                if self.op_model == 'two_op':
                    bom.append('J34 short' + '\n')
                    # module 11
                    if self.module11 == 'notch':
                        bom.append('C142' + ' ' + self.two_order_filter_data_11['C1_value'] + '\n')
                        bom.append('C143' + ' ' + self.two_order_filter_data_11['C2_value'] + '\n')
                        bom.append('C141' + ' ' + self.two_order_filter_data_11['C_value_double'] + '\n')
                        bom.append('R163' + ' ' + self.two_order_filter_data_11['R1_value'] + '\n')
                        bom.append('R164' + ' ' + self.two_order_filter_data_11['R2_value'] + '\n')
                        bom.append('R166' + ' ' + self.two_order_filter_data_11['R_half_value'] + '\n')
                        bom.append('R165' + ' ' + str(self.two_order_filter_data_11['R_gain_value']) + '\n')
                    elif self.module11 == 'highpass':
                        bom.append('C149' + ' ' + self.one_order_highpass_data_2['C_value'] + '\n')
                        bom.append('R171' + ' ' + self.one_order_highpass_data_2['R_value'] + '\n')
                    else:
                        bom.append('J35 short' + '\n')
                    # module 12
                    if self.module12 == 'notch':
                        bom.append('C147' + ' ' + self.two_order_filter_data_12['C1_value'] + '\n')
                        bom.append('C148' + ' ' + self.two_order_filter_data_12['C2_value'] + '\n')
                        bom.append('C144' + ' ' + self.two_order_filter_data_12['C_value_double'] + '\n')
                        bom.append('R167' + ' ' + self.two_order_filter_data_12['R1_value'] + '\n')
                        bom.append('R168' + ' ' + self.two_order_filter_data_12['R2_value'] + '\n')
                        bom.append('R170' + ' ' + self.two_order_filter_data_12['R_half_value'] + '\n')
                        bom.append('R169' + ' ' + str(self.two_order_filter_data_12['R_gain_value']) + '\n')
                    elif self.module12 == 'lowpass':
                        bom.append('C150' + ' ' + self.one_order_lowpass_data_2['C_value'] + '\n')
                        bom.append('R172' + ' ' + self.one_order_lowpass_data_2['R_value'] + '\n')
                    else:
                        bom.append('J36 short' + '\n')
                    # module 13
                    if self.module13 == 'op_one_order':
                        # self.op_gain_data_2 = dict(Ra_value='20k', Rb_value='20k')
                        bom.append('R173' + ' ' + '0' + '\n')
                        bom.append('R174' + ' ' + self.op_gain_data_2['Ra_value'] + '\n')
                        bom.append('R185' + ' ' + self.op_gain_data_2['Rb_value'] + '\n')
                        bom.append('R183' + ' ' + '0' + '\n')
                    else:
                        # self.two_order_lowpass_data_2 = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                        #                                    C2_value='12n')
                        bom.append('R173' + ' ' + self.two_order_lowpass_data_2['R1_value'] + '\n')
                        bom.append('R174' + ' ' + '0' + '\n')
                        bom.append('R183' + ' ' + self.two_order_lowpass_data_2['R3_value'] + '\n')
                        bom.append('R184' + ' ' + self.two_order_lowpass_data_2['R2_value'] + '\n')
                        bom.append('C151' + ' ' + self.two_order_lowpass_data_2['C2_value'] + '\n')
                        bom.append('C157' + ' ' + self.two_order_lowpass_data_2['C1_value'] + '\n')
                    # module 14
                    if self.module14 == 'high_shelf':
                        # self.high_shelf_data_2 = dict(C_value='680p', R_value='220k')
                        bom.append('R175' + ' ' + self.high_shelf_data_2['R_value'] + '\n')
                        bom.append('C152' + ' ' + self.high_shelf_data_2['C_value'] + '\n')
                    # module 15
                    if self.module15 == 'low_shelf':
                        # self.low_shelf_data_2 = dict(C_value='680p', R_value='220k')
                        bom.append('C158' + ' ' + self.low_shelf_data_2['C_value'] + '\n')
                        bom.append('R186' + ' ' + self.low_shelf_data_2['R_value'] + '\n')
                    # module 16
                    if self.module16 == 'op_lowpass':
                        # self.op_lowpass_data_2 = dict(C_value='8.2n')
                        bom.append('C159' + ' ' + self.op_lowpass_data_2['C_value'] + '\n')
                    # module 17
                    if self.module17 == 'peak':
                        # self.op_peak_data_2 = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k',
                        #                          R2_value='20k',R_half_value='10k', R_gain_value=0, R_high_cut='39k')
                        bom.append('C155' + ' ' + self.op_peak_data_2['C1_value'] + '\n')
                        bom.append('C156' + ' ' + self.op_peak_data_2['C2_value'] + '\n')
                        bom.append('C153' + ' ' + self.op_peak_data_2['C_value_double'] + '\n')
                        bom.append('R176' + ' ' + self.op_peak_data_2['R1_value'] + '\n')
                        bom.append('R177' + ' ' + self.op_peak_data_2['R2_value'] + '\n')
                        bom.append('R180' + ' ' + self.op_peak_data_2['R_half_value'] + '\n')
                        bom.append('R178' + ' ' + str(self.op_peak_data_2['R_gain_value']) + '\n')
                        bom.append('R179' + ' ' + self.op_peak_data_2['R_high_cut'] + '\n')
                        bom.append('R181' + ' ' + '0' + '\n')
                        bom.append('R182' + ' ' + '0' + '\n')

                bom.append('LEFT CHANNEL: ' + '\n')
                # module 01
                if self.module01 == 'notch':
                    # postil = ['C2', 'C5', 'C4', 'R4', 'R7', 'R6', 'R5']
                    bom.append('C127' + ' ' + self.two_order_filter_data['C1_value'] + '\n')
                    bom.append('C128' + ' ' + self.two_order_filter_data['C2_value'] + '\n')
                    bom.append('C126' + ' ' + self.two_order_filter_data['C_value_double'] + '\n')
                    bom.append('R139' + ' ' + self.two_order_filter_data['R1_value'] + '\n')
                    bom.append('R140' + ' ' + self.two_order_filter_data['R2_value'] + '\n')
                    bom.append('R142' + ' ' + self.two_order_filter_data['R_half_value'] + '\n')
                    bom.append('R141' + ' ' + str(self.two_order_filter_data['R_gain_value']) + '\n')
                elif self.module01 == 'highpass':
                    bom.append('C145' + ' ' + self.one_order_highpass_data_mode2['C_value'] + '\n')
                    bom.append('R159' + ' ' + self.one_order_highpass_data_mode2['R_value'] + '\n')
                    bom.append('R139' + ' ' + self.one_order_highpass_data_mode2['R2_value'] + '\n')
                    bom.append('R140' + ' ' + '0' + '\n')
                else:
                    bom.append('J29 short' + '\n')
                # module 02
                if self.module02 == 'notch':
                    # postil = ['C6', 'C9', 'C7', 'R9', 'R13', 'R12', 'R11']
                    bom.append('C130' + ' ' + self.two_order_filter_data_02['C1_value'] + '\n')
                    bom.append('C131' + ' ' + self.two_order_filter_data_02['C2_value'] + '\n')
                    bom.append('C139' + ' ' + self.two_order_filter_data_02['C_value_double'] + '\n')
                    bom.append('R143' + ' ' + self.two_order_filter_data_02['R1_value'] + '\n')
                    bom.append('R144' + ' ' + self.two_order_filter_data_02['R2_value'] + '\n')
                    bom.append('R146' + ' ' + self.two_order_filter_data_02['R_half_value'] + '\n')
                    bom.append('R145' + ' ' + str(self.two_order_filter_data_02['R_gain_value']) + '\n')
                elif self.module02 == 'lowpass':
                    bom.append('C146' + ' ' + self.one_order_lowpass_data['C_value'] + '\n')
                    bom.append('R160' + ' ' + self.one_order_lowpass_data['R_value'] + '\n')
                else:
                    bom.append('J30 short' + '\n')
                # module 03
                if self.module03 == 'op_one_order':
                    # self.op_gain_data = dict(Ra_value='20k', Rb_value='20k')
                    bom.append('R147' + ' ' + '0' + '\n')
                    bom.append('R148' + ' ' + self.op_gain_data['Ra_value'] + '\n')
                    bom.append('R161' + ' ' + self.op_gain_data['Rb_value'] + '\n')
                    bom.append('R157' + ' ' + '0' + '\n')
                else:
                    # self.two_order_lowpass_data = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                    #                                    C2_value='12n')
                    bom.append('R147' + ' ' + self.two_order_lowpass_data['R1_value'] + '\n')
                    bom.append('R148' + ' ' + '0' + '\n')
                    bom.append('R157' + ' ' + self.two_order_lowpass_data['R3_value'] + '\n')
                    bom.append('R208' + ' ' + self.two_order_lowpass_data['R2_value'] + '\n')
                    bom.append('C132' + ' ' + self.two_order_lowpass_data['C2_value'] + '\n')
                    bom.append('C138' + ' ' + self.two_order_lowpass_data['C1_value'] + '\n')
                # module 04
                if self.module04 == 'high_shelf':
                    # self.high_shelf_data = dict(C_value='680p', R_value='220k')
                    bom.append('R149' + ' ' + self.high_shelf_data['R_value'] + '\n')
                    bom.append('C133' + ' ' + self.high_shelf_data['C_value'] + '\n')
                # module 05
                if self.module05 == 'low_shelf':
                    # self.low_shelf_data = dict(C_value='680p', R_value='220k')
                    bom.append('C139' + ' ' + self.low_shelf_data['C_value'] + '\n')
                    bom.append('R162' + ' ' + self.low_shelf_data['R_value'] + '\n')
                # module 06
                if self.module06 == 'op_lowpass':
                    # self.op_lowpass_data = dict(C_value='8.2n')
                    bom.append('C140' + ' ' + self.op_lowpass_data['C_value'] + '\n')
                # module 07
                if self.module07 == 'peak':
                    # self.op_peak_data = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k',
                    #                          R2_value='20k',R_half_value='10k', R_gain_value=0, R_high_cut='39k')
                    bom.append('C136' + ' ' + self.op_peak_data['C1_value'] + '\n')
                    bom.append('C137' + ' ' + self.op_peak_data['C2_value'] + '\n')
                    bom.append('C134' + ' ' + self.op_peak_data['C_value_double'] + '\n')
                    bom.append('R150' + ' ' + self.op_peak_data['R1_value'] + '\n')
                    bom.append('R151' + ' ' + self.op_peak_data['R2_value'] + '\n')
                    bom.append('R154' + ' ' + self.op_peak_data['R_half_value'] + '\n')
                    bom.append('R152' + ' ' + str(self.op_peak_data['R_gain_value']) + '\n')
                    bom.append('R153' + ' ' + self.op_peak_data['R_high_cut'] + '\n')
                    bom.append('R155' + ' ' + '0' + '\n')
                    bom.append('R156' + ' ' + '0' + '\n')

                # OP 02
                if self.op_model == 'two_op':
                    bom.append('J34 short' + '\n')
                    # module 11
                    if self.module11 == 'notch':
                        bom.append('C142' + ' ' + self.two_order_filter_data_11['C1_value'] + '\n')
                        bom.append('C143' + ' ' + self.two_order_filter_data_11['C2_value'] + '\n')
                        bom.append('C141' + ' ' + self.two_order_filter_data_11['C_value_double'] + '\n')
                        bom.append('R163' + ' ' + self.two_order_filter_data_11['R1_value'] + '\n')
                        bom.append('R164' + ' ' + self.two_order_filter_data_11['R2_value'] + '\n')
                        bom.append('R166' + ' ' + self.two_order_filter_data_11['R_half_value'] + '\n')
                        bom.append('R165' + ' ' + str(self.two_order_filter_data_11['R_gain_value']) + '\n')
                    elif self.module11 == 'highpass':
                        bom.append('C149' + ' ' + self.one_order_highpass_data_2['C_value'] + '\n')
                        bom.append('R171' + ' ' + self.one_order_highpass_data_2['R_value'] + '\n')
                    else:
                        bom.append('J35 short' + '\n')
                    # module 12
                    if self.module12 == 'notch':
                        bom.append('C147' + ' ' + self.two_order_filter_data_12['C1_value'] + '\n')
                        bom.append('C148' + ' ' + self.two_order_filter_data_12['C2_value'] + '\n')
                        bom.append('C144' + ' ' + self.two_order_filter_data_12['C_value_double'] + '\n')
                        bom.append('R167' + ' ' + self.two_order_filter_data_12['R1_value'] + '\n')
                        bom.append('R168' + ' ' + self.two_order_filter_data_12['R2_value'] + '\n')
                        bom.append('R170' + ' ' + self.two_order_filter_data_12['R_half_value'] + '\n')
                        bom.append('R169' + ' ' + str(self.two_order_filter_data_12['R_gain_value']) + '\n')
                    elif self.module12 == 'lowpass':
                        bom.append('C150' + ' ' + self.one_order_lowpass_data_2['C_value'] + '\n')
                        bom.append('R172' + ' ' + self.one_order_lowpass_data_2['R_value'] + '\n')
                    else:
                        bom.append('J36 short' + '\n')
                    # module 13
                    if self.module13 == 'op_one_order':
                        # self.op_gain_data_2 = dict(Ra_value='20k', Rb_value='20k')
                        bom.append('R173' + ' ' + '0' + '\n')
                        bom.append('R174' + ' ' + self.op_gain_data_2['Ra_value'] + '\n')
                        bom.append('R185' + ' ' + self.op_gain_data_2['Rb_value'] + '\n')
                        bom.append('R183' + ' ' + '0' + '\n')
                    else:
                        # self.two_order_lowpass_data_2 = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                        #                                    C2_value='12n')
                        bom.append('R173' + ' ' + self.two_order_lowpass_data_2['R1_value'] + '\n')
                        bom.append('R174' + ' ' + '0' + '\n')
                        bom.append('R183' + ' ' + self.two_order_lowpass_data_2['R3_value'] + '\n')
                        bom.append('R184' + ' ' + self.two_order_lowpass_data_2['R2_value'] + '\n')
                        bom.append('C151' + ' ' + self.two_order_lowpass_data_2['C2_value'] + '\n')
                        bom.append('C157' + ' ' + self.two_order_lowpass_data_2['C1_value'] + '\n')
                    # module 14
                    if self.module14 == 'high_shelf':
                        # self.high_shelf_data_2 = dict(C_value='680p', R_value='220k')
                        bom.append('R175' + ' ' + self.high_shelf_data_2['R_value'] + '\n')
                        bom.append('C152' + ' ' + self.high_shelf_data_2['C_value'] + '\n')
                    # module 15
                    if self.module15 == 'low_shelf':
                        # self.low_shelf_data_2 = dict(C_value='680p', R_value='220k')
                        bom.append('C158' + ' ' + self.low_shelf_data_2['C_value'] + '\n')
                        bom.append('R186' + ' ' + self.low_shelf_data_2['R_value'] + '\n')
                    # module 16
                    if self.module16 == 'op_lowpass':
                        # self.op_lowpass_data_2 = dict(C_value='8.2n')
                        bom.append('C159' + ' ' + self.op_lowpass_data_2['C_value'] + '\n')
                    # module 17
                    if self.module17 == 'peak':
                        # self.op_peak_data_2 = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k',
                        #                          R2_value='20k',R_half_value='10k', R_gain_value=0, R_high_cut='39k')
                        bom.append('C155' + ' ' + self.op_peak_data_2['C1_value'] + '\n')
                        bom.append('C156' + ' ' + self.op_peak_data_2['C2_value'] + '\n')
                        bom.append('C153' + ' ' + self.op_peak_data_2['C_value_double'] + '\n')
                        bom.append('R176' + ' ' + self.op_peak_data_2['R1_value'] + '\n')
                        bom.append('R177' + ' ' + self.op_peak_data_2['R2_value'] + '\n')
                        bom.append('R180' + ' ' + self.op_peak_data_2['R_half_value'] + '\n')
                        bom.append('R178' + ' ' + str(self.op_peak_data_2['R_gain_value']) + '\n')
                        bom.append('R179' + ' ' + self.op_peak_data_2['R_high_cut'] + '\n')
                        bom.append('R181' + ' ' + '0' + '\n')
                        bom.append('R182' + ' ' + '0' + '\n')
            if right_channel_01:
                bom.append('RIGHT CHANNEL 01: ' + '\n')
                bom.append('J41 short' + '\n')
                # module 01
                if self.module01 == 'notch':
                    # postil = ['C2', 'C5', 'C4', 'R4', 'R7', 'R6', 'R5']
                    bom.append('C161' + ' ' + self.two_order_filter_data['C1_value'] + '\n')
                    bom.append('C162' + ' ' + self.two_order_filter_data['C2_value'] + '\n')
                    bom.append('C160' + ' ' + self.two_order_filter_data['C_value_double'] + '\n')
                    bom.append('R187' + ' ' + self.two_order_filter_data['R1_value'] + '\n')
                    bom.append('R188' + ' ' + self.two_order_filter_data['R2_value'] + '\n')
                    bom.append('R190' + ' ' + self.two_order_filter_data['R_half_value'] + '\n')
                    bom.append('R189' + ' ' + str(self.two_order_filter_data['R_gain_value']) + '\n')
                elif self.module01 == 'highpass':
                    bom.append('C166' + ' ' + self.one_order_highpass_data_mode2['C_value'] + '\n')
                    bom.append('R195' + ' ' + self.one_order_highpass_data_mode2['R_value'] + '\n')
                    bom.append('R187' + ' ' + self.one_order_highpass_data_mode2['R2_value'] + '\n')
                    bom.append('R188' + ' ' + '0' + '\n')
                else:
                    bom.append('J37 short' + '\n')
                # module 02
                if self.module02 == 'notch':
                    # postil = ['C6', 'C9', 'C7', 'R9', 'R13', 'R12', 'R11']
                    bom.append('C164' + ' ' + self.two_order_filter_data_02['C1_value'] + '\n')
                    bom.append('C165' + ' ' + self.two_order_filter_data_02['C2_value'] + '\n')
                    bom.append('C163' + ' ' + self.two_order_filter_data_02['C_value_double'] + '\n')
                    bom.append('R191' + ' ' + self.two_order_filter_data_02['R1_value'] + '\n')
                    bom.append('R192' + ' ' + self.two_order_filter_data_02['R2_value'] + '\n')
                    bom.append('R194' + ' ' + self.two_order_filter_data_02['R_half_value'] + '\n')
                    bom.append('R193' + ' ' + str(self.two_order_filter_data_02['R_gain_value']) + '\n')
                elif self.module02 == 'lowpass':
                    bom.append('C167' + ' ' + self.one_order_lowpass_data['C_value'] + '\n')
                    bom.append('R196' + ' ' + self.one_order_lowpass_data['R_value'] + '\n')
                else:
                    bom.append('J40 short' + '\n')
                # module 03
                if self.module03 == 'op_one_order':
                    # self.op_gain_data = dict(Ra_value='20k', Rb_value='20k')
                    bom.append('R197' + ' ' + '0' + '\n')
                    bom.append('R198' + ' ' + self.op_gain_data['Ra_value'] + '\n')
                    bom.append('R209' + ' ' + self.op_gain_data['Rb_value'] + '\n')
                    bom.append('R207' + ' ' + '0' + '\n')
                else:
                    # self.two_order_lowpass_data = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                    #                                    C2_value='12n')
                    bom.append('R197' + ' ' + self.two_order_lowpass_data['R1_value'] + '\n')
                    bom.append('R198' + ' ' + '0' + '\n')
                    bom.append('R207' + ' ' + self.two_order_lowpass_data['R3_value'] + '\n')
                    bom.append('R208' + ' ' + self.two_order_lowpass_data['R2_value'] + '\n')
                    bom.append('C168' + ' ' + self.two_order_lowpass_data['C2_value'] + '\n')
                    bom.append('C174' + ' ' + self.two_order_lowpass_data['C1_value'] + '\n')
                # module 04
                if self.module04 == 'high_shelf':
                    # self.high_shelf_data = dict(C_value='680p', R_value='220k')
                    bom.append('R149' + ' ' + self.high_shelf_data['R_value'] + '\n')
                    bom.append('C133' + ' ' + self.high_shelf_data['C_value'] + '\n')
                # module 05
                if self.module05 == 'low_shelf':
                    # self.low_shelf_data = dict(C_value='680p', R_value='220k')
                    bom.append('C139' + ' ' + self.low_shelf_data['C_value'] + '\n')
                    bom.append('R162' + ' ' + self.low_shelf_data['R_value'] + '\n')
                # module 06
                if self.module06 == 'op_lowpass':
                    # self.op_lowpass_data = dict(C_value='8.2n')
                    bom.append('C140' + ' ' + self.op_lowpass_data['C_value'] + '\n')
                # module 07
                if self.module07 == 'peak':
                    # self.op_peak_data = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k',
                    #                          R2_value='20k',R_half_value='10k', R_gain_value=0, R_high_cut='39k')
                    bom.append('C136' + ' ' + self.op_peak_data['C1_value'] + '\n')
                    bom.append('C137' + ' ' + self.op_peak_data['C2_value'] + '\n')
                    bom.append('C134' + ' ' + self.op_peak_data['C_value_double'] + '\n')
                    bom.append('R150' + ' ' + self.op_peak_data['R1_value'] + '\n')
                    bom.append('R151' + ' ' + self.op_peak_data['R2_value'] + '\n')
                    bom.append('R154' + ' ' + self.op_peak_data['R_half_value'] + '\n')
                    bom.append('R152' + ' ' + str(self.op_peak_data['R_gain_value']) + '\n')
                    bom.append('R153' + ' ' + self.op_peak_data['R_high_cut'] + '\n')
                    bom.append('R155' + ' ' + '0' + '\n')
                    bom.append('R156' + ' ' + '0' + '\n')

                # OP 02
                if self.op_model == 'two_op':
                    bom.append('J34 short' + '\n')
                    # module 11
                    if self.module11 == 'notch':
                        bom.append('C142' + ' ' + self.two_order_filter_data_11['C1_value'] + '\n')
                        bom.append('C143' + ' ' + self.two_order_filter_data_11['C2_value'] + '\n')
                        bom.append('C141' + ' ' + self.two_order_filter_data_11['C_value_double'] + '\n')
                        bom.append('R163' + ' ' + self.two_order_filter_data_11['R1_value'] + '\n')
                        bom.append('R164' + ' ' + self.two_order_filter_data_11['R2_value'] + '\n')
                        bom.append('R166' + ' ' + self.two_order_filter_data_11['R_half_value'] + '\n')
                        bom.append('R165' + ' ' + str(self.two_order_filter_data_11['R_gain_value']) + '\n')
                    elif self.module11 == 'highpass':
                        bom.append('C149' + ' ' + self.one_order_highpass_data_2['C_value'] + '\n')
                        bom.append('R171' + ' ' + self.one_order_highpass_data_2['R_value'] + '\n')
                    else:
                        bom.append('J35 short' + '\n')
                    # module 12
                    if self.module12 == 'notch':
                        bom.append('C147' + ' ' + self.two_order_filter_data_12['C1_value'] + '\n')
                        bom.append('C148' + ' ' + self.two_order_filter_data_12['C2_value'] + '\n')
                        bom.append('C144' + ' ' + self.two_order_filter_data_12['C_value_double'] + '\n')
                        bom.append('R167' + ' ' + self.two_order_filter_data_12['R1_value'] + '\n')
                        bom.append('R168' + ' ' + self.two_order_filter_data_12['R2_value'] + '\n')
                        bom.append('R170' + ' ' + self.two_order_filter_data_12['R_half_value'] + '\n')
                        bom.append('R169' + ' ' + str(self.two_order_filter_data_12['R_gain_value']) + '\n')
                    elif self.module12 == 'lowpass':
                        bom.append('C150' + ' ' + self.one_order_lowpass_data_2['C_value'] + '\n')
                        bom.append('R172' + ' ' + self.one_order_lowpass_data_2['R_value'] + '\n')
                    else:
                        bom.append('J36 short' + '\n')
                    # module 13
                    if self.module13 == 'op_one_order':
                        # self.op_gain_data_2 = dict(Ra_value='20k', Rb_value='20k')
                        bom.append('R173' + ' ' + '0' + '\n')
                        bom.append('R174' + ' ' + self.op_gain_data_2['Ra_value'] + '\n')
                        bom.append('R185' + ' ' + self.op_gain_data_2['Rb_value'] + '\n')
                        bom.append('R183' + ' ' + '0' + '\n')
                    else:
                        # self.two_order_lowpass_data_2 = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                        #                                    C2_value='12n')
                        bom.append('R173' + ' ' + self.two_order_lowpass_data_2['R1_value'] + '\n')
                        bom.append('R174' + ' ' + '0' + '\n')
                        bom.append('R183' + ' ' + self.two_order_lowpass_data_2['R3_value'] + '\n')
                        bom.append('R184' + ' ' + self.two_order_lowpass_data_2['R2_value'] + '\n')
                        bom.append('C151' + ' ' + self.two_order_lowpass_data_2['C2_value'] + '\n')
                        bom.append('C157' + ' ' + self.two_order_lowpass_data_2['C1_value'] + '\n')
                    # module 14
                    if self.module14 == 'high_shelf':
                        # self.high_shelf_data_2 = dict(C_value='680p', R_value='220k')
                        bom.append('R175' + ' ' + self.high_shelf_data_2['R_value'] + '\n')
                        bom.append('C152' + ' ' + self.high_shelf_data_2['C_value'] + '\n')
                    # module 15
                    if self.module15 == 'low_shelf':
                        # self.low_shelf_data_2 = dict(C_value='680p', R_value='220k')
                        bom.append('C158' + ' ' + self.low_shelf_data_2['C_value'] + '\n')
                        bom.append('R186' + ' ' + self.low_shelf_data_2['R_value'] + '\n')
                    # module 16
                    if self.module16 == 'op_lowpass':
                        # self.op_lowpass_data_2 = dict(C_value='8.2n')
                        bom.append('C159' + ' ' + self.op_lowpass_data_2['C_value'] + '\n')
                    # module 17
                    if self.module17 == 'peak':
                        # self.op_peak_data_2 = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k',
                        #                          R2_value='20k',R_half_value='10k', R_gain_value=0, R_high_cut='39k')
                        bom.append('C155' + ' ' + self.op_peak_data_2['C1_value'] + '\n')
                        bom.append('C156' + ' ' + self.op_peak_data_2['C2_value'] + '\n')
                        bom.append('C153' + ' ' + self.op_peak_data_2['C_value_double'] + '\n')
                        bom.append('R176' + ' ' + self.op_peak_data_2['R1_value'] + '\n')
                        bom.append('R177' + ' ' + self.op_peak_data_2['R2_value'] + '\n')
                        bom.append('R180' + ' ' + self.op_peak_data_2['R_half_value'] + '\n')
                        bom.append('R178' + ' ' + str(self.op_peak_data_2['R_gain_value']) + '\n')
                        bom.append('R179' + ' ' + self.op_peak_data_2['R_high_cut'] + '\n')
                        bom.append('R181' + ' ' + '0' + '\n')
                        bom.append('R182' + ' ' + '0' + '\n')

                bom.append('LEFT CHANNEL: ' + '\n')
                # module 01
                if self.module01 == 'notch':
                    # postil = ['C2', 'C5', 'C4', 'R4', 'R7', 'R6', 'R5']
                    bom.append('C127' + ' ' + self.two_order_filter_data['C1_value'] + '\n')
                    bom.append('C128' + ' ' + self.two_order_filter_data['C2_value'] + '\n')
                    bom.append('C126' + ' ' + self.two_order_filter_data['C_value_double'] + '\n')
                    bom.append('R139' + ' ' + self.two_order_filter_data['R1_value'] + '\n')
                    bom.append('R140' + ' ' + self.two_order_filter_data['R2_value'] + '\n')
                    bom.append('R142' + ' ' + self.two_order_filter_data['R_half_value'] + '\n')
                    bom.append('R141' + ' ' + str(self.two_order_filter_data['R_gain_value']) + '\n')
                elif self.module01 == 'highpass':
                    bom.append('C145' + ' ' + self.one_order_highpass_data_mode2['C_value'] + '\n')
                    bom.append('R159' + ' ' + self.one_order_highpass_data_mode2['R_value'] + '\n')
                    bom.append('R139' + ' ' + self.one_order_highpass_data_mode2['R2_value'] + '\n')
                    bom.append('R140' + ' ' + '0' + '\n')
                else:
                    bom.append('J29 short' + '\n')
                # module 02
                if self.module02 == 'notch':
                    # postil = ['C6', 'C9', 'C7', 'R9', 'R13', 'R12', 'R11']
                    bom.append('C130' + ' ' + self.two_order_filter_data_02['C1_value'] + '\n')
                    bom.append('C131' + ' ' + self.two_order_filter_data_02['C2_value'] + '\n')
                    bom.append('C139' + ' ' + self.two_order_filter_data_02['C_value_double'] + '\n')
                    bom.append('R143' + ' ' + self.two_order_filter_data_02['R1_value'] + '\n')
                    bom.append('R144' + ' ' + self.two_order_filter_data_02['R2_value'] + '\n')
                    bom.append('R146' + ' ' + self.two_order_filter_data_02['R_half_value'] + '\n')
                    bom.append('R145' + ' ' + str(self.two_order_filter_data_02['R_gain_value']) + '\n')
                elif self.module02 == 'lowpass':
                    bom.append('C146' + ' ' + self.one_order_lowpass_data['C_value'] + '\n')
                    bom.append('R160' + ' ' + self.one_order_lowpass_data['R_value'] + '\n')
                else:
                    bom.append('J30 short' + '\n')
                # module 03
                if self.module03 == 'op_one_order':
                    # self.op_gain_data = dict(Ra_value='20k', Rb_value='20k')
                    bom.append('R147' + ' ' + '0' + '\n')
                    bom.append('R148' + ' ' + self.op_gain_data['Ra_value'] + '\n')
                    bom.append('R161' + ' ' + self.op_gain_data['Rb_value'] + '\n')
                    bom.append('R157' + ' ' + '0' + '\n')
                else:
                    # self.two_order_lowpass_data = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                    #                                    C2_value='12n')
                    bom.append('R147' + ' ' + self.two_order_lowpass_data['R1_value'] + '\n')
                    bom.append('R148' + ' ' + '0' + '\n')
                    bom.append('R157' + ' ' + self.two_order_lowpass_data['R3_value'] + '\n')
                    bom.append('R208' + ' ' + self.two_order_lowpass_data['R2_value'] + '\n')
                    bom.append('C132' + ' ' + self.two_order_lowpass_data['C2_value'] + '\n')
                    bom.append('C138' + ' ' + self.two_order_lowpass_data['C1_value'] + '\n')
                # module 04
                if self.module04 == 'high_shelf':
                    # self.high_shelf_data = dict(C_value='680p', R_value='220k')
                    bom.append('R199' + ' ' + self.high_shelf_data['R_value'] + '\n')
                    bom.append('C169' + ' ' + self.high_shelf_data['C_value'] + '\n')
                # module 05
                if self.module05 == 'low_shelf':
                    # self.low_shelf_data = dict(C_value='680p', R_value='220k')
                    bom.append('C175' + ' ' + self.low_shelf_data['C_value'] + '\n')
                    bom.append('R210' + ' ' + self.low_shelf_data['R_value'] + '\n')
                # module 06
                if self.module06 == 'op_lowpass':
                    # self.op_lowpass_data = dict(C_value='8.2n')
                    bom.append('C176' + ' ' + self.op_lowpass_data['C_value'] + '\n')
                # module 07
                if self.module07 == 'peak':
                    # self.op_peak_data = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k',
                    #                          R2_value='20k',R_half_value='10k', R_gain_value=0, R_high_cut='39k')
                    bom.append('C172' + ' ' + self.op_peak_data['C1_value'] + '\n')
                    bom.append('C173' + ' ' + self.op_peak_data['C2_value'] + '\n')
                    bom.append('C170' + ' ' + self.op_peak_data['C_value_double'] + '\n')
                    bom.append('R200' + ' ' + self.op_peak_data['R1_value'] + '\n')
                    bom.append('R201' + ' ' + self.op_peak_data['R2_value'] + '\n')
                    bom.append('R204' + ' ' + self.op_peak_data['R_half_value'] + '\n')
                    bom.append('R202' + ' ' + str(self.op_peak_data['R_gain_value']) + '\n')
                    bom.append('R203' + ' ' + self.op_peak_data['R_high_cut'] + '\n')
                    bom.append('R205' + ' ' + '0' + '\n')
                    bom.append('R206' + ' ' + '0' + '\n')

                # OP 02
                if self.op_model == 'two_op':
                    bom.append('J44 short' + '\n')
                    # module 11
                    if self.module11 == 'notch':
                        bom.append('C178' + ' ' + self.two_order_filter_data_11['C1_value'] + '\n')
                        bom.append('C179' + ' ' + self.two_order_filter_data_11['C2_value'] + '\n')
                        bom.append('C177' + ' ' + self.two_order_filter_data_11['C_value_double'] + '\n')
                        bom.append('R211' + ' ' + self.two_order_filter_data_11['R1_value'] + '\n')
                        bom.append('R212' + ' ' + self.two_order_filter_data_11['R2_value'] + '\n')
                        bom.append('R214' + ' ' + self.two_order_filter_data_11['R_half_value'] + '\n')
                        bom.append('R213' + ' ' + str(self.two_order_filter_data_11['R_gain_value']) + '\n')
                    elif self.module11 == 'highpass':
                        bom.append('C183' + ' ' + self.one_order_highpass_data_2['C_value'] + '\n')
                        bom.append('R219' + ' ' + self.one_order_highpass_data_2['R_value'] + '\n')
                    else:
                        bom.append('J45 short' + '\n')
                    # module 12
                    if self.module12 == 'notch':
                        bom.append('C181' + ' ' + self.two_order_filter_data_12['C1_value'] + '\n')
                        bom.append('C182' + ' ' + self.two_order_filter_data_12['C2_value'] + '\n')
                        bom.append('C180' + ' ' + self.two_order_filter_data_12['C_value_double'] + '\n')
                        bom.append('R215' + ' ' + self.two_order_filter_data_12['R1_value'] + '\n')
                        bom.append('R216' + ' ' + self.two_order_filter_data_12['R2_value'] + '\n')
                        bom.append('R218' + ' ' + self.two_order_filter_data_12['R_half_value'] + '\n')
                        bom.append('R217' + ' ' + str(self.two_order_filter_data_12['R_gain_value']) + '\n')
                    elif self.module12 == 'lowpass':
                        bom.append('C184' + ' ' + self.one_order_lowpass_data_2['C_value'] + '\n')
                        bom.append('R220' + ' ' + self.one_order_lowpass_data_2['R_value'] + '\n')
                    else:
                        bom.append('J46 short' + '\n')
                    # module 13
                    if self.module13 == 'op_one_order':
                        # self.op_gain_data_2 = dict(Ra_value='20k', Rb_value='20k')
                        bom.append('R221' + ' ' + '0' + '\n')
                        bom.append('R222' + ' ' + self.op_gain_data_2['Ra_value'] + '\n')
                        bom.append('R233' + ' ' + self.op_gain_data_2['Rb_value'] + '\n')
                        bom.append('R231' + ' ' + '0' + '\n')
                    else:
                        # self.two_order_lowpass_data_2 = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                        #                                    C2_value='12n')
                        bom.append('R221' + ' ' + self.two_order_lowpass_data_2['R1_value'] + '\n')
                        bom.append('R222' + ' ' + '0' + '\n')
                        bom.append('R231' + ' ' + self.two_order_lowpass_data_2['R3_value'] + '\n')
                        bom.append('R232' + ' ' + self.two_order_lowpass_data_2['R2_value'] + '\n')
                        bom.append('C185' + ' ' + self.two_order_lowpass_data_2['C2_value'] + '\n')
                        bom.append('C191' + ' ' + self.two_order_lowpass_data_2['C1_value'] + '\n')
                    # module 14
                    if self.module14 == 'high_shelf':
                        # self.high_shelf_data_2 = dict(C_value='680p', R_value='220k')
                        bom.append('R223' + ' ' + self.high_shelf_data_2['R_value'] + '\n')
                        bom.append('C186' + ' ' + self.high_shelf_data_2['C_value'] + '\n')
                    # module 15
                    if self.module15 == 'low_shelf':
                        # self.low_shelf_data_2 = dict(C_value='680p', R_value='220k')
                        bom.append('C192' + ' ' + self.low_shelf_data_2['C_value'] + '\n')
                        bom.append('R234' + ' ' + self.low_shelf_data_2['R_value'] + '\n')
                    # module 16
                    if self.module16 == 'op_lowpass':
                        # self.op_lowpass_data_2 = dict(C_value='8.2n')
                        bom.append('C193' + ' ' + self.op_lowpass_data_2['C_value'] + '\n')
                    # module 17
                    if self.module17 == 'peak':
                        # self.op_peak_data_2 = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k',
                        #                          R2_value='20k',R_half_value='10k', R_gain_value=0, R_high_cut='39k')
                        bom.append('C189' + ' ' + self.op_peak_data_2['C1_value'] + '\n')
                        bom.append('C190' + ' ' + self.op_peak_data_2['C2_value'] + '\n')
                        bom.append('C187' + ' ' + self.op_peak_data_2['C_value_double'] + '\n')
                        bom.append('R224' + ' ' + self.op_peak_data_2['R1_value'] + '\n')
                        bom.append('R225' + ' ' + self.op_peak_data_2['R2_value'] + '\n')
                        bom.append('R228' + ' ' + self.op_peak_data_2['R_half_value'] + '\n')
                        bom.append('R226' + ' ' + str(self.op_peak_data_2['R_gain_value']) + '\n')
                        bom.append('R227' + ' ' + self.op_peak_data_2['R_high_cut'] + '\n')
                        bom.append('R229' + ' ' + '0' + '\n')
                        bom.append('R230' + ' ' + '0' + '\n')
        else:
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

            # OP 02
            if self.op_model == 'two_op':
                # module 11
                if self.module11 == 'notch':
                    bom.append('C19' + ' ' + self.two_order_filter_data_11['C1_value'] + '\n')
                    bom.append('C22' + ' ' + self.two_order_filter_data_11['C2_value'] + '\n')
                    bom.append('C21' + ' ' + self.two_order_filter_data_11['C_value_double'] + '\n')
                    bom.append('R28' + ' ' + self.two_order_filter_data_11['R1_value'] + '\n')
                    bom.append('R32' + ' ' + self.two_order_filter_data_11['R2_value'] + '\n')
                    bom.append('R30' + ' ' + self.two_order_filter_data_11['R_half_value'] + '\n')
                    bom.append('R29' + ' ' + str(self.two_order_filter_data_11['R_gain_value']) + '\n')
                elif self.module11 == 'highpass':
                    bom.append('C20' + ' ' + self.one_order_highpass_data_2['C_value'] + '\n')
                    bom.append('R31' + ' ' + self.one_order_highpass_data_2['R_value'] + '\n')
                else:
                    bom.append('J03 short' + '\n')
                # module 12
                if self.module12 == 'notch':
                    bom.append('C23' + ' ' + self.two_order_filter_data_12['C1_value'] + '\n')
                    bom.append('C26' + ' ' + self.two_order_filter_data_12['C2_value'] + '\n')
                    bom.append('C24' + ' ' + self.two_order_filter_data_12['C_value_double'] + '\n')
                    bom.append('R33' + ' ' + self.two_order_filter_data_12['R1_value'] + '\n')
                    bom.append('R37' + ' ' + self.two_order_filter_data_12['R2_value'] + '\n')
                    bom.append('R36' + ' ' + self.two_order_filter_data_12['R_half_value'] + '\n')
                    bom.append('R35' + ' ' + str(self.two_order_filter_data_12['R_gain_value']) + '\n')
                elif self.module12 == 'lowpass':
                    bom.append('C25' + ' ' + self.one_order_lowpass_data_2['C_value'] + '\n')
                    bom.append('R34' + ' ' + self.one_order_lowpass_data_2['R_value'] + '\n')
                else:
                    bom.append('J04 short' + '\n')
                # module 13
                if self.module13 == 'op_one_order':
                    # self.op_gain_data_2 = dict(Ra_value='20k', Rb_value='20k')
                    bom.append('R38' + ' ' + '0' + '\n')
                    bom.append('R39' + ' ' + self.op_gain_data_2['Ra_value'] + '\n')
                    bom.append('R44' + ' ' + self.op_gain_data_2['Rb_value'] + '\n')
                    bom.append('R42' + ' ' + '0' + '\n')
                else:
                    # self.two_order_lowpass_data_2 = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                    #                                    C2_value='12n')
                    bom.append('R38' + ' ' + self.two_order_lowpass_data_2['R1_value'] + '\n')
                    bom.append('R39' + ' ' + '0' + '\n')
                    bom.append('R42' + ' ' + self.two_order_lowpass_data_2['R3_value'] + '\n')
                    bom.append('R43' + ' ' + self.two_order_lowpass_data_2['R2_value'] + '\n')
                    bom.append('C27' + ' ' + self.two_order_lowpass_data_2['C2_value'] + '\n')
                    bom.append('C29' + ' ' + self.two_order_lowpass_data_2['C1_value'] + '\n')
                # module 14
                if self.module14 == 'high_shelf':
                    # self.high_shelf_data_2 = dict(C_value='680p', R_value='220k')
                    bom.append('R40' + ' ' + self.high_shelf_data_2['R_value'] + '\n')
                    bom.append('C28' + ' ' + self.high_shelf_data_2['C_value'] + '\n')
                # module 15
                if self.module15 == 'low_shelf':
                    # self.low_shelf_data_2 = dict(C_value='680p', R_value='220k')
                    bom.append('C30' + ' ' + self.low_shelf_data_2['C_value'] + '\n')
                    bom.append('R49' + ' ' + self.low_shelf_data_2['R_value'] + '\n')
                # module 16
                if self.module16 == 'op_lowpass':
                    # self.op_lowpass_data_2 = dict(C_value='8.2n')
                    bom.append('C31' + ' ' + self.op_lowpass_data_2['C_value'] + '\n')
                # module 17
                if self.module17 == 'peak':
                    # self.op_peak_data_2 = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k',
                    #                          R2_value='20k',R_half_value='10k', R_gain_value=0, R_high_cut='39k')
                    bom.append('C32' + ' ' + self.op_peak_data_2['C1_value'] + '\n')
                    bom.append('C33' + ' ' + self.op_peak_data_2['C_value_double'] + '\n')
                    bom.append('C34' + ' ' + self.op_peak_data_2['C2_value'] + '\n')
                    bom.append('R45' + ' ' + self.op_peak_data_2['R1_value'] + '\n')
                    bom.append('R48' + ' ' + self.op_peak_data_2['R2_value'] + '\n')
                    bom.append('R47' + ' ' + self.op_peak_data_2['R_half_value'] + '\n')
                    bom.append('R46' + ' ' + str(self.op_peak_data_2['R_gain_value']) + '\n')
                    bom.append('R41' + ' ' + self.op_peak_data_2['R_high_cut'] + '\n')
                    bom.append('R50' + ' ' + '0' + '\n')
                    bom.append('R51' + ' ' + '0' + '\n')

        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'save file', '.', 'txt Files (*.txt);;All Files (*)')
        if filename[0]:
            with open(filename[0], 'w') as f:
                f.writelines(bom)

    # 配置信息导入导出
    def ImportSettings_FF_clicked(self):
        """导入配置信息"""
        # 设置目录
        if self.project_file:
            filename = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', self.project_file,
                                                             'ini Files (*.ini);;All Files (*)')
        else:
            filename = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', '.', 'ini Files (*.ini);;All Files (*)')
        try:
            if filename[0]:
                self.project_file = filename[0]
                settings = QSettings(filename[0], QSettings.IniFormat)
                # 相位及OP模式
                self.radioButton_noninverting_phase.setChecked(
                    settings.value('phase_status_noninverting', True, type=bool))
                self.radioButton_inverting_phase.setChecked(settings.value('phase_status_inverting', False, type=bool))
                self.radioButton_two_op.setChecked(settings.value('op_status_two', True, type=bool))
                self.radioButton_one_op.setChecked(settings.value('op_status_one', False, type=bool))
                # mic 增益配置
                self.mic_gain_spin.setValue(settings.value('mic_gain', 0, type=float))
                # module01配置
                self.notch01_status = settings.value('module01/tuning_status', False, type=bool)
                self.frequencySpin.setValue(settings.value('module01/notch_frequency', 1000, type=int))  # 无数据时导入1000默认值
                self.amplitudeSlider.setValue(settings.value('module01/notch_amplitude', 0, type=int))
                self.filter01_radioButton_notch.setChecked(settings.value('module01/radioButton_notch', type=bool))
                self.filter01_radioButton_highpass.setChecked(
                    settings.value('module01/radioButton_highpass', type=bool))
                self.filter01_radioButton_bypass.setChecked(settings.value('module01/radioButton_bypass', type=bool))
                self.frequencySpin_highpass.setValue(settings.value('module01/highpass_frequency', 1000, type=int))
                self.highpass_gain_spin.setValue(settings.value('module01/highpass_gain', 0, type=int))
                if self.notch01_status:
                    self.two_order_filter_data = settings.value('module01/tuning_data', self.two_order_filter_data,
                                                                type=dict)
                    self.set_notch01_parameter(self.two_order_filter_data, self.notch01_status)

                # module02配置
                self.notch02_status = settings.value('module02/tuning_status', False, type=bool)
                self.frequencySpin_2.setValue(
                    settings.value('module02/notch_frequency', 1000, type=int))  # 无数据时导入1000默认值
                self.amplitudeSlider_2.setValue(settings.value('module02/notch_amplitude', 0, type=int))
                self.filter01_radioButton_notch_2.setChecked(settings.value('module02/radioButton_notch', type=bool))
                self.filter01_radioButton_lowpass.setChecked(settings.value('module02/radioButton_lowpass', type=bool))
                self.filter01_radioButton_bypass_2.setChecked(settings.value('module02/radioButton_bypass', type=bool))
                self.frequencySpin_lowpass.setValue(settings.value('module02/lowpass_frequency', 1000, type=int))
                if self.notch02_status:
                    self.two_order_filter_data_02 = settings.value('module02/tuning_data',
                                                                   self.two_order_filter_data_02,
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

                # module11配置
                self.notch11_status = settings.value('module11/tuning_status', False, type=bool)
                self.frequencySpin_4.setValue(
                    settings.value('module11/notch_frequency', 1000, type=int))  # 无数据时导入1000默认值
                self.amplitudeSlider_4.setValue(settings.value('module11/notch_amplitude', 0, type=int))
                self.filter01_radioButton_notch_4.setChecked(settings.value('module11/radioButton_notch', type=bool))
                self.filter01_radioButton_highpass_2.setChecked(
                    settings.value('module11/radioButton_highpass', type=bool))
                self.filter01_radioButton_bypass_4.setChecked(settings.value('module11/radioButton_bypass', type=bool))
                self.frequencySpin_highpass_2.setValue(settings.value('module11/highpass_frequency', 1000, type=int))
                if self.notch11_status:
                    self.two_order_filter_data_11 = settings.value('module11/tuning_data',
                                                                   self.two_order_filter_data_11,
                                                                   type=dict)
                    self.set_notch11_parameter(self.two_order_filter_data_11, self.notch11_status)

                # module12配置
                self.notch12_status = settings.value('module12/tuning_status', False, type=bool)
                self.frequencySpin_3.setValue(
                    settings.value('module12/notch_frequency', 1000, type=int))  # 无数据时导入1000默认值
                self.amplitudeSlider_3.setValue(settings.value('module12/notch_amplitude', 0, type=int))
                self.filter01_radioButton_notch_3.setChecked(settings.value('module12/radioButton_notch', type=bool))
                self.filter01_radioButton_lowpass_2.setChecked(
                    settings.value('module12/radioButton_lowpass', type=bool))
                self.filter01_radioButton_bypass_3.setChecked(settings.value('module12/radioButton_bypass', type=bool))
                self.frequencySpin_lowpass_2.setValue(settings.value('module12/lowpass_frequency', 1000, type=int))
                if self.notch12_status:
                    self.two_order_filter_data_12 = settings.value('module12/tuning_data',
                                                                   self.two_order_filter_data_12,
                                                                   type=dict)
                    self.set_notch12_parameter(self.two_order_filter_data_12, self.notch12_status)

                # module13
                self.two_order_lowpass_18_status = settings.value('module13/tuning_status', False, type=bool)
                self.OP_lowpass_filter_enable_2.setChecked(settings.value('module13/filter_enable', type=bool))
                self.OP_lowpass_order_radio_one_2.setChecked(settings.value('module13/order', type=bool))
                self.OP_lowpass_order_radio_one_2.setChecked(settings.value('module13/order_2', type=bool))
                self.OP_lowpass_order_radio_bessel_2.setChecked(settings.value('module13/filter_type', type=bool))
                self.OP_lowpass_order_radio_butterworth_2.setChecked(settings.value('module13/filter_type2', type=bool))
                self.OP_lowpass_order_radio_chebyshev_2.setChecked(settings.value('module13/filter_type3', type=bool))
                self.chebyshev_1dB_4.setChecked(settings.value('module13/ripple_1', type=bool))
                self.chebyshev_1dB_5.setChecked(settings.value('module13/ripple_2', type=bool))
                self.chebyshev_1dB_6.setChecked(settings.value('module13/ripple_3', type=bool))
                self.OP_gain_spin_2.setValue(settings.value('module13/gain', 0, type=int))
                self.frequencySpin_OP_lowpass_2.setValue(settings.value('module13/frequency', 1000, type=int))
                if self.two_order_lowpass_18_status:
                    self.two_order_lowpass_data_2 = settings.value('module13/tuning_data',
                                                                   self.two_order_lowpass_data_2,
                                                                   type=dict)
                    self.set_two_order_lowpass_parameter_2(self.two_order_lowpass_data_2,
                                                           self.two_order_lowpass_18_status)

                # module14
                self.OP_highshelf_filter_enable_2.setChecked(settings.value('module14/filter_enable', type=bool))
                self.high_shelf_gain_spin_2.setValue(settings.value('module14/gain', 0, type=int))
                self.high_shelf_frequency_spin_2.setValue(settings.value('module14/frequency', 1000, type=int))

                # module15
                self.OP_lowshelf_filter_enable_2.setChecked(settings.value('module15/filter_enable', type=bool))
                self.low_shelf_gain_spin_2.setValue(settings.value('module15/gain', 0, type=int))
                self.low_shelf_frequency_spin_2.setValue(settings.value('module15/frequency', 1000, type=int))

                # module17
                self.peak17_status = settings.value('module17/tuning_status', False, type=bool)
                self.OP_peak_filter_enable_2.setChecked(settings.value('module17/filter_enable', type=bool))
                self.peak_gain_spin_2.setValue(settings.value('module17/gain', 0, type=int))
                self.peak_frequency_spin_2.setValue(settings.value('module17/frequency', 1000, type=int))
                self.peak_lowpass_slider_2.setValue(settings.value('module17/high_reject', 0, type=int))
                self.peak_attenuation_slider_2.setValue(settings.value('module17/amplitude_attenuation', 0, type=int))
                if self.peak17_status:
                    self.op_peak_data_2 = settings.value('module17/tuning_data', self.op_peak_data_2, type=dict)
                    self.set_peak17_parameter(self.op_peak_data_2, self.peak17_status)  # 重置ICON及界面

                # 窗口尺寸及位置配置
                self.restoreGeometry(settings.value("geometry"))
                self.restoreState(settings.value("windowState"))

                # self.peak_frequency_spin.valueChanged.connect(self.set_module_07_data)
                # self.peak_gain_spin.valueChanged.connect(self.set_module_07_data)
                # self.peak_lowpass_slider.valueChanged.connect(self.set_module_07_data)
                # self.peak_attenuation_slider.valueChanged.connect(self.set_module_07_data)
        except Exception:
            QtWidgets.QMessageBox.information(self, '提示', '导入失败，格式不匹配')

    def SaveSettings_FF_clicked(self):
        """保存filter模块配置信息"""
        if self.project_file:
            filename = QtWidgets.QFileDialog.getSaveFileName(self, 'save file', self.project_file,
                                                             'ini Files (*.ini);;All Files (*)')
        else:
            filename = QtWidgets.QFileDialog.getSaveFileName(self, 'save file', '.', 'ini Files (*.ini);;All Files (*)')
        if filename[0]:
            self.project_file = filename[0]
            settings = QSettings(filename[0], QSettings.IniFormat)
            # 相位及OP模式
            settings.setValue('phase_status_noninverting', self.radioButton_noninverting_phase.isChecked())
            settings.setValue('phase_status_inverting', self.radioButton_inverting_phase.isChecked())
            settings.setValue('op_status_two', self.radioButton_two_op.isChecked())
            settings.setValue('op_status_one', self.radioButton_one_op.isChecked())
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
            settings.setValue('highpass_gain', self.highpass_gain_spin.value())
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
            # module11
            settings.beginGroup('module11')
            settings.setValue('notch_frequency', self.frequencySpin_4.value())
            settings.setValue('notch_amplitude', self.amplitudeSlider_4.value())
            settings.setValue('radioButton_notch', self.filter01_radioButton_notch_4.isChecked())
            settings.setValue('radioButton_bypass', self.filter01_radioButton_bypass_4.isChecked())
            settings.setValue('radioButton_highpass', self.filter01_radioButton_highpass_2.isChecked())
            settings.setValue('highpass_frequency', self.frequencySpin_highpass_2.value())
            settings.setValue('tuning_status', self.notch11_status)
            settings.setValue('tuning_data', self.two_order_filter_data_11)
            settings.endGroup()
            # module12
            settings.beginGroup('module12')
            settings.setValue('notch_frequency', self.frequencySpin_3.value())
            settings.setValue('notch_amplitude', self.amplitudeSlider_3.value())
            settings.setValue('radioButton_notch', self.filter01_radioButton_notch_3.isChecked())
            settings.setValue('radioButton_bypass', self.filter01_radioButton_bypass_3.isChecked())
            settings.setValue('radioButton_lowpass', self.filter01_radioButton_lowpass_2.isChecked())
            settings.setValue('lowpass_frequency', self.frequencySpin_lowpass_2.value())
            settings.setValue('tuning_status', self.notch12_status)
            settings.setValue('tuning_data', self.two_order_filter_data_12)
            settings.endGroup()
            # module13
            settings.beginGroup('module13')
            settings.setValue('tuning_status', self.two_order_lowpass_18_status)
            settings.setValue('tuning_data', self.two_order_lowpass_data_2)
            settings.setValue('filter_enable', self.OP_lowpass_filter_enable_2.isChecked())
            settings.setValue('order', self.OP_lowpass_order_radio_one_2.isChecked())
            settings.setValue('order_2', self.OP_lowpass_order_radio_one_2.isChecked())
            settings.setValue('filter_type', self.OP_lowpass_order_radio_bessel_2.isChecked())
            settings.setValue('filter_type2', self.OP_lowpass_order_radio_butterworth_2.isChecked())
            settings.setValue('filter_type3', self.OP_lowpass_order_radio_chebyshev_2.isChecked())
            settings.setValue('ripple_1', self.chebyshev_1dB_4.isChecked())
            settings.setValue('ripple_2', self.chebyshev_1dB_5.isChecked())
            settings.setValue('ripple_3', self.chebyshev_1dB_6.isChecked())
            settings.setValue('gain', self.OP_gain_spin_2.value())
            settings.setValue('frequency', self.frequencySpin_OP_lowpass_2.value())
            settings.endGroup()
            # module14
            settings.beginGroup('module14')
            settings.setValue('filter_enable', self.OP_highshelf_filter_enable_2.isChecked())
            settings.setValue('gain', self.high_shelf_gain_spin_2.value())
            settings.setValue('frequency', self.high_shelf_frequency_spin_2.value())
            settings.endGroup()
            # module15
            settings.beginGroup('module15')
            settings.setValue('filter_enable', self.OP_lowshelf_filter_enable_2.isChecked())
            settings.setValue('gain', self.low_shelf_gain_spin_2.value())
            settings.setValue('frequency', self.low_shelf_frequency_spin_2.value())
            settings.endGroup()
            # module17
            settings.beginGroup('module17')
            settings.setValue('filter_enable', self.OP_peak_filter_enable_2.isChecked())
            settings.setValue('gain', self.peak_gain_spin_2.value())
            settings.setValue('frequency', self.peak_frequency_spin_2.value())
            settings.setValue('high_reject', self.peak_lowpass_slider_2.value())
            settings.setValue('amplitude_attenuation', self.peak_attenuation_slider_2.value())
            settings.setValue('tuning_status', self.peak17_status)
            settings.setValue('tuning_data', self.op_peak_data_2)
            settings.endGroup()
            # 窗口尺寸及位置配置
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())

            del settings
            if True:
                QtWidgets.QMessageBox.information(self, '提示', '保存成功')

    def reset_settings(self):
        # 相位及OP模式
        self.radioButton_noninverting_phase.setChecked(True)
        self.radioButton_two_op.setChecked(True)
        # mic 增益配置
        self.mic_gain_spin.setValue(0)
        # module01配置
        self.notch01_status = False
        self.frequencySpin.setValue(1000)  # 无数据时导入1000默认值
        self.amplitudeSlider.setValue(0)
        self.filter01_radioButton_bypass.setChecked(True)
        self.frequencySpin_highpass.setValue(1000)
        self.highpass_gain_spin.setValue(0)

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

        # module11配置
        self.notch11_status = False
        self.frequencySpin_4.setValue(1000)  # 无数据时导入1000默认值
        self.amplitudeSlider_4.setValue(0)
        self.filter01_radioButton_bypass_4.setChecked(True)
        self.frequencySpin_highpass_2.setValue(1000)

        # module12配置
        self.notch12_status = False
        self.frequencySpin_3.setValue(1000)  # 无数据时导入1000默认值
        self.amplitudeSlider_3.setValue(0)
        self.filter01_radioButton_bypass_3.setChecked(True)
        self.frequencySpin_lowpass_2.setValue(1000)

        # module13
        self.two_order_lowpass_18_status = False
        self.OP_lowpass_filter_enable_2.setChecked(False)
        self.OP_lowpass_order_radio_one_2.setChecked(True)
        self.OP_lowpass_order_radio_bessel_2.setChecked(True)
        self.chebyshev_1dB_4.setChecked(True)
        self.OP_gain_spin_2.setValue(0)
        self.OP_gain_spin_2.setMinimum(-10)
        self.frequencySpin_OP_lowpass_2.setValue(1000)

        # module14
        self.OP_highshelf_filter_enable_2.setChecked(False)
        self.high_shelf_gain_spin_2.setValue(0)
        self.high_shelf_frequency_spin_2.setValue(1000)

        # module15
        self.OP_lowshelf_filter_enable_2.setChecked(False)
        self.low_shelf_gain_spin_2.setValue(0)
        self.low_shelf_frequency_spin_2.setValue(1000)

        # module17
        self.peak17_status = False
        self.OP_peak_filter_enable_2.setChecked(False)
        self.peak_gain_spin_2.setValue(0)
        self.peak_frequency_spin_2.setValue(1000)
        self.peak_lowpass_slider_2.setValue(0)
        self.peak_attenuation_slider_2.setValue(0)

        # set default data
        self.set_op2_default_data()
        self.set_op2_default_module()
        self.set_notch11_parameter(self.two_order_filter_data_11, False)
        self.set_notch12_parameter(self.two_order_filter_data_12, False)
        self.set_peak17_parameter(self.op_peak_data_2, False)
        self.set_two_order_lowpass_parameter_2(self.two_order_lowpass_data_2, False)
        self.set_module_17()
        self.AimCurveInButton.setDefault(False)

    # tuning module 01
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
            r_notch = R_value2map_2(self.default_notch_r_value)
            r_notch_half = R_value2map_2(self.default_notch_r_value * 0.5)
            self.amplitudeSlider.setEnabled(True)
            self.label_2.setEnabled(True)
            self.label.setEnabled(True)
            self.frequencySpin.setEnabled(True)
            self.btn_notch01_tuning.setDefault(False)  # 取消按键标记

            self.two_order_filter_data = dict(C1_value='22n', C2_value='22n', C_value_double='47n', R1_value=r_notch,
                                              R2_value=r_notch, R_half_value=r_notch_half, R_gain_value=0)
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
            r_notch = R_value2map_2(self.default_notch_r_value)
            r_notch_half = R_value2map_2(self.default_notch_r_value * 0.5)
            self.amplitudeSlider_2.setEnabled(True)
            self.label_3.setEnabled(True)
            self.label_4.setEnabled(True)
            self.frequencySpin_2.setEnabled(True)
            self.btn_notch02_tuning.setDefault(False)  # 取消按键标记

            self.two_order_filter_data_02 = dict(C1_value='22n', C2_value='22n', C_value_double='47n', R1_value=r_notch,
                                              R2_value=r_notch, R_half_value=r_notch_half, R_gain_value=0)
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
            r_peak = R_value2map_2(self.default_peak_r_value)
            r_peak_half = R_value2map_2(self.default_peak_r_value * 0.5)
            r_peak_double = R_value2map_2(self.default_peak_r_value * 2)
            self.btn_peak01_tuning.setDefault(False)  # 按键标记
            self.label_11.setPixmap(QtGui.QPixmap(':/mic/icon/peak.png'))
            self.op_peak_data = dict(C1_value='8.2n', C2_value='8.2n', C_value_double='15n', R1_value=r_peak,
                                 R2_value=r_peak, R_half_value=r_peak_half, R_gain_value=0, R_high_cut=r_peak_double)
            self.set_module_07()

    def peak01_tuning(self):
        dialog = MyPeakFilterTuningDialog(self.op_peak_data, self.peak01_status)
        dialog.signal.connect(self.set_peak01_parameter)
        dialog.exec_()

    def set_peak01_all_parameter(self, argv_peak, module_peak, argv_ls, module_ls, argv_hs, module_hs, argv_lp,
                                 module_lp, argv_gain):
        self.peak01_status = module_peak
        self.ls01_status = module_ls
        self.hs01_status = module_hs
        self.lp01_status = module_lp
        if module_peak:
            self.op_peak_data = argv_peak
            self.module07 = 'peak'
        else:
            self.module07 = None
        if module_ls:
            self.low_shelf_data = argv_ls
            self.module05 = 'low_shelf'
        else:
            self.module05 = None
        if module_hs:
            self.high_shelf_data = argv_hs
            self.module04 = 'high_shelf'
        else:
            self.module04 = None
        if module_lp:
            self.op_lowpass_data = argv_lp
            self.module06 = 'op_lowpass'
        else:
            self.module06 = None
        if module_peak or module_ls or module_hs or module_lp:
            self.btn_peak01_tuning.setDefault(True)  # 按键标记
            self.groupBox_4.setEnabled(False)
            self.groupBox_5.setEnabled(False)
            self.groupBox_6.setEnabled(False)
            self.groupBox_7.setEnabled(False)
            self.label_11.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            self.label_12.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            self.label_13.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            self.label_15.setPixmap(QtGui.QPixmap(':/mic/icon/tuning.png'))
            self.op_gain_data = argv_gain
        else:
            self.btn_peak01_tuning.setDefault(False)  # 按键标记
            self.groupBox_4.setEnabled(True)
            self.groupBox_5.setEnabled(True)
            self.groupBox_6.setEnabled(True)
            self.groupBox_7.setEnabled(True)
            self.label_11.setPixmap(QtGui.QPixmap(':/mic/icon/peak.png'))
            self.label_12.setPixmap(QtGui.QPixmap(":/mic/icon/LowShelf.png"))
            self.label_13.setPixmap(QtGui.QPixmap(":/mic/icon/HighShelf.png"))
            self.label_15.setPixmap(QtGui.QPixmap(":/mic/icon/lowpass.png"))
            self.set_module_03()
            self.set_module_04()
            self.set_module_05()
            # self.set_module_06()
            self.set_module_07()
            # self.set_module_08()


    def peak01_tuning_all(self):
        dialog = MyPeakFilterTuningAllDialog(self.op_peak_data,self.peak01_status, self.low_shelf_data,
                                             self.ls01_status, self.high_shelf_data, self.hs01_status,
                                             self.op_lowpass_data, self.lp01_status, self.op_gain_data)
        dialog.signal.connect(self.set_peak01_all_parameter)
        dialog.exec_()

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
            self.two_order_lowpass_data = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                                               C2_value='12n')
            self.set_module_08()

    def two_order_lowpass_tuning(self):
        dialog = MyTwoOrderLowpassTuningDialog(self.two_order_lowpass_data, self.two_order_lowpass_status)
        dialog.signal.connect(self.set_two_order_lowpass_parameter)
        dialog.exec_()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myWin = FilterDesignerWindow()
    print(FilterDesignerWindow.mro())
    myWin.tabWidget_2.setCurrentIndex(1)
    myWin.tab_5.setEnabled(False)
    myWin.show()
    sys.exit(app.exec_())
