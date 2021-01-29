# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'register_rw_ui.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(395, 138)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setEnabled(True)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.le_write_value = QtWidgets.QLineEdit(self.groupBox)
        self.le_write_value.setObjectName("le_write_value")
        self.gridLayout.addWidget(self.le_write_value, 1, 2, 1, 1)
        self.le_write_addr = QtWidgets.QLineEdit(self.groupBox)
        self.le_write_addr.setObjectName("le_write_addr")
        self.gridLayout.addWidget(self.le_write_addr, 1, 1, 1, 1)
        self.le_read_addr = QtWidgets.QLineEdit(self.groupBox)
        self.le_read_addr.setObjectName("le_read_addr")
        self.gridLayout.addWidget(self.le_read_addr, 2, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 1)
        self.label_read_value = QtWidgets.QLabel(self.groupBox)
        self.label_read_value.setObjectName("label_read_value")
        self.gridLayout.addWidget(self.label_read_value, 2, 2, 1, 1)
        self.btn_read = QtWidgets.QPushButton(self.groupBox)
        self.btn_read.setObjectName("btn_read")
        self.gridLayout.addWidget(self.btn_read, 2, 0, 1, 1)
        self.btn_write = QtWidgets.QPushButton(self.groupBox)
        self.btn_write.setObjectName("btn_write")
        self.gridLayout.addWidget(self.btn_write, 1, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setMinimumSize(QtCore.QSize(0, 12))
        self.label_3.setMaximumSize(QtCore.QSize(16777215, 12))
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 0, 2, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.label_connect_state = QtWidgets.QLabel(Dialog)
        self.label_connect_state.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_connect_state.setObjectName("label_connect_state")
        self.verticalLayout.addWidget(self.label_connect_state)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.groupBox.setTitle(_translate("Dialog", "寄存器操作"))
        self.le_write_value.setText(_translate("Dialog", "0x09"))
        self.le_write_addr.setText(_translate("Dialog", "0x01"))
        self.le_read_addr.setText(_translate("Dialog", "0x01"))
        self.label_2.setText(_translate("Dialog", "addr(hex)"))
        self.label_read_value.setText(_translate("Dialog", "值："))
        self.btn_read.setText(_translate("Dialog", "read"))
        self.btn_write.setText(_translate("Dialog", "write"))
        self.label_3.setText(_translate("Dialog", "value(hex)"))
        self.label_connect_state.setText(_translate("Dialog", "控制状态：无USB连接"))

