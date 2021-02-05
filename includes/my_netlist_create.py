#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/1/22 16:48
from PySpice.Plot.BodeDiagram import bode_diagram
from PySpice.Spice.Parser import SpiceParser
from PySpice.Spice.Netlist import Circuit
from includes.my_subcircuit import *


class MyNetlistCreate(object):
    """根据UI界面传递过来的参数创建仿真电路图"""

    def __init__(self, *, my_netlist_path=None, op_model=None, ac_source=None, mic_op_gain_data=None,
                 two_order_filter_data=None, two_order_filter_data_02=None,
                 one_order_highpass_data=None, one_order_lowpass_data=None,
                 op_gain_data=None, op_lowpass_data=None,
                 high_shelf_data=None, low_shelf_data=None,
                 op_peak_data=None, two_order_lowpass_data=None,
                 module_01=None, module_02=None, module_03=None, module_04=None, module_05=None,
                 module_06=None, module_07=None,
                 two_order_filter_data_11=None, two_order_filter_data_12=None,
                 one_order_highpass_data_2=None, one_order_lowpass_data_2=None,
                 op_gain_data_2=None, op_lowpass_data_2=None,
                 high_shelf_data_2=None, low_shelf_data_2=None,
                 op_peak_data_2=None, two_order_lowpass_data_2=None,
                 module_11=None, module_12=None, module_13=None, module_14=None, module_15=None,
                 module_16=None, module_17=None):
        self.default_data()
        self.op_model = op_model
        self.ac_source = ac_source
        self.module01 = module_01
        self.module02 = module_02
        self.module03 = module_03
        self.module04 = module_04
        self.module05 = module_05
        self.module06 = module_06
        self.module07 = module_07
        self.module11 = module_11
        self.module12 = module_12
        self.module13 = module_13
        self.module14 = module_14
        self.module15 = module_15
        self.module16 = module_16
        self.module17 = module_17
        if mic_op_gain_data:
            self.mic_op_gain_data = mic_op_gain_data
        if two_order_filter_data:
            self.two_order_filter_data = two_order_filter_data
        if two_order_filter_data_02:
            self.two_order_filter_data_02 = two_order_filter_data_02
        if one_order_highpass_data:
            self.one_order_highpass_data = one_order_highpass_data
        if one_order_lowpass_data:
            self.one_order_lowpass_data = one_order_lowpass_data
        if op_gain_data:
            self.op_gain_data = op_gain_data
        if op_lowpass_data:
            self.op_lowpass_data = op_lowpass_data
        if high_shelf_data:
            self.high_shelf_data = high_shelf_data
        if low_shelf_data:
            self.low_shelf_data = low_shelf_data
        if op_peak_data:
            self.op_peak_data = op_peak_data
        if two_order_lowpass_data:
            self.two_order_lowpass_data = two_order_lowpass_data

        if two_order_filter_data_11:
            self.two_order_filter_data_11 = two_order_filter_data_11
        if two_order_filter_data_12:
            self.two_order_filter_data_12 = two_order_filter_data_12
        if one_order_highpass_data_2:
            self.one_order_highpass_data_2 = one_order_highpass_data_2
        if one_order_lowpass_data_2:
            self.one_order_lowpass_data_2 = one_order_lowpass_data_2
        if op_gain_data_2:
            self.op_gain_data_2 = op_gain_data_2
        if op_lowpass_data_2:
            self.op_lowpass_data_2 = op_lowpass_data_2
        if high_shelf_data_2:
            self.high_shelf_data_2 = high_shelf_data_2
        if low_shelf_data_2:
            self.low_shelf_data_2 = low_shelf_data_2
        if op_peak_data_2:
            self.op_peak_data_2 = op_peak_data_2
        if two_order_lowpass_data_2:
            self.two_order_lowpass_data_2 = two_order_lowpass_data_2
        if my_netlist_path:
            self._path = my_netlist_path
            self.parser_netlist()

    def default_data(self):

        self.mic_op_gain_data = dict(Ra_value=22000, Rb_value=0)
        # OP 01
        self.two_order_filter_data = dict(C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k',
                                          R2_value='2.2k', R_half_value='1.1k', R_gain_value=0)
        self.two_order_filter_data_02 = dict(C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k',
                                             R2_value='2.2k', R_half_value='1.1k', R_gain_value=0)
        self.one_order_highpass_data = dict(C_value='68n', R_value='2.2k', R2_value='2.2k')
        self.one_order_lowpass_data = dict(C_value='68n', R_value='2.2k')
        self.op_gain_data = dict(Ra_value='20k', Rb_value='20k')
        self.op_lowpass_data = dict(C_value='3.9p')
        self.high_shelf_data = dict(C_value='680p', R_value='220k')
        self.low_shelf_data = dict(C_value='680p', R_value='220k')
        self.op_peak_data = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k',
                                 R2_value='20k',
                                 R_half_value='10k', R_gain_value=0, R_high_cut='39k')
        self.two_order_lowpass_data = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                                           C2_value='12n')
        # OP 02
        self.two_order_filter_data_11 = dict(C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k',
                                             R2_value='2.2k', R_half_value='1.1k', R_gain_value=0)
        self.two_order_filter_data_12 = dict(C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k',
                                             R2_value='2.2k', R_half_value='1.1k', R_gain_value=0)
        self.one_order_highpass_data_2 = dict(C_value='68n', R_value='2.2k')
        self.one_order_lowpass_data_2 = dict(C_value='68n', R_value='2.2k')
        self.op_gain_data_2 = dict(Ra_value='20k', Rb_value='20k')
        self.op_lowpass_data_2 = dict(C_value='8.2n')
        self.high_shelf_data_2 = dict(C_value='680p', R_value='220k')
        self.low_shelf_data_2 = dict(C_value='680p', R_value='220k')
        self.op_peak_data_2 = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k', R2_value='20k',
                                   R_half_value='10k', R_gain_value=0, R_high_cut='39k')
        self.two_order_lowpass_data_2 = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                                             C2_value='12n')

    def parser_netlist(self):
        """
        解析netlist
        :return:self.circurt属性绑定解析的netlist电路
        """
        parser = SpiceParser(path=self._path)
        self.circuit = parser.build_circuit()
        print(str(self.circuit))

    def create_netlist(self):
        self.circuit = Circuit('ANC Filter')
        self.creat_Mic_input(self.ac_source)  # 输入
        self.creat_Mic_OP_gain(self.mic_op_gain_data)  # mic放大器
        self.circuit.R('load', 'output', self.circuit.gnd, '1000k')  # 负载电阻
        self.circuit.R('load2', 'op02_out', self.circuit.gnd, '1000k')  # 负载电阻
        self.create_module01(self.module01)
        self.create_module02(self.module02)
        self.create_module03(self.module03)  # op gain
        self.create_module04(self.module04)  # high shelf
        self.create_module05(self.module05)  # low shelf
        self.create_module06(self.module06)  # op low pass
        self.create_module07(self.module07)  # op peak
        if self.op_model == 'two_op':
            self.create_module11(self.module11)
            self.create_module12(self.module12)
            self.create_module13(self.module13)  # op gain
            self.create_module14(self.module14)  # high shelf
            self.create_module15(self.module15)  # low shelf
            self.create_module16(self.module16)  # op low pass
            self.create_module17(self.module17)  # op peak

    def creat_Mic_input(self, source=None):
        """模拟mic 输入，输入电容10uf,阻抗22k"""
        if source:
            self.circuit.subcircuit(My_AC_source(V=source))
        else:
            self.circuit.subcircuit(My_AC_source())
        self.circuit.X('Mic_input', 'My_AC_source', 'Mic_in')

    def creat_Mic_OP_gain(self, data):
        """创建mic输入运放，采用正相输入"""
        self.circuit.subcircuit(My_OP_Mic(**data))
        self.circuit.X('Mic_gain', 'My_OP_Mic', 'Mic_in', 'input')

    def create_module01(self, module=None):
        """
        创建01模块fiter circuit
        :param module:三个类型可选 highpass、bypass(默认)、notch
        :param data:参考class字典默认参数设置
        :return:接口为in，out子电路模块
        """
        if module == 'notch':
            self.circuit.subcircuit(My_two_order_filter(**self.two_order_filter_data))
            self.circuit.X('filter01', 'My_two_order_filter', 'input', 'out01')
        elif module == 'highpass':
            # self.circuit.subcircuit(My_one_order_highpass(**self.one_order_highpass_data))
            # self.circuit.X('filter01', 'My_one_order_highpass', 'input', 'out01')
            # print('highpass filter 01 set OK')
            self.circuit.subcircuit(My_one_order_highpass_mode2(**self.one_order_highpass_data))
            self.circuit.X('filter01', 'My_one_order_highpass_mode2', 'input', 'out01')
        else:
            self.circuit.R('01', 'input', 'out01', 0)
            # print('bypass filter 01 set OK')

    def create_module02(self, module=None):
        """
        创建01模块fiter circuit
        :param module:三个类型可选 highpass、bypass(默认)、notch
        :param data:参考class字典默认参数设置
        :return:接口为in，out子电路模块
        """
        if module == 'notch':
            self.circuit.subcircuit(My_two_order_filter_02(**self.two_order_filter_data_02))
            self.circuit.X('filter02', 'My_two_order_filter_02', 'out01', 'out02')
        elif module == 'lowpass':
            self.circuit.subcircuit(My_one_order_lowpass(**self.one_order_lowpass_data))
            self.circuit.X('filter02', 'My_one_order_lowpass', 'out01', 'out02')
        else:
            self.circuit.R('02', 'out01', 'out02', 0)

    def create_module03(self, module=None):
        """运放增益调整模块"""
        if module == 'op_one_order':
            self.circuit.subcircuit(My_OP_gain(**self.op_gain_data))
            self.circuit.X('OP_gain', 'My_OP_gain', 'out02', 'output', 'op_invert')
        if module == 'op_two_order':
            self.circuit.subcircuit(My_two_order_lowpass(**self.two_order_lowpass_data))
            self.circuit.X('two_order_lowpass', 'My_two_order_lowpass', 'out02', 'output')
        else:
            pass

    def create_module04(self, module=None):
        if module == 'high_shelf':
            self.circuit.subcircuit(My_high_shelf_01(**self.high_shelf_data))
            self.circuit.X('high_shelf', 'My_high_shelf_01', 'out02', 'op_invert')
        else:
            pass

    def create_module05(self, module=None):
        if module == 'low_shelf':
            self.circuit.subcircuit(My_low_shelf_01(**self.low_shelf_data))
            self.circuit.X('low_shelf', 'My_low_shelf_01', 'op_invert', 'output')
        else:
            pass

    def create_module06(self, module=None):
        """运放lowpass模块"""
        if module == 'op_lowpass':
            self.circuit.subcircuit(My_OP_lowpass(**self.op_lowpass_data))
            self.circuit.X('OP_lowpass', 'My_OP_lowpass', 'op_invert', 'output')
        else:
            pass

    def create_module07(self, module=None):
        """peak module"""
        if module == 'peak':
            self.circuit.subcircuit(My_peak_filter_01(**self.op_peak_data))
            self.circuit.X('peak01', 'My_peak_filter_01', 'op_invert', 'output')
        elif module == 'peak_ams':
            self.circuit.subcircuit(My_peak_filter_ams01(**self.op_peak_data))
            self.circuit.X('peak01', 'My_peak_filter_ams01', 'op_invert', 'output')
        else:
            pass

    # op 02
    def create_module11(self, module=None):
        """
        创建11模块fiter circuit
        :param module:三个类型可选 highpass、bypass(默认)、notch
        :param data:参考class字典默认参数设置
        :return:接口为in，out子电路模块
        """
        if module == 'notch':
            self.circuit.subcircuit(My_two_order_filter_03(**self.two_order_filter_data_11))
            self.circuit.X('filter11', 'My_two_order_filter_03', 'output', 'out11')
        elif module == 'highpass':
            self.circuit.subcircuit(My_one_order_highpass_2(**self.one_order_highpass_data_2))
            self.circuit.X('filter11', 'My_one_order_highpass_2', 'output', 'out11')
            # print('highpass filter 01 set OK')
        else:
            self.circuit.R('11', 'output', 'out11', 0)
            # print('bypass filter 01 set OK')

    def create_module12(self, module=None):
        """
        创建01模块fiter circuit
        :param module:三个类型可选 highpass、bypass(默认)、notch
        :param data:参考class字典默认参数设置
        :return:接口为in，out子电路模块
        """
        if module == 'notch':
            self.circuit.subcircuit(My_two_order_filter_04(**self.two_order_filter_data_12))
            self.circuit.X('filter12', 'My_two_order_filter_04', 'out11', 'out12')
        elif module == 'lowpass':
            self.circuit.subcircuit(My_one_order_lowpass_2(**self.one_order_lowpass_data_2))
            self.circuit.X('filter12', 'My_one_order_lowpass_2', 'out11', 'out12')
        else:
            self.circuit.R('12', 'out11', 'out12', 0)

    def create_module13(self, module=None):
        """运放增益调整模块"""
        if module == 'op_one_order':
            self.circuit.subcircuit(My_OP_gain_2(**self.op_gain_data_2))
            self.circuit.X('OP_gain_2', 'My_OP_gain_2', 'out12', 'op02_out', 'op02_invert')
        if module == 'op_two_order':
            self.circuit.subcircuit(My_two_order_lowpass_02(**self.two_order_lowpass_data_2))
            self.circuit.X('two_order_lowpass_2', 'My_two_order_lowpass_02', 'out12', 'op02_out')
        else:
            pass

    def create_module14(self, module=None):
        if module == 'high_shelf':
            self.circuit.subcircuit(My_high_shelf_02(**self.high_shelf_data_2))
            self.circuit.X('high_shelf_2', 'My_high_shelf_02', 'out12', 'op02_invert')
        else:
            pass

    def create_module15(self, module=None):
        if module == 'low_shelf':
            self.circuit.subcircuit(My_low_shelf_02(**self.low_shelf_data_2))
            self.circuit.X('low_shelf_2', 'My_low_shelf_02', 'op02_invert', 'op02_out')
        else:
            pass

    def create_module16(self, module=None):
        """运放lowpass模块"""
        if module == 'op_lowpass':
            self.circuit.subcircuit(My_OP_lowpass_2(**self.op_lowpass_data_2))
            self.circuit.X('OP_lowpass_2', 'My_OP_lowpass_2', 'op02_invert', 'op02_out')
        else:
            pass

    def create_module17(self, module=None):
        """peak module"""
        if module == 'peak':
            self.circuit.subcircuit(My_peak_filter_02(**self.op_peak_data_2))
            self.circuit.X('peak02', 'My_peak_filter_02', 'op02_invert', 'op02_out')
        elif module == 'peak_ams':
            self.circuit.subcircuit(My_peak_filter_ams02(**self.op_peak_data_2))
            self.circuit.X('peak02', 'My_peak_filter_ams02', 'op02_invert', 'op02_out')
        else:
            pass


