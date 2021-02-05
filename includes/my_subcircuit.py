#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/1/23 14:31
from PySpice.Spice.Netlist import SubCircuitFactory
from includes.My_OperationalAmplifier import BasicOperationalAmplifier  ##私有运放模块
from PySpice.Unit import *


################################################################
####集合定义滤波器各种子电路模块
################################################################

# class BasicOperationalAmplifier(SubCircuitFactory):
#     """
#     理想运放定义模块
#     """
#
#     __name__ = 'BasicOperationalAmplifier'
#     __nodes__ = ('non_inverting_input', 'inverting_input', 'output')
#
#     ##############################################
#
#     def __init__(self):
#
#         super().__init__()
#
#         # Input impedance
#         self.R('input', 'non_inverting_input', 'inverting_input', 10@u_MΩ)
#
#         # dc gain=100k and pole1=100hz
#         # unity gain = dcgain x pole1 = 10MHZ
#         self.VCVS('gain', 1, self.gnd, 'non_inverting_input', 'inverting_input', voltage_gain=kilo(100))
#         self.R('P1', 1, 2, '1k')
#         self.C('P1', 2, self.gnd, '1.5915u')
#
#         # Output buffer and resistance
#         self.VCVS('buffer', 3, self.gnd, 2, self.gnd, 1)
#         self.R('out', 3, 'output', '10')


class My_AC_source(SubCircuitFactory):
    '''
    定义AC电压源，模拟mic输入
    前馈输入电容默认：10uf，反馈默认2.2uf
    负载电阻默认：22k
    '''
    __name__ = 'My_AC_source'
    __nodes__ = ('out',)

    def __init__(self, *, C_value='10u', R_value='22k', V='DC 2 AC 1 0'):
        super().__init__()
        # self.SinusoidalVoltageSource('input', 'in1', self.gnd, amplitude=1)
        self.V('input', 'in1', self.gnd, V)
        self.C('1', 'in1', 'out', C_value)
        self.R('1', 'out', self.gnd, R_value)


class My_OP_Mic(SubCircuitFactory):
    """
    同相运放电路，用于mic输入放大
    放大增益gain=(Ra+Rb)/Ra
    mic增益控制范围0-30dB,默认0dB
    阻抗22k
    """
    __name__ = 'My_OP_Mic'
    __nodes__ = ('in1', 'out')

    def __init__(self, *, Ra_value='22k', Rb_value='0'):
        super().__init__()

        self.subcircuit(BasicOperationalAmplifier())
        self.X('op', 'BasicOperationalAmplifier', 'in1', 1, 'out')

        self.R('a', 1, self.gnd, Ra_value)
        self.R('b', 1, 'out', Rb_value)


class My_one_order_C_R_series(SubCircuitFactory):
    """电容、电阻串联电路
    电阻默认阻值：R_value='2.2k'
    电容默认阻值：C_value='68n'
    """
    __name__ = 'My_one_order_C_R_series'
    __nodes__ = ('in1', 'out')

    def __init__(self, C_value='68n', R_value='2.2k'):
        super().__init__()
        self.C('1', 'in1', 1, C_value)
        self.R('1', '1', 'out', R_value)


class My_one_order_highpass(SubCircuitFactory):
    """1阶高通滤波器
    电阻默认阻值：R_value='2.2k'
    电容默认阻值：C_value='68n'
    默认截止频率：f=1/(2*pi*R*C)
    """
    __name__ = 'My_one_order_highpass'
    __nodes__ = ('in1', 'out')

    def __init__(self, C_value='68n', R_value='2.2k'):
        super().__init__()
        self.R('1', 'out', self.gnd, R_value)
        self.C('1', 'in1', 'out', C_value)


class My_one_order_highpass_mode2(SubCircuitFactory):
    """1阶高通滤波器,低频旁通
    电阻默认阻值：R_value='2.2k'
    电容默认阻值：C_value='68n'
    默认截止频率：f=1/(2*pi*R*C)
    """
    __name__ = 'My_one_order_highpass_mode2'
    __nodes__ = ('in1', 'out')

    def __init__(self, C_value='68n', R_value='2.2k', R2_value='1000k'):
        super().__init__()
        self.R('1', 'out', self.gnd, R_value)
        self.C('1', 'in1', 'out', C_value)
        self.R('2', 'in1', 'out', R2_value)


class My_one_order_lowpass(SubCircuitFactory):
    """1阶低通滤波器
    电阻默认阻值：R_value='2.2k'
    电容默认阻值：C_value='68n'
    默认截止频率：f=1/(2*pi*R*C)
    """
    __name__ = 'My_one_order_lowpass'
    __nodes__ = ('in1', 'out')

    def __init__(self, C_value='68n', R_value='2.2k'):
        super().__init__()
        self.R('1', 'in1', 'out', R_value)
        self.C('1', 'out', self.gnd, C_value)


