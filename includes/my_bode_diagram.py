#!/usr/bin/env python 
# -*- coding:utf-8 -*-
# @Time    : 2019-1-17 21:28
# @Author  : liujin_person
####################################################################################################
# ##根据pyspice BodeDiagram.py类调整phase数值范围，
# ##默认位置C:\Users\my love\AppData\Local\Programs\Python\Python37\Lib\site-packages\PySpice-1.2.0-py3.7.egg\PySpice\Plot
# ##由pi调整为180°
import matplotlib.pyplot as plt


####################################################################################################

def bode_diagram_gain(axe, frequency, gain, **kwargs):
    axe.semilogx(frequency, gain, basex=10, **kwargs)
    axe.grid(True)
    axe.grid(True, which='minor')
    axe.set_xlabel("Frequency [Hz]")
    axe.set_ylabel("Gain [dB]")


####################################################################################################

def bode_diagram_phase(axe, frequency, phase, **kwargs):
    axe.semilogx(frequency, phase, basex=10, **kwargs)
    axe.set_ylim(-200, 200)
    axe.grid(True)
    axe.grid(True, which='minor')
    axe.set_xlabel("Frequency [Hz]")
    axe.set_ylabel("Phase [deg]")
    # plt.yticks((-180, -90, 0, 90, 180),
    #            (r"-180", r"-90", "0", r"90", r"180"))


####################################################################################################

def bode_diagram(axes, frequency, gain, phase, **kwargs):
    bode_diagram_gain(axes[0], frequency, gain, **kwargs)
    bode_diagram_phase(axes[1], frequency, phase, **kwargs)
