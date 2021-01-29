#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/5/17 15:12
import sys
import xlrd
import xml.etree.ElementTree as ET
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from main_UI import Ui_MainWindow  # 导入UI
from includes.iir_filter_func import *
import matplotlib

matplotlib.use("Qt5Agg")  # 声明使用QT5


class MyEqFigure(FigureCanvas):

    def __init__(self, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)  # 创建figure
        super(MyEqFigure, self).__init__(self.fig)  # 父类中激活figure

        self.axes0 = self.fig.add_subplot(211)
        self.axes0.set_ylabel('Magnitude(dB)')
        self.axes0.grid(True, which='both')

        self.axes1 = self.fig.add_subplot(212, sharex=self.axes0)
        self.axes1.set_xlabel('Frequency(Hz)')
        self.axes1.set_ylabel('phase(degree)')
        self.axes1.grid(True, which='both')

    def plot_eq_fr(self, sos1, fs1, eq_reference=None):
        self.axes0.lines = []  # 清除绘图区
        self.axes1.lines = []

        w, h = sg.sosfreqz(sos1, worN=4096, fs=fs1)  # 计算IIR响应
        mag = 20 * np.log10(abs(h))
        mag = mag.clip(-150, 150)
        phase = np.angle(h, deg=True)

        if eq_reference:  # 导入参考EQ曲线
            x_reference, mag_reference = eq_reference
            y_min = np.min([mag.min(), mag_reference.min()])
            y_max = np.max([mag.max(), mag_reference.max()])
            self.axes0.semilogx(x_reference, mag_reference, 'g')
        else:
            y_min = mag.min()
            y_max = mag.max()

        self.axes0.semilogx(w, mag, 'b')
        self.axes1.semilogx(w, phase, 'b')
        try:
            self.axes0.set_ylim(y_min - np.abs(y_min) * 0.01 - 0.1, y_max + np.abs(y_max) * 0.01 + 0.1)
            self.axes1.set_ylim(phase.min() - np.abs(phase.min()) * 0.03 - 0.1,
                                phase.max() + np.abs(phase.min()) * 0.03 + 0.1)
        except Exception:
            pass

        self.draw()

    def plot_eq_limit_fr(self, sos1, sos2, fs1, eq_reference=None):
        self.axes0.cla()
        self.axes1.cla()

        w, h = sg.sosfreqz(sos1, worN=4096, fs=fs1)
        w2, h2 = sg.sosfreqz(sos2, worN=4096, fs=fs1)
        mag = 20 * np.log10(abs(h))
        phase = np.angle(h, deg=True)
        mag2 = 20 * np.log10(abs(h2))
        phase2 = np.angle(h2, deg=True)

        self.axes0.semilogx(w, mag, 'b')
        self.axes0.semilogx(w2, mag2, 'r')

        self.axes1.semilogx(w, phase, 'b')
        self.axes1.semilogx(w2, phase2, 'r')

        self.axes1.legend(('Ideal filter', 'Real filter'))

        if eq_reference:  # 导入参考EQ曲线
            x_reference, mag_reference = eq_reference
            self.axes0.semilogx(x_reference, mag_reference, 'g')
            self.axes0.legend(('Ideal filter', 'Real filter', 'Reference curve'))
        else:
            self.axes0.legend(('Ideal filter', 'Real filter'))
        self.draw()


class SetEqWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """EQ设计UI界面控制"""

    def __init__(self, parent=None):
        super(SetEqWindow, self).__init__(parent)
        self.setupUi(self)
        self.eq_reference = ()  # 参考eq曲线
        self._real_time_draw = True  # 实时绘图开关
        self.set_default_iir_data()
        self.iir_data_boxes, self.create_iir_funcs = self.signals_slots_iir_eq()

        self.figure_eq = MyEqFigure(width=9, height=4, dpi=100)  # matplotlib绘图
        navi_toolbar_eq = NavigationToolbar(self.figure_eq, self)
        self.layout_eq = QtWidgets.QVBoxLayout(self.iir_preview)
        self.layout_eq.addWidget(navi_toolbar_eq)
        self.layout_eq.addWidget(self.figure_eq)
        self.eq_preview()

    def signals_slots_iir_eq(self):
        list_data_box = [[self.checkbox_IIR_1, self.checkbox_IIR_2, self.checkbox_IIR_3,
                          self.checkbox_IIR_4, self.checkbox_IIR_5, self.checkbox_IIR_6,
                          self.checkbox_IIR_r1, self.checkbox_IIR_r2, self.checkbox_IIR_r3,
                          self.checkbox_IIR_r4, self.checkbox_IIR_r5, self.checkbox_IIR_r6],
                         [self.combobox_iir_1, self.combobox_iir_2, self.combobox_iir_3,
                          self.combobox_iir_4, self.combobox_iir_5, self.combobox_iir_6,
                          self.combobox_iir_r1, self.combobox_iir_r2, self.combobox_iir_r3,
                          self.combobox_iir_r4, self.combobox_iir_r5, self.combobox_iir_r6],
                         [self.spinbox_iir_q_1, self.spinbox_iir_q_2, self.spinbox_iir_q_3,
                          self.spinbox_iir_q_4, self.spinbox_iir_q_5, self.spinbox_iir_q_6,
                          self.spinbox_iir_q_r1, self.spinbox_iir_q_r2, self.spinbox_iir_q_r3,
                          self.spinbox_iir_q_r4, self.spinbox_iir_q_r5, self.spinbox_iir_q_r6],
                         [self.spinbox_iir_f_1, self.spinbox_iir_f_2, self.spinbox_iir_f_3,
                          self.spinbox_iir_f_4, self.spinbox_iir_f_5, self.spinbox_iir_f_6,
                          self.spinbox_iir_f_r1, self.spinbox_iir_f_r2, self.spinbox_iir_f_r3,
                          self.spinbox_iir_f_r4, self.spinbox_iir_f_r5, self.spinbox_iir_f_r6],
                         [self.spinbox_iir_gain_1, self.spinbox_iir_gain_2, self.spinbox_iir_gain_3,
                          self.spinbox_iir_gain_4, self.spinbox_iir_gain_5, self.spinbox_iir_gain_6,
                          self.spinbox_iir_gain_r1, self.spinbox_iir_gain_r2, self.spinbox_iir_gain_r3,
                          self.spinbox_iir_gain_r4, self.spinbox_iir_gain_r5, self.spinbox_iir_gain_r6]]
        list_create_func = [self.create_iir_l01, self.create_iir_l02, self.create_iir_l03,
                            self.create_iir_l04, self.create_iir_l05, self.create_iir_l06,
                            self.create_iir_r01, self.create_iir_r02, self.create_iir_r03,
                            self.create_iir_r04, self.create_iir_r05, self.create_iir_r06]

        for i, func in zip(range(len(list_create_func)), list_create_func):  # IIR类型、f，gain，Q值设置框
            list_data_box[0][i].toggled.connect(func)
            list_data_box[1][i].currentIndexChanged.connect(func)
            list_data_box[2][i].valueChanged.connect(func)
            list_data_box[3][i].valueChanged.connect(func)
            list_data_box[4][i].valueChanged.connect(func)

        self.tabWidget_4.currentChanged.connect(self.eq_preview)  # L/R选择框
        self.spinbox_gain_eq_l.valueChanged.connect(self.create_iir_l01)
        self.spinbox_gain_eq_r.valueChanged.connect(self.create_iir_r01)
        # 界面配置
        self.btn_iir_save_setting.clicked.connect(self.save_settings_eq)  # 保存
        self.btn_iir_import_setting.clicked.connect(self.import_settings_eq)  # 导入
        self.btn_eq_reset_data.clicked.connect(self.reset_settings_eq)  # 重置
        self.btn_eq_copy_l_to_r.clicked.connect(self.set_r_data_form_l_eq)  # 复制L EQ
        self.btn_iir_import_eq.clicked.connect(self.import_data_eq_reference)  # 导入参考EQ

        self.btn_export_iir_ba.clicked.connect(self.export_eq_ba)  # 导出iir ba参数
        self.btn_export_iir_ba_sample.clicked.connect(self.export_eq_ba_sample)  # 导出iir ba参数
        self.checkbox_iir_real_time_darw.toggled.connect(self.real_time_drawing)  # 实时绘图

        return list_data_box, list_create_func

    def set_default_iir_data(self):
        sos_l1 = np.array([1., 0., 0., 1., 0., 0.])
        sos_l2 = np.array([1., 0., 0., 1., 0., 0.])
        sos_l3 = np.array([1., 0., 0., 1., 0., 0.])
        sos_l4 = np.array([1., 0., 0., 1., 0., 0.])
        sos_l5 = np.array([1., 0., 0., 1., 0., 0.])
        sos_l6 = np.array([1., 0., 0., 1., 0., 0.])
        self.eq_data_l_fs8000 = np.vstack((sos_l1, sos_l2, sos_l3, sos_l4, sos_l5, sos_l6))
        self.eq_data_l_fs11025 = np.vstack((sos_l1, sos_l2, sos_l3, sos_l4, sos_l5, sos_l6))
        self.eq_data_l_fs12000 = np.vstack((sos_l1, sos_l2, sos_l3, sos_l4, sos_l5, sos_l6))
        self.eq_data_l_fs16000 = np.vstack((sos_l1, sos_l2, sos_l3, sos_l4, sos_l5, sos_l6))
        self.eq_data_l_fs22050 = np.vstack((sos_l1, sos_l2, sos_l3, sos_l4, sos_l5, sos_l6))
        self.eq_data_l_fs24000 = np.vstack((sos_l1, sos_l2, sos_l3, sos_l4, sos_l5, sos_l6))
        self.eq_data_l_fs32000 = np.vstack((sos_l1, sos_l2, sos_l3, sos_l4, sos_l5, sos_l6))
        self.eq_data_l_fs44100 = np.vstack((sos_l1, sos_l2, sos_l3, sos_l4, sos_l5, sos_l6))
        self.eq_data_l_fs48000 = np.vstack((sos_l1, sos_l2, sos_l3, sos_l4, sos_l5, sos_l6))
        self.eq_data_L = {'8000': self.eq_data_l_fs8000, '11025': self.eq_data_l_fs11025,
                          '12000': self.eq_data_l_fs12000, '16000': self.eq_data_l_fs16000,
                          '22050': self.eq_data_l_fs22050, '24000': self.eq_data_l_fs24000,
                          '32000': self.eq_data_l_fs32000, '44100': self.eq_data_l_fs44100,
                          '48000': self.eq_data_l_fs48000}

        sos_r1 = np.array([1., 0., 0., 1., 0., 0.])
        sos_r2 = np.array([1., 0., 0., 1., 0., 0.])
        sos_r3 = np.array([1., 0., 0., 1., 0., 0.])
        sos_r4 = np.array([1., 0., 0., 1., 0., 0.])
        sos_r5 = np.array([1., 0., 0., 1., 0., 0.])
        sos_r6 = np.array([1., 0., 0., 1., 0., 0.])
        self.eq_data_r_fs8000 = np.vstack((sos_r1, sos_r2, sos_r3, sos_r4, sos_r5, sos_r6))
        self.eq_data_r_fs11025 = np.vstack((sos_r1, sos_r2, sos_r3, sos_r4, sos_r5, sos_r6))
        self.eq_data_r_fs12000 = np.vstack((sos_r1, sos_r2, sos_r3, sos_r4, sos_r5, sos_r6))
        self.eq_data_r_fs16000 = np.vstack((sos_r1, sos_r2, sos_r3, sos_r4, sos_r5, sos_r6))
        self.eq_data_r_fs22050 = np.vstack((sos_r1, sos_r2, sos_r3, sos_r4, sos_r5, sos_r6))
        self.eq_data_r_fs24000 = np.vstack((sos_r1, sos_r2, sos_r3, sos_r4, sos_r5, sos_r6))
        self.eq_data_r_fs32000 = np.vstack((sos_r1, sos_r2, sos_r3, sos_r4, sos_r5, sos_r6))
        self.eq_data_r_fs44100 = np.vstack((sos_r1, sos_r2, sos_r3, sos_r4, sos_r5, sos_r6))
        self.eq_data_r_fs48000 = np.vstack((sos_r1, sos_r2, sos_r3, sos_r4, sos_r5, sos_r6))

        self.eq_data_r = {'8000': self.eq_data_r_fs8000, '11025': self.eq_data_r_fs11025,
                          '12000': self.eq_data_r_fs12000, '16000': self.eq_data_r_fs16000,
                          '22050': self.eq_data_r_fs22050, '24000': self.eq_data_r_fs24000,
                          '32000': self.eq_data_r_fs32000, '44100': self.eq_data_r_fs44100,
                          '48000': self.eq_data_r_fs48000}

    # 根据UI界面调整EQ参数
    def create_iir_l01(self):
        """创建L通道第一组IIR滤波器"""
        gain = self.spinbox_iir_gain_1.value()
        f = self.spinbox_iir_f_1.value()
        q = self.spinbox_iir_q_1.value()
        dc_gain_l = self.spinbox_gain_eq_l.value()
        K = 10 ** (dc_gain_l / 20)
        if self.checkbox_IIR_1.isChecked():
            if self.combobox_iir_1.currentText() == 'peak/notch':
                for k, data in self.eq_data_L.items():
                    data[0] = peak_filter_iir(f, gain, q, fs=int(k))
                    data[0][:3] = data[0][:3] * K

            elif self.combobox_iir_1.currentText() == 'lowshelf':
                for k, data in self.eq_data_L.items():
                    data[0] = low_shelf_filter_iir(f, gain, q, fs=int(k))
                    data[0][:3] = data[0][:3] * K

            elif self.combobox_iir_1.currentText() == 'highshelf':
                for k, data in self.eq_data_L.items():
                    data[0] = high_shelf_filter_iir(f, gain, q, fs=int(k))
                    data[0][:3] = data[0][:3] * K

            elif self.combobox_iir_1.currentText() == 'lowpass':
                for k, data in self.eq_data_L.items():
                    data[0] = low_pass_filter_iir(f, q, fs=int(k))
                    data[0][:3] = data[0][:3] * K

            elif self.combobox_iir_1.currentText() == 'highpass':
                for k, data in self.eq_data_L.items():
                    data[0] = high_pass_filter_iir(f, q, fs=int(k))
                    data[0][:3] = data[0][:3] * K

        else:
            for k, data in self.eq_data_L.items():
                data[0] = np.array([1., 0., 0., 1., 0., 0.])
                data[0][:3] = data[0][:3] * K

        self.eq_preview()

    def create_iir_l02(self):
        """创建L通道第一组IIR滤波器"""
        gain = self.spinbox_iir_gain_2.value()
        f = self.spinbox_iir_f_2.value()
        q = self.spinbox_iir_q_2.value()
        if self.checkbox_IIR_2.isChecked():
            if self.combobox_iir_2.currentText() == 'peak/notch':
                for k, data in self.eq_data_L.items():
                    data[1] = peak_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_2.currentText() == 'lowshelf':
                for k, data in self.eq_data_L.items():
                    data[1] = low_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_2.currentText() == 'highshelf':
                for k, data in self.eq_data_L.items():
                    data[1] = high_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_2.currentText() == 'lowpass':
                for k, data in self.eq_data_L.items():
                    data[1] = low_pass_filter_iir(f, q, fs=int(k))

            elif self.combobox_iir_2.currentText() == 'highpass':
                for k, data in self.eq_data_L.items():
                    data[1] = high_pass_filter_iir(f, q, fs=int(k))

        else:
            for k, data in self.eq_data_L.items():
                data[1] = np.array([1., 0., 0., 1., 0., 0.])

        self.eq_preview()

    def create_iir_l03(self):
        """创建L通道第一组IIR滤波器"""
        gain = self.spinbox_iir_gain_3.value()
        f = self.spinbox_iir_f_3.value()
        q = self.spinbox_iir_q_3.value()
        if self.checkbox_IIR_3.isChecked():
            if self.combobox_iir_3.currentText() == 'peak/notch':
                for k, data in self.eq_data_L.items():
                    data[2] = peak_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_3.currentText() == 'lowshelf':
                for k, data in self.eq_data_L.items():
                    data[2] = low_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_3.currentText() == 'highshelf':
                for k, data in self.eq_data_L.items():
                    data[2] = high_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_3.currentText() == 'lowpass':
                for k, data in self.eq_data_L.items():
                    data[2] = low_pass_filter_iir(f, q, fs=int(k))

            elif self.combobox_iir_3.currentText() == 'highpass':
                for k, data in self.eq_data_L.items():
                    data[2] = high_pass_filter_iir(f, q, fs=int(k))

        else:
            for k, data in self.eq_data_L.items():
                data[2] = np.array([1., 0., 0., 1., 0., 0.])

        self.eq_preview()

    def create_iir_l04(self):
        """创建L通道第一组IIR滤波器"""
        gain = self.spinbox_iir_gain_4.value()
        f = self.spinbox_iir_f_4.value()
        q = self.spinbox_iir_q_4.value()
        if self.checkbox_IIR_4.isChecked():
            if self.combobox_iir_4.currentText() == 'peak/notch':
                for k, data in self.eq_data_L.items():
                    data[3] = peak_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_4.currentText() == 'lowshelf':
                for k, data in self.eq_data_L.items():
                    data[3] = low_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_4.currentText() == 'highshelf':
                for k, data in self.eq_data_L.items():
                    data[3] = high_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_4.currentText() == 'lowpass':
                for k, data in self.eq_data_L.items():
                    data[3] = low_pass_filter_iir(f, q, fs=int(k))

            elif self.combobox_iir_4.currentText() == 'highpass':
                for k, data in self.eq_data_L.items():
                    data[3] = high_pass_filter_iir(f, q, fs=int(k))

        else:
            for k, data in self.eq_data_L.items():
                data[3] = np.array([1., 0., 0., 1., 0., 0.])

        self.eq_preview()

    def create_iir_l05(self):
        """创建L通道第一组IIR滤波器"""
        gain = self.spinbox_iir_gain_5.value()
        f = self.spinbox_iir_f_5.value()
        q = self.spinbox_iir_q_5.value()
        if self.checkbox_IIR_5.isChecked():
            if self.combobox_iir_5.currentText() == 'peak/notch':
                for k, data in self.eq_data_L.items():
                    data[4] = peak_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_5.currentText() == 'lowshelf':
                for k, data in self.eq_data_L.items():
                    data[4] = low_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_5.currentText() == 'highshelf':
                for k, data in self.eq_data_L.items():
                    data[4] = high_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_5.currentText() == 'lowpass':
                for k, data in self.eq_data_L.items():
                    data[4] = low_pass_filter_iir(f, q, fs=int(k))

            elif self.combobox_iir_5.currentText() == 'highpass':
                for k, data in self.eq_data_L.items():
                    data[4] = high_pass_filter_iir(f, q, fs=int(k))

        else:
            for k, data in self.eq_data_L.items():
                data[4] = np.array([1., 0., 0., 1., 0., 0.])

        self.eq_preview()

    def create_iir_l06(self):
        """创建L通道第一组IIR滤波器"""
        gain = self.spinbox_iir_gain_6.value()
        f = self.spinbox_iir_f_6.value()
        q = self.spinbox_iir_q_6.value()
        if self.checkbox_IIR_6.isChecked():
            if self.combobox_iir_6.currentText() == 'peak/notch':
                for k, data in self.eq_data_L.items():
                    data[5] = peak_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_6.currentText() == 'lowshelf':
                for k, data in self.eq_data_L.items():
                    data[5] = low_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_6.currentText() == 'highshelf':
                for k, data in self.eq_data_L.items():
                    data[5] = high_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_6.currentText() == 'lowpass':
                for k, data in self.eq_data_L.items():
                    data[5] = low_pass_filter_iir(f, q, fs=int(k))

            elif self.combobox_iir_6.currentText() == 'highpass':
                for k, data in self.eq_data_L.items():
                    data[5] = high_pass_filter_iir(f, q, fs=int(k))

        else:
            for k, data in self.eq_data_L.items():
                data[5] = np.array([1., 0., 0., 1., 0., 0.])

        self.eq_preview()

    def create_iir_r01(self):
        """创建r通道第一组IIR滤波器"""
        gain = self.spinbox_iir_gain_r1.value()
        f = self.spinbox_iir_f_r1.value()
        q = self.spinbox_iir_q_r1.value()
        dc_gain_r = self.spinbox_gain_eq_r.value()
        K = 10 ** (dc_gain_r / 20)
        if self.checkbox_IIR_r1.isChecked():
            if self.combobox_iir_r1.currentText() == 'peak/notch':
                for k, data in self.eq_data_r.items():
                    data[0] = peak_filter_iir(f, gain, q, fs=int(k))
                    data[0][:3] = data[0][:3] * K

            elif self.combobox_iir_r1.currentText() == 'lowshelf':
                for k, data in self.eq_data_r.items():
                    data[0] = low_shelf_filter_iir(f, gain, q, fs=int(k))
                    data[0][:3] = data[0][:3] * K

            elif self.combobox_iir_r1.currentText() == 'highshelf':
                for k, data in self.eq_data_r.items():
                    data[0] = high_shelf_filter_iir(f, gain, q, fs=int(k))
                    data[0][:3] = data[0][:3] * K

            elif self.combobox_iir_r1.currentText() == 'lowpass':
                for k, data in self.eq_data_r.items():
                    data[0] = low_pass_filter_iir(f, q, fs=int(k))
                    data[0][:3] = data[0][:3] * K

            elif self.combobox_iir_r1.currentText() == 'highpass':
                for k, data in self.eq_data_r.items():
                    data[0] = high_pass_filter_iir(f, q, fs=int(k))
                    data[0][:3] = data[0][:3] * K

        else:
            for k, data in self.eq_data_r.items():
                data[0] = np.array([1., 0., 0., 1., 0., 0.])
                data[0][:3] = data[0][:3] * K

        self.eq_preview()

    def create_iir_r02(self):
        """创建L通道第一组IIR滤波器"""
        gain = self.spinbox_iir_gain_r2.value()
        f = self.spinbox_iir_f_r2.value()
        q = self.spinbox_iir_q_r2.value()
        if self.checkbox_IIR_r2.isChecked():
            if self.combobox_iir_r2.currentText() == 'peak/notch':
                for k, data in self.eq_data_r.items():
                    data[1] = peak_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r2.currentText() == 'lowshelf':
                for k, data in self.eq_data_r.items():
                    data[1] = low_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r2.currentText() == 'highshelf':
                for k, data in self.eq_data_r.items():
                    data[1] = high_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r2.currentText() == 'lowpass':
                for k, data in self.eq_data_r.items():
                    data[1] = low_pass_filter_iir(f, q, fs=int(k))

            elif self.combobox_iir_r2.currentText() == 'highpass':
                for k, data in self.eq_data_r.items():
                    data[1] = high_pass_filter_iir(f, q, fs=int(k))

        else:
            for k, data in self.eq_data_r.items():
                data[1] = np.array([1., 0., 0., 1., 0., 0.])

        self.eq_preview()

    def create_iir_r03(self):
        """创建L通道第一组IIR滤波器"""
        gain = self.spinbox_iir_gain_r3.value()
        f = self.spinbox_iir_f_r3.value()
        q = self.spinbox_iir_q_r3.value()
        if self.checkbox_IIR_r3.isChecked():
            if self.combobox_iir_r3.currentText() == 'peak/notch':
                for k, data in self.eq_data_r.items():
                    data[2] = peak_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r3.currentText() == 'lowshelf':
                for k, data in self.eq_data_r.items():
                    data[2] = low_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r3.currentText() == 'highshelf':
                for k, data in self.eq_data_r.items():
                    data[2] = high_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r3.currentText() == 'lowpass':
                for k, data in self.eq_data_r.items():
                    data[2] = low_pass_filter_iir(f, q, fs=int(k))

            elif self.combobox_iir_r3.currentText() == 'highpass':
                for k, data in self.eq_data_r.items():
                    data[2] = high_pass_filter_iir(f, q, fs=int(k))

        else:
            for k, data in self.eq_data_r.items():
                data[2] = np.array([1., 0., 0., 1., 0., 0.])

        self.eq_preview()

    def create_iir_r04(self):
        """创建L通道第一组IIR滤波器"""
        gain = self.spinbox_iir_gain_r4.value()
        f = self.spinbox_iir_f_r4.value()
        q = self.spinbox_iir_q_r4.value()
        if self.checkbox_IIR_r4.isChecked():
            if self.combobox_iir_r4.currentText() == 'peak/notch':
                for k, data in self.eq_data_r.items():
                    data[3] = peak_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r4.currentText() == 'lowshelf':
                for k, data in self.eq_data_r.items():
                    data[3] = low_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r4.currentText() == 'highshelf':
                for k, data in self.eq_data_r.items():
                    data[3] = high_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r4.currentText() == 'lowpass':
                for k, data in self.eq_data_r.items():
                    data[3] = low_pass_filter_iir(f, q, fs=int(k))

            elif self.combobox_iir_r4.currentText() == 'highpass':
                for k, data in self.eq_data_r.items():
                    data[3] = high_pass_filter_iir(f, q, fs=int(k))

        else:
            for k, data in self.eq_data_r.items():
                data[3] = np.array([1., 0., 0., 1., 0., 0.])

        self.eq_preview()

    def create_iir_r05(self):
        """创建L通道第一组IIR滤波器"""
        gain = self.spinbox_iir_gain_r5.value()
        f = self.spinbox_iir_f_r5.value()
        q = self.spinbox_iir_q_r5.value()
        if self.checkbox_IIR_r5.isChecked():
            if self.combobox_iir_r5.currentText() == 'peak/notch':
                for k, data in self.eq_data_r.items():
                    data[4] = peak_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r5.currentText() == 'lowshelf':
                for k, data in self.eq_data_r.items():
                    data[4] = low_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r5.currentText() == 'highshelf':
                for k, data in self.eq_data_r.items():
                    data[4] = high_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r5.currentText() == 'lowpass':
                for k, data in self.eq_data_r.items():
                    data[4] = low_pass_filter_iir(f, q, fs=int(k))

            elif self.combobox_iir_r5.currentText() == 'highpass':
                for k, data in self.eq_data_r.items():
                    data[4] = high_pass_filter_iir(f, q, fs=int(k))

        else:
            for k, data in self.eq_data_r.items():
                data[4] = np.array([1., 0., 0., 1., 0., 0.])

        self.eq_preview()

    def create_iir_r06(self):
        """创建L通道第一组IIR滤波器"""
        gain = self.spinbox_iir_gain_r6.value()
        f = self.spinbox_iir_f_r6.value()
        q = self.spinbox_iir_q_r6.value()
        if self.checkbox_IIR_r6.isChecked():
            if self.combobox_iir_r6.currentText() == 'peak/notch':
                for k, data in self.eq_data_r.items():
                    data[5] = peak_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r6.currentText() == 'lowshelf':
                for k, data in self.eq_data_r.items():
                    data[5] = low_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r6.currentText() == 'highshelf':
                for k, data in self.eq_data_r.items():
                    data[5] = high_shelf_filter_iir(f, gain, q, fs=int(k))

            elif self.combobox_iir_r6.currentText() == 'lowpass':
                for k, data in self.eq_data_r.items():
                    data[5] = low_pass_filter_iir(f, q, fs=int(k))

            elif self.combobox_iir_r6.currentText() == 'highpass':
                for k, data in self.eq_data_r.items():
                    data[5] = high_pass_filter_iir(f, q, fs=int(k))

        else:
            for k, data in self.eq_data_r.items():
                data[5] = np.array([1., 0., 0., 1., 0., 0.])

        self.eq_preview()

    # 绘图
    def eq_preview(self):
        if self._real_time_draw:  # 检测实时绘图开关
            fs01 = 48000
            sos1L = self.eq_data_l_fs48000
            sos1r = self.eq_data_r_fs48000
            sos2L = self.eq_data_l_fs48000.copy().clip(-8, 8)
            sos2L = self.ba_float_to_d12(sos2L)
            sos2L = self.ba_d12_to_float(sos2L)
            sos2r = self.eq_data_r_fs48000.copy().clip(-8, 8)
            sos2r = self.ba_float_to_d12(sos2r)
            sos2r = self.ba_d12_to_float(sos2r)

            result01 = sos2L == self.eq_data_l_fs48000
            result02 = sos2r == self.eq_data_r_fs48000

            try:
                if self.tabWidget_4.currentIndex() == 0:
                    if result01.all():
                        self.figure_eq.plot_eq_fr(sos1L, fs01, eq_reference=self.eq_reference)
                    else:
                        self.figure_eq.plot_eq_limit_fr(sos1L, sos2L, fs01, eq_reference=self.eq_reference)
                else:
                    if result02.all():
                        self.figure_eq.plot_eq_fr(sos1r, fs01, eq_reference=self.eq_reference)
                    else:
                        self.figure_eq.plot_eq_limit_fr(sos1r, sos2r, fs01, eq_reference=self.eq_reference)
            except Exception as e:
                print(e)
        else:
            pass

    def real_time_drawing(self):
        """实时绘图控制函数"""
        if self.checkbox_iir_real_time_darw.isChecked():
            self._real_time_draw = True
            self.eq_preview()
        else:
            self._real_time_draw = False

    # 界面配置
    def save_settings_eq(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'save file', '.',
                                                         'eqdata Files (*.eqdata);;All Files (*)')
        if filename[0]:
            settings = QSettings(filename[0], QSettings.IniFormat)
            for i in range(12):
                settings.beginGroup('module' + str(i))
                settings.setValue(self.iir_data_boxes[0][i].objectName(), self.iir_data_boxes[0][i].isChecked())
                settings.setValue(self.iir_data_boxes[1][i].objectName(), self.iir_data_boxes[1][i].currentIndex())
                settings.setValue(self.iir_data_boxes[2][i].objectName(), self.iir_data_boxes[2][i].value())
                settings.setValue(self.iir_data_boxes[3][i].objectName(), self.iir_data_boxes[3][i].value())
                settings.setValue(self.iir_data_boxes[4][i].objectName(), self.iir_data_boxes[4][i].value())
                settings.endGroup()
            settings.setValue(self.spinbox_gain_eq_l.objectName(), self.spinbox_gain_eq_l.value())
            settings.setValue(self.spinbox_gain_eq_r.objectName(), self.spinbox_gain_eq_r.value())
            del settings

    def import_settings_eq(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', '.',
                                                         'eqdata Files (*.eqdata);;All Files (*)')

        if filename[0]:
            try:
                self._real_time_draw = False
                settings = QSettings(filename[0], QSettings.IniFormat)
                for i in range(12):
                    self.iir_data_boxes[0][i].setChecked(
                        settings.value('module' + str(i) + r'/' + self.iir_data_boxes[0][i].objectName(), False, bool))
                    self.iir_data_boxes[1][i].setCurrentIndex(
                        settings.value('module' + str(i) + r'/' + self.iir_data_boxes[1][i].objectName(), 0, int))
                    self.iir_data_boxes[2][i].setValue(
                        settings.value('module' + str(i) + r'/' + self.iir_data_boxes[2][i].objectName(), 1, float))
                    self.iir_data_boxes[3][i].setValue(
                        settings.value('module' + str(i) + r'/' + self.iir_data_boxes[3][i].objectName(), 1000, int))
                    self.iir_data_boxes[4][i].setValue(
                        settings.value('module' + str(i) + r'/' + self.iir_data_boxes[4][i].objectName(), 1, float))
                self.spinbox_gain_eq_l.setValue(settings.value(self.spinbox_gain_eq_l.objectName(), 0, float))
                self.spinbox_gain_eq_r.setValue(settings.value(self.spinbox_gain_eq_r.objectName(), 0, float))
                self._real_time_draw = True
                self.eq_preview()
                self.real_time_drawing()
            except Exception:
                QtWidgets.QMessageBox.information(self, '提示', '导入失败，格式不匹配')

    def reset_settings_eq(self):
        self._real_time_draw = False
        for i in range(12):
            self.iir_data_boxes[0][i].setChecked(False)
            self.iir_data_boxes[1][i].setCurrentIndex(0)
            self.iir_data_boxes[2][i].setValue(1)
            self.iir_data_boxes[3][i].setValue(1000)
            self.iir_data_boxes[4][i].setValue(1)
        self.spinbox_gain_eq_l.setValue(0)
        self.spinbox_gain_eq_r.setValue(0)

        self.figure_eq.axes0.cla()
        self.figure_eq.axes0.set_ylabel('Magnitude(dB)')
        self.figure_eq.axes1.cla()
        self.figure_eq.axes1.set_xlabel('Frequency(Hz)')
        self.figure_eq.axes1.set_ylabel('phase(degree)')
        self.figure_eq.plot_eq_fr(self.eq_data_l_fs48000, 48000)
        self.real_time_drawing()

    def set_r_data_form_l_eq(self):
        self._real_time_draw = False
        for i in range(6):
            self.iir_data_boxes[0][i + 6].setChecked(self.iir_data_boxes[0][i].isChecked())
            self.iir_data_boxes[1][i + 6].setCurrentIndex(self.iir_data_boxes[1][i].currentIndex())
            self.iir_data_boxes[2][i + 6].setValue(self.iir_data_boxes[2][i].value())
            self.iir_data_boxes[3][i + 6].setValue(self.iir_data_boxes[3][i].value())
            self.iir_data_boxes[4][i + 6].setValue(self.iir_data_boxes[4][i].value())
        self.spinbox_gain_eq_r.setValue(self.spinbox_gain_eq_l.value())
        self._real_time_draw = True
        self.eq_preview()
        self.real_time_drawing()

    # 导入参考曲线
    def import_data_eq_reference(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'open file', '.',
                                                         'excel Files (*.xls;*.xlsx);;txt Files (*.txt)')
        if filename[0]:
            if filename[1] == 'txt Files (*.txt)':  # 打开txt格式数据
                try:  # 频响曲线导入,根据样条插值法匹配横坐标
                    x_freq, mag = np.loadtxt(filename[0], unpack=True, encoding='utf-8')
                    self.eq_reference = (x_freq, mag)
                    # tck1 = interpolate.splrep(x_freq, mag)
                    # mag1 = interpolate.splev(self.x, tck1, ext=3)
                    #
                    # tck2 = interpolate.splrep(x_freq, phase)
                    # phase1 = interpolate.splev(self.x, tck2, ext=3)
                    #
                    # num = len(phase1) - 1  # 恢复相位区间
                    # for j in range(5):
                    #     for i in range(num):
                    #         if phase1[i + 1] - phase1[i] > 300:
                    #             phase1[i + 1:] -= 360
                    #         if phase1[i + 1] - phase1[i] < -300:
                    #             phase1[i + 1:] += 360
                    #
                    # self.fb_spk_mag = mag1  # 输出FB频响曲线
                    # self.fb_spk_phase = phase1
                except Exception as e:
                    print(e)
                    QtWidgets.QMessageBox.warning(self, '警告', '导入失败：数据格式不匹配')
            else:  # 打开excel格式数据
                try:
                    with xlrd.open_workbook(filename[0]) as excel_data:
                        table0 = excel_data.sheet_by_index(0)
                        x_freq = np.array(table0.col_values(0)[1:])  # 忽略第一行参数
                        mag = np.array(table0.col_values(1)[1:])
                        # phase = np.array(table0.col_values(2)[1:])
                        self.eq_reference = (x_freq, mag)

                        # tck1 = interpolate.splrep(x_freq, mag)
                        # mag1 = interpolate.splev(self.x, tck1, ext=3)
                        #
                        # tck2 = interpolate.splrep(x_freq, phase)
                        # phase1 = interpolate.splev(self.x, tck2, ext=3)
                        #
                        # num = len(phase1) - 1  # 恢复相位区间
                        # for j in range(5):
                        #     for i in range(num):
                        #         if phase1[i + 1] - phase1[i] > 300:
                        #             phase1[i + 1:] -= 360
                        #         if phase1[i + 1] - phase1[i] < -300:
                        #             phase1[i + 1:] += 360
                        #
                        # self.fb_spk_mag = mag1  # 输出FB频响曲线
                        # self.fb_spk_phase = phase1
                        #
                        # self.groupBox_4.setEnabled(True)
                        # self.groupBox_3.setEnabled(True)
                        # QtWidgets.QMessageBox.information(self, '提示', '导入成功')
                        # return self.fb_spk_mag, self.fb_spk_phase
                except Exception as e:
                    print(e)
                    QtWidgets.QMessageBox.warning(self, '警告', '导入失败：数据格式不匹配')
            self._real_time_draw = True
            self.eq_preview()
            self.real_time_drawing()

    # 导出ba参数
    def ba_float_to_d12(self, eq_data):
        """
        IIR滤波器系数由浮点数转换为定点数
        :param eq_data: IIR双二阶系数，形如：array([1,0,0,1,0,0], [1,0,0,1,0,0]，[1,0,0,1,0,0]...)
        :return:array([b0, b1, b2, a0, a1, a2, shift factor],[b0, b1, b2, a0, a1, a2, shift factor]...)
        """
        # print(eq_data)
        m, n = eq_data.shape
        out_data = np.zeros([m, n + 1])
        for i in range(m):
            data = eq_data[i]
            max01 = np.max(np.abs(data) * 2 ** 12)  # 确定移位系数
            if max01 <= 4096:
                shift_factor = 15
            elif max01 <= 8192:
                shift_factor = 14
            elif max01 <= 16384:
                shift_factor = 13
            else:  # ba最大系数限定8
                shift_factor = 12
            num_ba = (data * 2 ** shift_factor).astype(int)
            out_data[i] = np.hstack((num_ba, shift_factor))

        return out_data.astype(int)

    def ba_d12_to_float(self, eq_data):
        """
        ba_float_to_d12函数生成的定点数组转换浮点数数组
        :param 形如 array([b0, b1, b2, a0, a1, a2, shift factor],[b0, b1, b2, a0, a1, a2, shift factor]...)
        :return: 形如 array([1.11,0.88,0,1,0,0], [1,0,0,1,0,0]，[1,0,0,1,0,0]...)
        """
        m, n = eq_data.shape
        out_data = np.zeros([m, n - 1])
        for i in range(m):
            data = eq_data[i]
            out_data[i] = data[:-1] / 2 ** data[-1]

        return out_data

    def ba_float_to_d12_1d(self, eq_data):
        """
        浮点数表示的iir系数转换为定点数
        :param eq_data: array([1,0,0,1,0,0])
        :return: array([b0, b1, b2, a0, a1, a2, shift factor])
        """
        max01 = np.max(np.abs(eq_data) * 2 ** 12)  # 确定移位系数
        if max01 <= 4096:
            shift_factor = 15
        elif max01 <= 8192:
            shift_factor = 14
        elif max01 <= 16384:
            shift_factor = 13
        else:  # ba最大系数限定8
            shift_factor = 12
        num_ba = (eq_data * 2 ** shift_factor).astype(int)
        out_data = np.hstack((num_ba, shift_factor))

        return out_data.astype(int)

    def ba_d12_to_float_1d(self, eq_data):
        """
        定点数表示的iir系数转换为浮点数表示
        :param eq_data: array([b0, b1, b2, a0, a1, a2, shift factor])
        :return: array([1,0,0,1,0,0])
        """
        out_data = eq_data[:-1] / 2 ** eq_data[-1]
        return out_data

    def export_eq_ba(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'save file', '.', 'xml Files (*.xml);;All Files (*)')
        if filename[0]:
            try:
                root = ET.Element('filterSection')  # 根目录设置
                root.attrib = dict(formatVersion='1.0')

                for k, v in self.eq_data_L.items():  # 整个数组，字典格式
                    sub = ET.SubElement(root, 'filter')
                    sub.attrib = dict(channel='L', fs=k)
                    data = self.ba_float_to_d12(v)  # 6段iir定点数数组
                    for i in data:
                        str01 = i.astype(str)  # 1段iir双二阶定点数数组
                        start_str = ''  # 拼接输出str
                        for m, n in enumerate(str01):
                            if m == 3:  # 储存系数跳过a0
                                continue
                            start_str = start_str + n + ', '
                        if start_str != '32768, 0, 0, 0, 0, 15, ':  # 忽略初始[1,0,0,1,0,0]数组
                            a = ET.SubElement(sub, 'iirBiquad')
                            a.text = start_str[:-2]

                for k, v in self.eq_data_r.items():  # 整个数组，字典格式
                    sub = ET.SubElement(root, 'filter')
                    sub.attrib = dict(channel='R', fs=k)
                    data = self.ba_float_to_d12(v)  # 6段iir定点数数组
                    for i in data:
                        str01 = i.astype(str)  # 1段iir双二阶定点数数组
                        start_str = ''  # 拼接输出str
                        for m, n in enumerate(str01):
                            if m == 3:  # 储存系数跳过a0
                                continue
                            start_str = start_str + n + ', '
                        if start_str != '32768, 0, 0, 0, 0, 15, ':  # 忽略初始[1,0,0,1,0,0]数组
                            a = ET.SubElement(sub, 'iirBiquad')
                            a.text = start_str[:-2]

                self.pretty_xml(root, '\t', '\n')
                tree = ET.ElementTree(root)
                tree.write(filename[0], encoding='UTF-8', xml_declaration=True)
                QtWidgets.QMessageBox.information(self, '提示', '保存成功')
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, '提示', '保存失败:' + str(e))
                print(e)

    def export_eq_ba_sample(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'save file', '.', 'xml Files (*.xml);;All Files (*)')
        if filename[0]:
            try:
                root = ET.Element('filterSection')  # 根目录设置
                root.attrib = dict(formatVersion='1.0')

                sub = ET.SubElement(root, 'filter')
                sub.attrib = dict(channel='L', fs='48000')
                data = self.ba_float_to_d12(self.eq_data_L['48000'])  # 6段iir定点数数组
                for i in data:
                    str01 = i.astype(str)  # 1段iir双二阶定点数数组
                    start_str = ''  # 拼接输出str
                    for m, n in enumerate(str01):
                        if m == 3:  # 储存系数跳过a0
                            continue
                        start_str = start_str + n + ', '
                    if start_str != '32768, 0, 0, 0, 0, 15, ':  # 忽略初始[1,0,0,1,0,0]数组
                        a = ET.SubElement(sub, 'iirBiquad')
                        a.text = start_str[:-2]

                sub = ET.SubElement(root, 'filter')
                sub.attrib = dict(channel='R', fs='48000')
                data = self.ba_float_to_d12(self.eq_data_r['48000'])  # 6段iir定点数数组
                for i in data:
                    str01 = i.astype(str)  # 1段iir双二阶定点数数组
                    start_str = ''  # 拼接输出str
                    for m, n in enumerate(str01):
                        if m == 3:  # 储存系数跳过a0
                            continue
                        start_str = start_str + n + ', '
                    if start_str != '32768, 0, 0, 0, 0, 15, ':  # 忽略初始[1,0,0,1,0,0]数组
                        a = ET.SubElement(sub, 'iirBiquad')
                        a.text = start_str[:-2]

                self.pretty_xml(root, '\t', '\n')
                tree = ET.ElementTree(root)
                tree.write(filename[0], encoding='UTF-8', xml_declaration=True)
                QtWidgets.QMessageBox.information(self, '提示', '保存成功')
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, '提示', '保存失败:' + str(e))
                print(e)

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


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myWin = SetEqWindow()
    myWin.show()
    sys.exit(app.exec_())