class My_OP_gain(SubCircuitFactory):
    """反向运放电路
    分子电阻默认值：Rb_value='20k'
    分母电阻默认值：Ra_value='20k'
    默认增益：gain=Rb/Ra=0dB
    """
    __name__ = 'My_OP_gain'
    __nodes__ = ('in1', 'out', 'op_invert')

    def __init__(self, *, Ra_value='20k', Rb_value='20k'):
        super().__init__()

        self.subcircuit(BasicOperationalAmplifier())
        self.X('op01', 'BasicOperationalAmplifier', self.gnd, 'op_invert', 'out')

        self.R('a', 'in1', 'op_invert', Ra_value)
        self.R('b', 'op_invert', 'out', Rb_value)


class My_OP_lowpass(SubCircuitFactory):
    """
    运放电路反馈电容，用于低通滤波
    默认电容：C_value=‘39p’
    """
    __name__ = 'My_OP_lowpass'
    __nodes__ = ('out', 'op_invert')

    def __init__(self, *, C_value='3.9p'):
        super().__init__()
        self.C('1', 'op_invert', 'out', C_value)


class My_two_order_filter(SubCircuitFactory):
    """
    module01使用电路 fixme:创建的实例无法更改__name__属性
    模拟电路双二阶滤波器，实现带阻滤波或带通滤波功能
    带阻滤波器电阻默认：R_value=2.2k
    带通滤波器电阻默认：R_value=20k
    中心频率电容容值由get_capactitance_value函数提供（或者提供类似C_value='68n'字符）
    增益电阻阻值由get_resistance_value函数提供（或者提供R_value=?数值）
    """
    __name__ = 'My_two_order_filter'
    __nodes__ = ('in1', 'out')

    def __init__(self, *, C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k', R2_value='2.2k',
                 R_half_value='1.1k', R_gain_value='0'):
        super().__init__()
        self.R('1', 'in1', 1, R1_value)
        self.R('2', 1, 'out', R2_value)
        self.R('3', 2, self.gnd, R_gain_value)
        self.R('4', 3, self.gnd, R_half_value)
        self.C('3', 1, 2, C_value_double)
        self.C('1', 'in1', 3, C1_value)
        self.C('2', 3, 'out', C2_value)


class My_two_order_filter_02(SubCircuitFactory):
    """
    module02使用电路 fixme:创建的实例无法更改__name__属性
    模拟电路双二阶滤波器，实现带阻滤波或带通滤波功能
    带阻滤波器电阻默认：R_value=2.2k
    带通滤波器电阻默认：R_value=20k
    中心频率电容容值由get_capactitance_value函数提供（或者提供类似C_value='68n'字符）
    增益电阻阻值由get_resistance_value函数提供（或者提供R_value=?数值）
    """
    __name__ = 'My_two_order_filter_02'
    __nodes__ = ('in1', 'out')

    def __init__(self, *, C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k', R2_value='2.2k',
                 R_half_value='1.1k', R_gain_value='0'):
        super().__init__()
        self.R('1', 'in1', 1, R1_value)
        self.R('2', 1, 'out', R2_value)
        self.R('3', 2, self.gnd, R_gain_value)
        self.R('4', 3, self.gnd, R_half_value)
        self.C('3', 1, 2, C_value_double)
        self.C('1', 'in1', 3, C1_value)
        self.C('2', 3, 'out', C2_value)


class My_peak_filter_01(SubCircuitFactory):
    """自建peak filter电路"""
    __name__ = 'My_peak_filter_01'
    __nodes__ = ('input', 'out')

    def __init__(self, *, C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k', R2_value='20k',
                 R_half_value='10k', R_gain_value='0', R_high_cut='39k'):
        super().__init__()
        self.R('1', 'input', 1, R1_value)
        self.R('2', 1, 'out', R2_value)
        self.R('3', 4, self.gnd, R_half_value)
        self.R('gain', 2, self.gnd, R_gain_value)
        self.R('high_cut', 'input', '3', R_high_cut)
        self.C('1', 3, 4, C1_value)
        self.C('2', 4, 'out', C2_value)
        self.C('3', 1, 2, C_value_double)


class My_peak_filter_ams01(SubCircuitFactory):
    """保持跟AMS开发版peak filter一致"""
    __name__ = 'My_peak_filter_ams01'
    __nodes__ = ('input', 'out')

    def __init__(self, *, C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k', R2_value='20k',
                 R_half_value='10k', R_gain_value='0', R_high_cut='0'):
        super().__init__()
        self.R('1', 3, 1, R1_value)
        self.R('2', 1, 'out', R2_value)
        self.R('3', 4, self.gnd, R_half_value)
        self.R('gain', 2, self.gnd, R_gain_value)
        self.R('high_cut', 'input', '3', R_high_cut)
        self.C('1', 3, 4, C1_value)
        self.C('2', 4, 'out', C2_value)
        self.C('3', 1, 2, C_value_double)


