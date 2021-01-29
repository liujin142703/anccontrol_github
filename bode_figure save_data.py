import math
import numpy as np
import matplotlib

matplotlib.use("Qt5Agg")  # 声明使用QT5
import matplotlib.pyplot as plt
import PySpice.Logging.Logging as Logging

logger = Logging.setup_logging()

from PySpice.Plot.BodeDiagram import bode_diagram
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

######ngspice输出格式保存及用matplotlib绘制伯德图###

inductance = 10 @ u_mH
capacitance = 1 @ u_uF
resonant_frequency = 1 / (2 * math.pi * math.sqrt(inductance * capacitance))  # LC电路谐振频率

figure = plt.figure(1, (20, 10))
plt.title('Bode Diagrams of RLC Filters')
axes = (plt.subplot(211), plt.subplot(212))

# 带通滤波器
circuit2 = Circuit('pass-band RLC Filter')
circuit2.SinusoidalVoltageSource('input', 'in', circuit2.gnd, amplitude=1 @ u_V)
circuit2.L(1, 'in', 2, inductance)
circuit2.C(1, 2, 'out', capacitance)
circuit2.R(1, 'out', circuit2.gnd, 25 @ u_Ω)

simulator2 = circuit2.simulator(temperature=25, nominal_temperature=25)
analysis2 = simulator2.ac(start_frequency=10 @ u_Hz, stop_frequency=20 @ u_kHz, number_of_points=100, variation='dec')

###系统推荐伯德图设置
# bode_diagram(axes=axes,
#               frequency=analysis2.frequency,
#              gain=20*np.log10(np.absolute(analysis2.out)),
#              phase=np.angle(analysis2.out,deg=False),
#              marker='.',
#              color='magenta',
#              linestyle='-')

###独立伯德图绘制及保存参数
gain = 20 * np.log10(np.absolute(analysis2.out))
x_frequency = np.logspace(1, np.log10(20000), num=gain.__len__())


###保存数据函数
def write_output_data(x, y):
    Lists = []
    x1 = x.tolist()
    y1 = y.tolist()
    for i in range(len(x1)):
        Lists.append(str(x1[i]) + ' ' + str(y1[i]) + '\n')
    return Lists


A_Lists = write_output_data(x_frequency, gain)
with open('text1.txt', 'w') as f:
    f.writelines(A_Lists)

axes[0].semilogx(x_frequency, gain, basex=10)
axes[0].grid(True)
axes[0].grid(True, which='minor')
axes[0].set_xlabel("Frequency [Hz]")
axes[0].set_ylabel("Gain [dB]")

plt.tight_layout()
plt.show()
