# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'two_order_lowpass_tuning_UI.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(957, 532)
        self.layoutWidget = QtWidgets.QWidget(Dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(785, 250, 166, 281))
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.checkBox = QtWidgets.QCheckBox(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.checkBox.setFont(font)
        self.checkBox.setObjectName("checkBox")
        self.verticalLayout_2.addWidget(self.checkBox)
        self.pushButton_OK = QtWidgets.QPushButton(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.pushButton_OK.setFont(font)
        self.pushButton_OK.setObjectName("pushButton_OK")
        self.verticalLayout_2.addWidget(self.pushButton_OK)
        self.pushButton_Cancel = QtWidgets.QPushButton(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.pushButton_Cancel.setFont(font)
        self.pushButton_Cancel.setObjectName("pushButton_Cancel")
        self.verticalLayout_2.addWidget(self.pushButton_Cancel)
        self.C1 = QtWidgets.QComboBox(Dialog)
        self.C1.setEnabled(False)
        self.C1.setGeometry(QtCore.QRect(510, 180, 58, 24))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.C1.setFont(font)
        self.C1.setObjectName("C1")
        self.C2 = QtWidgets.QComboBox(Dialog)
        self.C2.setEnabled(False)
        self.C2.setGeometry(QtCore.QRect(275, 380, 58, 24))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.C2.setFont(font)
        self.C2.setObjectName("C2")
        self.R1 = QtWidgets.QComboBox(Dialog)
        self.R1.setEnabled(False)
        self.R1.setGeometry(QtCore.QRect(80, 235, 58, 24))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.R1.setFont(font)
        self.R1.setObjectName("R1")
        self.R3 = QtWidgets.QComboBox(Dialog)
        self.R3.setEnabled(False)
        self.R3.setGeometry(QtCore.QRect(315, 235, 58, 24))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.R3.setFont(font)
        self.R3.setObjectName("R3")
        self.R2 = QtWidgets.QComboBox(Dialog)
        self.R2.setEnabled(False)
        self.R2.setGeometry(QtCore.QRect(315, 55, 58, 24))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.R2.setFont(font)
        self.R2.setObjectName("R2")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(0, -5, 781, 541))
        self.label.setMaximumSize(QtCore.QSize(800, 680))
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap(":/notch/two_order_lowpass.png"))
        self.label.setObjectName("label")
        self.label.raise_()
        self.layoutWidget.raise_()
        self.C1.raise_()
        self.C2.raise_()
        self.R1.raise_()
        self.R3.raise_()
        self.R2.raise_()

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.checkBox.setText(_translate("Dialog", "启用"))
        self.pushButton_OK.setText(_translate("Dialog", "OK"))
        self.pushButton_Cancel.setText(_translate("Dialog", "取消"))


import value_tuning.notch_icon_rc
