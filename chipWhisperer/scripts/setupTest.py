import numpy as np
import chipwhisperer as cw
import scipy.stats
import matplotlib.pyplot as plt

if __name__ == '__main__':
    r = np.arange(0,100)
    print("NumPy works!")
    r = r + scipy.stats.norm.rvs(size=100)
    print("scipy.stats works!")

    plt.plot(r[::-1] + scipy.stats.norm.rvs(size=100))
    plt.show()
    print("Plotting works!")
    try:
        if not scope.connectStatus:
            scope.con()
    except NameError:
        scope = cw.scope()

    try:
        if SS_VER == "SS_VER_2_1":
            target_type = cw.targets.SimpleSerial2
        elif SS_VER == "SS_VER_2_0":
            raise OSError("SS_VER_2_0 is deprecated. Use SS_VER_2_1")
        else:
            target_type = cw.targets.SimpleSerial
    except:
        SS_VER="SS_VER_1_1" 
        target_type = cw.targets.SimpleSerial

    try:
        target = cw.target(scope, target_type)
    except:
        print("INFO: Caught exception on reconnecting to target - attempting to reconnect to scope first.")
        print("INFO: This is a work-around when USB has died without Python knowing. Ignore errors above this line.")
        scope = cw.scope()
        target = cw.target(scope, target_type)


    print("Connecting to ChipWhisperer works!")