class My_high_shelf_01(SubCircuitFactory):
    """电容、电阻串联电路
    电阻默认阻值：R_value='2.2k'
    电容默认阻值：C_value='68n'
    """
    __name__ = 'My_high_shelf_01'
    __nodes__ = ('in1', 'out')

    def __init__(self, *, C_value='680p', R_value='220k'):
        super().__init__()
        self.C('1', 'in1', 1, C_value)
        self.R('1', '1', 'out', R_value)


class My_low_shelf_01(SubCircuitFactory):
    """电容、电阻串联电路
    电阻默认阻值：R_value='2.2k'
    电容默认阻值：C_value='68n'
    """
    __name__ = 'My_low_shelf_01'
    __nodes__ = ('in1', 'out')

    def __init__(self, *, C_value='680p', R_value='220k'):
        super().__init__()
        self.C('1', 'in1', 1, C_value)
        self.R('1', '1', 'out', R_value)


class My_two_order_lowpass(SubCircuitFactory):
    """二阶无限增益多路反馈低通滤波电路"""
    __name__ = 'My_two_order_lowpass'
    __nodes__ = ('in1', 'out')

    def __init__(self, *, R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n', C2_value='12n'):
        super().__init__()

        self.subcircuit(BasicOperationalAmplifier())
        self.X('op', 'BasicOperationalAmplifier', self.gnd, 2, 'out')

        self.R('1', 'in1', 1, R1_value)
        self.R('2', 1, 'out', R2_value)
        self.R('3', 1, 2, R3_value)
        self.C('1', 2, 'out', C1_value)
        self.C('2', 1, self.gnd, C2_value)


# OP2
class My_two_order_filter_03(SubCircuitFactory):
    """
    module03使用电路 fixme:创建的实例无法更改__name__属性
    模拟电路双二阶滤波器，实现带阻滤波或带通滤波功能
    带阻滤波器电阻默认：R_value=2.2k
    带通滤波器电阻默认：R_value=20k
    中心频率电容容值由get_capactitance_value函数提供（或者提供类似C_value='68n'字符）
    增益电阻阻值由get_resistance_value函数提供（或者提供R_value=?数值）
    """
    __name__ = 'My_two_order_filter_03'
    __nodes__ = ('in1', 'out')

    def __init__(self, *, C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k', R2_value='2.2k',
                 R_half_value='1.1k', R_gain_value='0'):
        super().__init__()
        self.R('1', 'in1', 1, R1_value)
        self.R('2', 1, 'out', R2_value)
        self.R('3', 2, self.gnd, R_gain_value)
        self.R('4', 3, self.gnd, R_half_value)
        self.C('3', 1, 2, C_value_double)
        self.C('1', 'in1', 3, C1_value)
        self.C('2', 3, 'out', C2_value)


class My_two_order_filter_04(SubCircuitFactory):
    """
    module03使用电路 fixme:创建的实例无法更改__name__属性
    模拟电路双二阶滤波器，实现带阻滤波或带通滤波功能
    带阻滤波器电阻默认：R_value=2.2k
    带通滤波器电阻默认：R_value=20k
    中心频率电容容值由get_capactitance_value函数提供（或者提供类似C_value='68n'字符）
    增益电阻阻值由get_resistance_value函数提供（或者提供R_value=?数值）
    """
    __name__ = 'My_two_order_filter_04'
    __nodes__ = ('in1', 'out')

    def __init__(self, *, C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k', R2_value='2.2k',
                 R_half_value='1.1k', R_gain_value='0'):
        super().__init__()
        self.R('1', 'in1', 1, R1_value)
        self.R('2', 1, 'out', R2_value)
        self.R('3', 2, self.gnd, R_gain_value)
        self.R('4', 3, self.gnd, R_half_value)
        self.C('3', 1, 2, C_value_double)
        self.C('1', 'in1', 3, C1_value)
        self.C('2', 3, 'out', C2_value)


class My_one_order_highpass_2(SubCircuitFactory):
    """1阶高通滤波器
    电阻默认阻值：R_value='2.2k'
    电容默认阻值：C_value='68n'
    默认截止频率：f=1/(2*pi*R*C)
    """
    __name__ = 'My_one_order_highpass_2'
    __nodes__ = ('in1', 'out')

    def __init__(self, C_value='68n', R_value='2.2k'):
        super().__init__()
        self.R('1', 'out', self.gnd, R_value)
        self.C('1', 'in1', 'out', C_value)


class My_one_order_lowpass_2(SubCircuitFactory):
    """1阶低通滤波器
    电阻默认阻值：R_value='2.2k'
    电容默认阻值：C_value='68n'
    默认截止频率：f=1/(2*pi*R*C)
    """
    __name__ = 'My_one_order_lowpass_2'
    __nodes__ = ('in1', 'out')

    def __init__(self, C_value='68n', R_value='2.2k'):
        super().__init__()
        self.R('1', 'in1', 'out', R_value)
        self.C('1', 'out', self.gnd, C_value)


class My_OP_gain_2(SubCircuitFactory):
    """反向运放电路
    分子电阻默认值：Rb_value='20k'
    分母电阻默认值：Ra_value='20k'
    默认增益：gain=Rb/Ra=0dB
    """
    __name__ = 'My_OP_gain_2'
    __nodes__ = ('in1', 'out', 'op_invert')

    def __init__(self, *, Ra_value='20k', Rb_value='20k'):
        super().__init__()

        self.subcircuit(BasicOperationalAmplifier())
        self.X('op02', 'BasicOperationalAmplifier', self.gnd, 'op_invert', 'out')

        self.R('a', 'in1', 'op_invert', Ra_value)
        self.R('b', 'op_invert', 'out', Rb_value)


class My_OP_lowpass_2(SubCircuitFactory):
    """
    运放电路反馈电容，用于低通滤波
    默认电容：C_value=‘39p’
    """
    __name__ = 'My_OP_lowpass_2'
    __nodes__ = ('out', 'op_invert')

    def __init__(self, *, C_value='3.9p'):
        super().__init__()
        self.C('1', 'op_invert', 'out', C_value)


class My_peak_filter_02(SubCircuitFactory):
    """自建peak filter电路"""
    __name__ = 'My_peak_filter_02'
    __nodes__ = ('input', 'out')

    def __init__(self, *, C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k', R2_value='20k',
                 R_half_value='10k', R_gain_value='0', R_high_cut='39k'):
        super().__init__()
        self.R('1', 'input', 1, R1_value)
        self.R('2', 1, 'out', R2_value)
        self.R('3', 4, self.gnd, R_half_value)
        self.R('gain', 2, self.gnd, R_gain_value)
        self.R('high_cut', 'input', '3', R_high_cut)
        self.C('1', 3, 4, C1_value)
        self.C('2', 4, 'out', C2_value)
        self.C('3', 1, 2, C_value_double)


class My_peak_filter_ams02(SubCircuitFactory):
    """保持跟AMS开发版peak filter一致"""
    __name__ = 'My_peak_filter_ams02'
    __nodes__ = ('input', 'out')

    def __init__(self, *, C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k', R2_value='20k',
                 R_half_value='10k', R_gain_value='0', R_high_cut='0'):
        super().__init__()
        self.R('1', 3, 1, R1_value)
        self.R('2', 1, 'out', R2_value)
        self.R('3', 4, self.gnd, R_half_value)
        self.R('gain', 2, self.gnd, R_gain_value)
        self.R('high_cut', 'input', '3', R_high_cut)
        self.C('1', 3, 4, C1_value)
        self.C('2', 4, 'out', C2_value)
        self.C('3', 1, 2, C_value_double)


class My_high_shelf_02(SubCircuitFactory):
    """电容、电阻串联电路
    电阻默认阻值：R_value='2.2k'
    电容默认阻值：C_value='68n'
    """
    __name__ = 'My_high_shelf_02'
    __nodes__ = ('in1', 'out')

    def __init__(self, *, C_value='680p', R_value='220k'):
        super().__init__()
        self.C('1', 'in1', 1, C_value)
        self.R('1', '1', 'out', R_value)


class My_low_shelf_02(SubCircuitFactory):
    """电容、电阻串联电路
    电阻默认阻值：R_value='2.2k'
    电容默认阻值：C_value='68n'
    """
    __name__ = 'My_low_shelf_02'
    __nodes__ = ('in1', 'out')

    def __init__(self, *, C_value='680p', R_value='220k'):
        super().__init__()
        self.C('1', 'in1', 1, C_value)
        self.R('1', '1', 'out', R_value)


class My_two_order_lowpass_02(SubCircuitFactory):
    """二阶无限增益多路反馈低通滤波电路"""
    __name__ = 'My_two_order_lowpass_02'
    __nodes__ = ('in1', 'out')

    def __init__(self, *, R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n', C2_value='12n'):
        super().__init__()

        self.subcircuit(BasicOperationalAmplifier())
        self.X('op', 'BasicOperationalAmplifier', self.gnd, 2, 'out')

        self.R('1', 'in1', 1, R1_value)
        self.R('2', 1, 'out', R2_value)
        self.R('3', 1, 2, R3_value)
        self.C('1', 2, 'out', C1_value)
        self.C('2', 1, self.gnd, C2_value)
