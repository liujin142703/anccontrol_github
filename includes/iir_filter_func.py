#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:dell
# datetime:2019/5/6 11:37
import numpy as np
from scipy import signal as sg
import matplotlib.pyplot as plt


def low_pass_filter_iir(f0, Q=1., fs=192000):
    """
    根据PEQ参数设计二阶IIR数字低通滤波器，默认采样率192k
    :param f0: 中心频率
    :param Q: 峰值带宽
    :param fs: 系统采样率
    :return: 双二阶滤波器系数
    """
    w0 = 2 * np.pi * f0 / fs
    alpha = np.sin(w0) / (2 * Q)

    b0 = (1 - np.cos(w0)) / 2
    b1 = 1 - np.cos(w0)
    b2 = (1 - np.cos(w0)) / 2
    a0 = 1 + alpha
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha
    b = np.array([b0, b1, b2])
    a = np.array([a0, a1, a2])
    h = np.hstack((b / a[0], a / a[0]))

    return h


def high_pass_filter_iir(f0, Q=1., fs=192000):
    """
    根据PEQ参数设计二阶IIR数字高通滤波器，默认采样率192k
    :param f0: 中心频率
    :param Q: 峰值带宽
    :param fs: 系统采样率
    :return: 双二阶滤波器系数
    """
    w0 = 2 * np.pi * f0 / fs
    alpha = np.sin(w0) / (2 * Q)

    b0 = (1 + np.cos(w0)) / 2
    b1 = -1 - np.cos(w0)
    b2 = (1 + np.cos(w0)) / 2
    a0 = 1 + alpha
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha
    b = np.array([b0, b1, b2])
    a = np.array([a0, a1, a2])

    h = np.hstack((b / a[0], a / a[0]))

    return h


def peak_filter_iir(f0, gain=0., Q=1., fs=192000):
    """
    根据PEQ参数设计二阶IIR数字peak滤波器，默认采样率192k
    :param f0: 中心频率
    :param gain: 峰值增益
    :param Q: 峰值带宽
    :param fs: 系统采样率
    :return: 双二阶滤波器系数
    """
    A = np.sqrt(10 ** (gain / 20))
    w0 = 2 * np.pi * f0 / fs
    alpha = np.sin(w0) / (2 * Q)

    b0 = 1 + alpha * A
    b1 = -2 * np.cos(w0)
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha / A
    b = np.array([b0, b1, b2])
    a = np.array([a0, a1, a2])

    h = np.hstack((b / a[0], a / a[0]))

    return h


def low_shelf_filter_iir(f0, gain=0., Q=1., fs=192000):
    """
    根据PEQ参数设计二阶IIR数字low shelf滤波器，默认采样率192k
    :param f0: 中心频率
    :param gain: 峰值增益
    :param Q: 峰值带宽
    :param fs: 系统采样率
    :return: 双二阶滤波器系数
    """
    A = np.sqrt(10 ** (gain / 20))
    w0 = 2 * np.pi * f0 / fs
    alpha = np.sin(w0) / (2 * Q)

    b0 = A * ((A + 1) - (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha)
    b1 = 2 * A * ((A - 1) - (A + 1) * np.cos(w0))
    b2 = A * ((A + 1) - (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha)
    a0 = (A + 1) + (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha
    a1 = -2 * ((A - 1) + (A + 1) * np.cos(w0))
    a2 = (A + 1) + (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha

    b = np.array([b0, b1, b2])
    a = np.array([a0, a1, a2])

    h = np.hstack((b / a[0], a / a[0]))

    return h


def high_shelf_filter_iir(f0, gain=0., Q=1., fs=192000):
    """
    根据PEQ参数设计二阶IIR数字high shelf滤波器，默认采样率192k
    :param f0: 中心频率
    :param gain: 峰值增益
    :param Q: 峰值带宽
    :param fs: 系统采样率
    :return: 双二阶滤波器系数
    """
    A = np.sqrt(10 ** (gain / 20))
    w0 = 2 * np.pi * f0 / fs
    alpha = np.sin(w0) / (2 * Q)

    b0 = A * ((A + 1) + (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha)
    b1 = -2 * A * ((A - 1) + (A + 1) * np.cos(w0))
    b2 = A * ((A + 1) + (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha)
    a0 = (A + 1) - (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha
    a1 = 2 * ((A - 1) - (A + 1) * np.cos(w0))
    a2 = (A + 1) - (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha

    b = np.array([b0, b1, b2])
    a = np.array([a0, a1, a2])

    h = np.hstack((b / a[0], a / a[0]))

    return h


if __name__ == '__main__':
    f0 = 500
    Q = 1 / np.sqrt(2)
    fs = 4000
    gain = 10
    sos = low_pass_filter_iir(f0=f0, Q=Q, fs=fs)
    print(sos)
    w, h = sg.sosfreqz(sos, worN=4096, fs=fs)
    sos_book = [0.09763107, 0.19526215, 0.09763107, 1., -0.94280904, 0.33333333]
    print(sos_book)
    w1, h1 = sg.sosfreqz(sos_book, worN=4096, fs=fs)

    fig, ax1 = plt.subplots()
    ax1.semilogx(w, 20 * np.log10(abs(h)), 'b')
    ax1.semilogx(w1, 20 * np.log10(abs(h1)), 'y')
    ax1.set_ylabel('Amplitude [dB]', color='b')
    ax1.set_xlabel('Frequency')
    ax1.grid()
    ax2 = ax1.twinx()
    ax2.semilogx(w, np.angle(h, deg=True), 'r')
    ax2.semilogx(w1, np.angle(h1, deg=True), 'r')
    ax2.set_ylabel('Angle [deg]', color='r')
    ax2.axis('tight')
    plt.show()
