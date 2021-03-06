#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/2/27 17:05

import sys
from PyQt5 import QtCore, QtWidgets
from value_tuning.peak_tuning_all_UI import Ui_Dialog


class MyPeakFilterTuningAllDialog(QtWidgets.QDialog, Ui_Dialog):
    signal = QtCore.pyqtSignal(dict, bool, dict, bool, dict, bool, dict, bool, dict)

    def __init__(self, argv_peak, module_peak, argv_ls, module_ls, argv_hs, module_hs, argv_lp, module_lp, argv_gain):
        """
        滤波器阻容参数手动调节对话框
        :param argv_peak: 下拉菜单参数
        :param module_peak: 功能是否启用
        """
        super(MyPeakFilterTuningAllDialog, self).__init__()
        self.data_peak = argv_peak
        self.data_ls = argv_ls
        self.data_hs = argv_hs
        self.data_lp = argv_lp
        self.data_gain = argv_gain
        self.peak_enable = module_peak
        self.ls_enable = module_ls
        self.hs_enable = module_hs
        self.lp_enable = module_lp
        self.setupUi(self)
        self.set_items()
        self.set_initial_value(argv_peak, module_peak, argv_ls, module_ls, argv_hs, module_hs, argv_lp, module_lp,
                               argv_gain)
        self.signal_slot()

    def set_items(self):
        """设置下拉菜单默认内容"""
        r_items = ['0', '2.2', '2.4', '2.7', '3.0', '3.3', '3.6',
                   '3.9', '4.3', '4.7', '5.1', '5.6', '6.2', '6.8',
                   '7.5', '8.2', '9.1', '10', '11', '12', '13',
                   '15', '16', '18',
                   '20', '22', '24', '27', '30', '33', '36',
                   '39', '43', '47', '51', '56', '62', '68',
                   '75', '82', '91', '100', '110', '120', '130',
                   '150', '160', '180',
                   '200', '220', '240', '270', '300', '330', '360',
                   '390', '430', '470', '510', '560', '620', '680',
                   '750', '820', '910', '1k', '1.1k', '1.2k', '1.3k',
                   '1.5k', '1.6k', '1.8k',
                   '2k', '2.2k', '2.4k', '2.7k', '3k', '3.3k', '3.6k',
                   '3.9k', '4.3k', '4.7k', '5.1k', '5.6k', '6.2k', '6.8k',
                   '7.5k', '8.2k', '9.1k', '10k', '11k', '12k', '13k',
                   '15k', '16k', '18k', '20k', '22k', '24k', '27k',
                   '30k', '33k', '36k', '39k', '43k', '47k', '51k',
                   '56k', '62k', '68k', '75k', '82k', '91k', '100k',
                   '110k', '120k', '130k', '150k', '160k', '180k', '200k',
                   '220k', '240k', '270k', '300k', '330k', '360k',
                   '390k', '430k', '470k', '510k', '560k', '620k', '680k', '750k', '820k', '910k', '1000k',
                   '1100k', '1200k', '1500k', '1600k', '1800k', '2000k', '2200k', '2400k', '2700k', '3000k', '3300k',
                   '3600k',
                   '3900k', '4300k', '4700k', '5100k', '5600k', '6200k', '6800k', '7500k', '8200k', '9100k', '10000k', ]
        c_items = ['10p', '12p', '15p', '18p', '22p', '27p', '33p', '39p', '47p', '56p', '68p', '82p',
                   '100p', '120p', '150p', '180p', '220p', '270p', '330p', '390p', '470p', '560p', '680p', '820p',
                   '1n', '1.2n', '1.5n', '1.8n', '2.2n', '2.7n', '3.3n', '3.9n', '4.7n', '5.6n', '6.8n', '8.2n',
                   '10n', '12n', '15n', '18n', '22n', '27n', '33n', '39n', '47n', '56n', '68n', '82n',
                   '100n', '120n', '150n', '180n', '220n', '270n', '330n', '390n', '470n', '560n', '680n', '820n',
                   '1u', '1.2u', '1.5u', '1.8u', '2.2u', '2.7u', '3.3u', '3.9u', '4.7u', '5.6u', '6.8u', '8.2u',
                   '10u', '12u', '15u', '18u', '22u', '27u', '33u', '39u', '47u', '56u', '68u', '82u', '91u', '100u']
        self.R1.addItems(r_items)
        self.R2.addItems(r_items)
        self.R3.addItems(r_items)
        self.R4.addItems(r_items)
        self.R5.addItems(r_items)
        self.Ra.addItems(r_items)
        self.Rb.addItems(r_items)
        self.R6.addItems(r_items)
        self.R7.addItems(r_items)
        self.C1.addItems(c_items)
        self.C2.addItems(c_items)
        self.C3.addItems(c_items)
        self.C4.addItems(c_items)
        self.C5.addItems(c_items)
        self.C6.addItems(c_items)

    def set_initial_value(self, argv_peak, module_peak, argv_ls, module_ls, argv_hs, module_hs, argv_lp, module_lp,
                          argv_gain):
        """根据传入参数设置下拉菜单选择项，否则设置为默认值"""
        # peak
        self.checkBox_peak.setChecked(module_peak)  # 设置启用键
        self.R1.setCurrentText(argv_peak['R1_value'])
        self.R2.setCurrentText(argv_peak['R2_value'])
        self.R3.setCurrentText(str(argv_peak['R_gain_value']))
        self.R4.setCurrentText(argv_peak['R_half_value'])
        self.R5.setCurrentText(argv_peak['R_high_cut'])
        self.C1.setCurrentText(argv_peak['C1_value'])
        self.C2.setCurrentText(argv_peak['C2_value'])
        self.C3.setCurrentText(argv_peak['C_value_double'])
        # ls
        self.checkBox_ls.setChecked(module_ls)
        self.C5.setCurrentText(argv_ls['C_value'])
        self.R7.setCurrentText(argv_ls['R_value'])
        # hs
        self.checkBox_hs.setChecked(module_hs)
        self.C4.setCurrentText(argv_hs['C_value'])
        self.R6.setCurrentText(argv_hs['R_value'])
        # lp
        self.checkBox_lp.setChecked(module_lp)
        self.C6.setCurrentText(argv_lp['C_value'])
        # gain
        self.Ra.setCurrentText(argv_gain['Ra_value'])
        self.Rb.setCurrentText(argv_gain['Rb_value'])

        self.set_data_value()
        self.set_combobox_enabled()

    def signal_slot(self):
        self.checkBox_peak.toggled.connect(self.set_combobox_enabled)  # 启用功能键设置
        self.checkBox_ls.toggled.connect(self.set_combobox_enabled)  # 启用功能键设置
        self.checkBox_hs.toggled.connect(self.set_combobox_enabled)  # 启用功能键设置
        self.checkBox_lp.toggled.connect(self.set_combobox_enabled)  # 启用功能键设置
        # peak
        self.R1.currentIndexChanged.connect(self.set_data_value)  # data参数设置
        self.R2.currentIndexChanged.connect(self.set_data_value)
        self.R3.currentIndexChanged.connect(self.set_data_value)
        self.R4.currentIndexChanged.connect(self.set_data_value)
        self.R5.currentIndexChanged.connect(self.set_data_value)
        self.R6.currentIndexChanged.connect(self.set_data_value)
        self.R7.currentIndexChanged.connect(self.set_data_value)
        self.Ra.currentIndexChanged.connect(self.set_data_value)
        self.Rb.currentIndexChanged.connect(self.set_data_value)
        self.C1.currentIndexChanged.connect(self.set_data_value)
        self.C2.currentIndexChanged.connect(self.set_data_value)
        self.C3.currentIndexChanged.connect(self.set_data_value)
        self.C4.currentIndexChanged.connect(self.set_data_value)
        self.C5.currentIndexChanged.connect(self.set_data_value)
        self.C6.currentIndexChanged.connect(self.set_data_value)

        self.pushButton_OK.clicked.connect(self.return_data)
        self.pushButton_Cancel.clicked.connect(self.reject)

    def set_combobox_enabled(self):
        if self.checkBox_peak.isChecked():
            self.peak_enable = True
            self.R1.setEnabled(True)
            self.R2.setEnabled(True)
            self.R3.setEnabled(True)
            self.R4.setEnabled(True)
            self.R5.setEnabled(True)
            self.C1.setEnabled(True)
            self.C2.setEnabled(True)
            self.C3.setEnabled(True)
        else:
            self.peak_enable = False
            self.R1.setEnabled(False)
            self.R2.setEnabled(False)
            self.R3.setEnabled(False)
            self.R4.setEnabled(False)
            self.R5.setEnabled(False)
            self.C1.setEnabled(False)
            self.C2.setEnabled(False)
            self.C3.setEnabled(False)
        if self.checkBox_ls.isChecked():
            self.ls_enable = True
            self.R7.setEnabled(True)
            self.C5.setEnabled(True)
        else:
            self.ls_enable = False
            self.R7.setEnabled(False)
            self.C5.setEnabled(False)
        if self.checkBox_hs.isChecked():
            self.hs_enable = True
            self.R6.setEnabled(True)
            self.C4.setEnabled(True)
        else:
            self.hs_enable = False
            self.R6.setEnabled(False)
            self.C4.setEnabled(False)
        if self.checkBox_lp.isChecked():
            self.lp_enable = True
            self.C6.setEnabled(True)
        else:
            self.lp_enable = False
            self.C6.setEnabled(False)
        if self.checkBox_peak.isChecked() or self.checkBox_ls.isChecked()\
                or self.checkBox_hs.isChecked() or self.checkBox_lp.isChecked():
            self.Ra.setEnabled(True)
            self.Rb.setEnabled(True)
        else:
            self.Ra.setEnabled(False)
            self.Rb.setEnabled(False)

    def set_data_value(self, i=None):
        # peak
        self.data_peak['R1_value'] = self.R1.currentText()
        self.data_peak['R2_value'] = self.R2.currentText()
        self.data_peak['R_gain_value'] = self.R3.currentText()
        self.data_peak['R_half_value'] = self.R4.currentText()
        self.data_peak['R_high_cut'] = self.R5.currentText()
        self.data_peak['C1_value'] = self.C1.currentText()
        self.data_peak['C2_value'] = self.C2.currentText()
        self.data_peak['C_value_double'] = self.C3.currentText()
        # ls
        self.data_ls['R_value'] = self.R7.currentText()
        self.data_ls['C_value'] = self.C5.currentText()
        # hs
        self.data_hs['R_value'] = self.R6.currentText()
        self.data_hs['C_value'] = self.C4.currentText()
        # lp
        self.data_lp['C_value'] = self.C6.currentText()
        # gain
        self.data_gain['Ra_value'] = self.Ra.currentText()
        self.data_gain['Rb_value'] = self.Rb.currentText()

    def return_data(self):
        self.signal.emit(self.data_peak, self.peak_enable, self.data_ls, self.ls_enable, self.data_hs, self.hs_enable,
                         self.data_lp, self.lp_enable, self.data_gain)
        self.accept()


if __name__ == "__main__":
    data_peak = dict(C1_value='12n', C2_value='12n', C_value_double='27n', R1_value='20k', R2_value='20k',
                     R_half_value='10k', R_gain_value=2.2, R_high_cut='39k')
    data_ls = dict(C_value='12n', R_value='20k')
    data_hs = dict(C_value='12n', R_value='20k')
    data_lp = dict(C_value='12n')
    data_gain = dict(Ra_value='20k', Rb_value='20k')

    app = QtWidgets.QApplication(sys.argv)
    myWin = MyPeakFilterTuningAllDialog(data_peak, True, data_ls, True, data_hs, True, data_lp, True, data_gain)


    def set_data(data, bool0, data1, bool1, data2, bool2, data3, bool3, data4):
        print(data)
        print(data1)
        print(data2)
        print(data3)
        print(data4)


    myWin.signal.connect(set_data)

    myWin.show()
    sys.exit(app.exec_())