if __name__ == '__main__':
    import numpy as np
    import matplotlib.pyplot as plt
    from PySpice.Unit import *

    # import matplotlib
    # matplotlib.use("Qt5Agg")
    mic_op_gain_data_default = dict(Ra_value=22000, Rb_value=0)
    two_order_filter_data_default = dict(C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k',
                                         R2_value='2.2k', R_half_value='1.1k', R_gain_value='0')
    two_order_filter_data_02_default = dict(C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k',
                                            R2_value='2.2k', R_half_value='1.1k', R_gain_value='0')
    one_order_highpass_data_default = dict(C_value='68n', R_value='2.2k')
    one_order_lowpass_data_default = dict(C_value='68n', R_value='2.2k')
    op_gain_data_default = dict(Ra_value='20k', Rb_value='20k')
    op_lowpass_data_default = dict(C_value='3.9p')
    high_shelf_data_default = dict(C_value='680p', R_value='2200k')
    low_shelf_data_default = dict(C_value='680p', R_value='2200k')
    op_peak_data_default = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k', R2_value='20k',
                                R_half_value='10k', R_gain_value='0', R_high_cut='39k')
    two_order_lowpass_data_default = dict(R1_value='18k', R2_value='18k', R3_value='9k', C1_value='4.7n',
                                          C2_value='62n')

    two_order_filter_data_11 = dict(C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k',
                                    R2_value='2.2k', R_half_value='1.1k', R_gain_value='0')
    two_order_filter_data_12 = dict(C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k',
                                    R2_value='2.2k', R_half_value='1.1k', R_gain_value='0')
    one_order_highpass_data_2 = dict(C_value='68n', R_value='2.2k')
    one_order_lowpass_data_2 = dict(C_value='68n', R_value='2.2k')
    op_gain_data_2 = dict(Ra_value='20k', Rb_value='20k')
    op_lowpass_data_2 = dict(C_value='8.2n')
    high_shelf_data_2 = dict(C_value='680p', R_value='220k')
    low_shelf_data_2 = dict(C_value='680p', R_value='220k')
    op_peak_data_2 = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k', R2_value='20k',
                          R_half_value='10k', R_gain_value='0', R_high_cut='39k')
    two_order_lowpass_data_2 = dict(R1_value='27k', R2_value='27k', R3_value='13k', C1_value='4.7n',
                                    C2_value='12n')

    my_netlist = MyNetlistCreate(two_order_filter_data=two_order_filter_data_default, module_01='notch',
                                 two_order_filter_data_02=two_order_filter_data_02_default, module_02='bypass',
                                 one_order_lowpass_data=one_order_lowpass_data_default,
                                 one_order_highpass_data=one_order_highpass_data_default,
                                 op_gain_data=op_gain_data_default, ac_source='DC 2 AC 1 180',
                                 two_order_lowpass_data=two_order_lowpass_data_default, module_03='op_one_order',
                                 high_shelf_data=high_shelf_data_default, module_04=None,
                                 low_shelf_data=low_shelf_data_default, module_05=None,
                                 op_lowpass_data=op_lowpass_data_default, module_06=None,
                                 op_peak_data=op_peak_data_default, module_07=None,
                                 two_order_filter_data_11=two_order_filter_data_11,
                                 two_order_filter_data_12=two_order_filter_data_12,
                                 one_order_highpass_data_2=one_order_highpass_data_2,
                                 one_order_lowpass_data_2=one_order_lowpass_data_2,
                                 op_gain_data_2=op_gain_data_2, op_lowpass_data_2=op_lowpass_data_2,
                                 high_shelf_data_2=high_shelf_data_2, low_shelf_data_2=low_shelf_data_2,
                                 op_peak_data_2=op_peak_data_2, two_order_lowpass_data_2=two_order_lowpass_data_2,
                                 module_11='notch', module_12=None, module_13='op_one_order', module_14=None,
                                 module_15=None, module_16=None, module_17=None, op_model='two_op')
    my_netlist.create_netlist()
    print(str(my_netlist.circuit))

    simulator = my_netlist.circuit.simulator(temperature=25, nominal_temperature=25)
    analysis = simulator.ac(start_frequency=10 @ u_Hz, stop_frequency=20 @ u_kHz, number_of_points=200, variation='dec')

    figure = plt.figure(1, (20, 10))
    plt.title("Bode Diagram of an Operational Amplifier")
    bode_diagram(axes=(plt.subplot(211), plt.subplot(212)),
                 frequency=analysis.frequency,
                 gain=20 * np.log10(np.absolute(analysis.op02_out)),
                 phase=np.angle(analysis.op02_out, deg=False),
                 marker='.',
                 color='blue',
                 linestyle='-',
                 )
    bode_diagram(axes=(plt.subplot(211), plt.subplot(212)),
                 frequency=analysis.frequency,
                 gain=20 * np.log10(np.absolute(analysis.output)),
                 phase=np.angle(analysis.output, deg=False),
                 marker='.',
                 color='red',
                 linestyle='-',
                 )
    plt.tight_layout()
    plt.show()
