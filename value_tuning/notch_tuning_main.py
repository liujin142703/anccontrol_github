#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/2/26 15:35

import sys
from PyQt5 import QtCore, QtWidgets
from value_tuning.notch_tuning_UI import Ui_Dialog


class MyNotchFilterTuningDialog(QtWidgets.QDialog, Ui_Dialog):
    """接收notch参数及bool值，根据UI界面调整notch电路参数及bool值"""
    signal = QtCore.pyqtSignal(dict, bool)

    def __init__(self, argv, module):
        """
        滤波器阻容参数手动调节对话框
        :param argv: 下拉菜单参数
        :param module: 功能是否启用
        """
        super(MyNotchFilterTuningDialog, self).__init__()
        self.data = argv
        self.setupUi(self)
        self.set_items()
        self.set_initial_value(argv, module)
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
                   '390k', '430k', '470k', '510k', '560k', '620k', '680k', '750k', '820k', '910k', '1000k']
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
        self.C1.addItems(c_items)
        self.C2.addItems(c_items)
        self.C3.addItems(c_items)

    def set_initial_value(self, argv, module):
        """根据传入参数设置下拉菜单选择项，否则设置为默认值"""
        self.checkBox.setChecked(module)  # 设置启用键
        self.set_combobox_enabled()
        self.R1.setCurrentText(argv['R1_value'])
        self.R2.setCurrentText(argv['R2_value'])
        self.R3.setCurrentText(str(argv['R_gain_value']))
        self.R4.setCurrentText(argv['R_half_value'])
        self.C1.setCurrentText(argv['C1_value'])
        self.C2.setCurrentText(argv['C2_value'])
        self.C3.setCurrentText(argv['C_value_double'])
        self.set_data_value()

    def signal_slot(self):
        self.checkBox.toggled.connect(self.set_combobox_enabled)  # 启用功能键设置

        self.R1.currentIndexChanged.connect(self.set_data_value)  # data参数设置
        self.R2.currentIndexChanged.connect(self.set_data_value)
        self.R3.currentIndexChanged.connect(self.set_data_value)
        self.R4.currentIndexChanged.connect(self.set_data_value)
        self.C1.currentIndexChanged.connect(self.set_data_value)
        self.C2.currentIndexChanged.connect(self.set_data_value)
        self.C3.currentIndexChanged.connect(self.set_data_value)

        self.pushButton_OK.clicked.connect(self.return_data)
        self.pushButton_Cancel.clicked.connect(self.reject)

    def set_combobox_enabled(self):
        if self.checkBox.isChecked():
            self.R1.setEnabled(True)
            self.R2.setEnabled(True)
            self.R3.setEnabled(True)
            self.R4.setEnabled(True)
            self.C1.setEnabled(True)
            self.C2.setEnabled(True)
            self.C3.setEnabled(True)
        else:
            self.R1.setEnabled(False)
            self.R2.setEnabled(False)
            self.R3.setEnabled(False)
            self.R4.setEnabled(False)
            self.C1.setEnabled(False)
            self.C2.setEnabled(False)
            self.C3.setEnabled(False)

    def set_data_value(self, i=None):
        self.data['R1_value'] = self.R1.currentText()
        self.data['R2_value'] = self.R2.currentText()
        self.data['R_gain_value'] = self.R3.currentText()
        self.data['R_half_value'] = self.R4.currentText()
        self.data['C1_value'] = self.C1.currentText()
        self.data['C2_value'] = self.C2.currentText()
        self.data['C_value_double'] = self.C3.currentText()

    def return_data(self):
        if self.checkBox.isChecked():
            self.signal.emit(self.data, True)
            self.accept()
        else:
            self.signal.emit(self.data, False)
            self.accept()


if __name__ == "__main__":
    data = dict(C1_value='68n', C2_value='68n', C_value_double='150n', R1_value='2.2k',
                R2_value='2.2k', R_half_value='1.1k', R_gain_value=0)

    app = QtWidgets.QApplication(sys.argv)
    myWin = MyNotchFilterTuningDialog(data, True)


    def set_data(data, bool):
        if bool:
            data1 = data
        else:
            data1 = data


    myWin.signal.connect(set_data)

    myWin.show()
    sys.exit(app.exec_())
