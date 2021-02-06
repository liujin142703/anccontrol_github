#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/1/18 14:34
import os

import PySpice.Spice.NgSpice.Shared as ps

add_path1 = os.path.abspath('.')
ps.NgSpiceShared.LIBRARY_PATH = os.path.join(add_path1, 'ngspice{}.dll')
# import matplotlib
# matplotlib.use("qt5agg")  # 声明使用QT5
# plt.rcParams['font.sans-serif'] = ['SimHei']  # legend无法正常显示中文,设置字体切换
# plt.rcParams['axes.unicode_minus'] = False  # 显示负号
import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from PySpice.Unit import *


class MyFilterSimulator(object):

    def __init__(self):
        pass

    def my_simulator(self, netlist):
        """根据输入电路网表参数进行仿真分析，输出为分析结果"""
        # if self.list_path:  # 直接解析netlist,暂无使用
        #     parser = SpiceParser(path=self.list_path)
        #     circuit = parser.build_circuit()
        #     # 导入运算放大器，运放输入管脚：负输入、正输入、输出
        #     circuit.subcircuit(BasicOperationalAmplifier())
        #     # 插入运放，负输入接input，输出接notch电路
        #     circuit.X('op', 'BasicOperationalAmplifier', 'Net-_R1-Pad1_', circuit.gnd, 'Net-_C1-Pad2_')
        #     # 仿真计算.ac(开始频率，截止频率，点数，指数取点）
        #     simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        #     analysis = simulator.ac(start_frequency=10 @ u_Hz, stop_frequency=20 @ u_kHz, number_of_points=200,
        #                             variation='dec')
        #     return analysis
        simulator = netlist.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.ac(start_frequency=10 @ u_Hz, stop_frequency=20 @ u_kHz, number_of_points=200,
                                variation='dec')
        return analysis

    def my_plotter(self, ax, data1, data2, mode, param_dict):
        out = ax.semilogx(data1, data2, base=10, **param_dict)
        ax.grid(True, which='both')
        if mode == 'gain':
            ax.set_xlabel("Frequency [Hz]")
            ax.set_ylabel("Gain [dB]")
        else:
            ax.set_xlabel("Frequency [Hz]")
            ax.set_ylabel("Phase [deg]")
        return out

    def closed_loop_calculate_fb_mic(self, gain, phase):
        a = 1 / (gain * gain + 2 * gain * np.cos(phase) + 1)
        return np.power(a, 0.5)

    def closed_loop_calculate_artificial_ear_mic(self, gain, phase, gain1, phase1):
        a = gain * gain + 2 * gain * np.cos(phase) + 1
        b1 = 1 + gain * np.cos(phase) - gain1 * np.cos(phase1)
        b2 = gain * np.sin(phase) - gain1 * np.sin(phase1)
        result = np.power((b1 * b1 + b2 * b2), 0.5) / np.power(a, 0.5)
        return result

    def my_bode_diagram(self, analysis=None, aim_curve_data=None, model=None):
        """绘图函数，利用Circuit.simulator.ac分析结果，进行matplotlib绘图，曲线为analysis.output端口响应数据"""
        figure = plt.figure(1, (12, 6), clear=False)
        plt.title("my notch filter")
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(212, sharex=ax1)
        if analysis:
            if model == 'one_op':
                gain = 20 * np.log10(np.absolute(analysis.output))
                phase = (np.angle(analysis.output, deg=False) * 180 / np.pi)
            else:
                gain = 20 * np.log10(np.absolute(analysis.op02_out)),
                phase = (np.angle(analysis.op02_out, deg=False) * 180 / np.pi),

            frequency = analysis.frequency
            self.my_plotter(ax1, frequency, gain[0], 'gain', {'marker': None})
            self.my_plotter(ax2, frequency, phase[0], 'phase', {'marker': None})
        # 如果用户导入excel参考数据，绘制参考数据
        if aim_curve_data:
            self.my_plotter(ax1, aim_curve_data.x_frequency, aim_curve_data.f_gain, 'gain', {'marker': None})
            self.my_plotter(ax2, aim_curve_data.x_frequency, aim_curve_data.phase_num, 'phase', {'marker': None})
            plt.legend(('simulation result', 'Ideal filter'), loc='upper right')
        cursor = Cursor(ax1, useblit=True, color='g', linewidth=1)
        cursor1 = Cursor(ax2, useblit=True, color='g', linewidth=1)
        plt.tight_layout(pad=2, w_pad=2, h_pad=2)
        figure.show()

    def my_fb_result_forecast(self, analysis, spk_fb_mic, spk_artificial_ear_mic=None, fb_artificial_ear_mic=None):
        figure = plt.figure(2, (12, 6), clear=False)
        plt.title("FB result forecast")
        axe = figure.add_subplot(1, 1, 1)

        frequency = analysis.frequency
        filter_gain = np.absolute(analysis.op02_out)
        gain1 = np.log10(filter_gain),
        filter_phase = np.angle(analysis.op02_out, deg=False)

        # 导入SPK_FB频响并根据样条插值法匹配横坐标
        tck1 = interpolate.splrep(spk_fb_mic.x_frequency, spk_fb_mic.f_gain)
        spk_fb_gain = interpolate.splev(frequency, tck1, ext=3)
        tck2 = interpolate.splrep(spk_fb_mic.x_frequency, spk_fb_mic.phase_num)
        spk_fb_phase = interpolate.splev(frequency, tck2, ext=3)

        # num = len(spk_fb_phase) - 1  # 恢复相位区间
        # for j in range(5):
        #     for i in range(num):
        #         if spk_fb_phase[i + 1] - spk_fb_phase[i] > 300:
        #             spk_fb_phase[i + 1:] -= 360
        #         if spk_fb_phase[i + 1] - spk_fb_phase[i] < -300:
        #             spk_fb_phase[i + 1:] += 360

        open_loop_gain = np.power(10, gain1[0]) * np.power(10, spk_fb_gain / 20)
        open_loop_phase = filter_phase + spk_fb_phase * np.pi / 180
        closed_loop_fb_result = self.closed_loop_calculate_fb_mic(open_loop_gain, open_loop_phase)
        self.my_plotter(axe, frequency, 20 * np.log10(closed_loop_fb_result), 'gain', {'marker': None})

        if spk_artificial_ear_mic:
            if fb_artificial_ear_mic:
                tck1 = interpolate.splrep(fb_artificial_ear_mic.x_frequency, fb_artificial_ear_mic.f_gain)
                x_x1_gain = interpolate.splev(frequency, tck1, ext=3)
                tck2 = interpolate.splrep(fb_artificial_ear_mic.x_frequency, fb_artificial_ear_mic.phase_num)
                x_x1_phase = interpolate.splev(frequency, tck2, ext=3)
            else:
                x_x1_gain = 0
                x_x1_phase = 0

            tck1 = interpolate.splrep(spk_artificial_ear_mic.x_frequency, spk_artificial_ear_mic.f_gain)
            spk_artificial_ear_gain = interpolate.splev(frequency, tck1, ext=3)
            tck2 = interpolate.splrep(spk_artificial_ear_mic.x_frequency, spk_artificial_ear_mic.phase_num)
            spk_artificial_ear_phase = interpolate.splev(frequency, tck2, ext=3)

            # num = len(spk_artificial_ear_phase) - 1  # 恢复相位区间
            # for j in range(5):
            #     for i in range(num):
            #         if spk_artificial_ear_phase[i + 1] - spk_artificial_ear_phase[i] > 300:
            #             spk_artificial_ear_phase[i + 1:] -= 360
            #         if spk_artificial_ear_phase[i + 1] - spk_artificial_ear_phase[i] < -300:
            #             spk_artificial_ear_phase[i + 1:] += 360

            open_loop_gain_1 = np.power(10, gain1[0]) * np.power(10, spk_artificial_ear_gain / 20) * np.power(10,
                                                                                                              x_x1_gain / 20)
            open_loop_phase_1 = filter_phase + spk_artificial_ear_phase * np.pi / 180 + x_x1_phase * np.pi / 180
            closed_loop_artificial_ear_result = self.closed_loop_calculate_artificial_ear_mic(
                open_loop_gain, open_loop_phase, open_loop_gain_1, open_loop_phase_1)
            self.my_plotter(axe, frequency, 20 * np.log10(closed_loop_artificial_ear_result), 'gain', {'marker': None})

        cursor = Cursor(axe, useblit=True, color='g', linewidth=1)
        plt.tight_layout(pad=2, w_pad=2, h_pad=2)
        plt.show()
