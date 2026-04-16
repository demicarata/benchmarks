import chipwhisperer as cw
import time
import matplotlib.pyplot as plt
from numpy import trace

FIRMWARE_PATH = "chipWhisperer/firmware/simpleserial-base-CW308_STM32F3.hex"

def connect_cw(target_type=cw.targets.SimpleSerial2):
    print("Connecting to ChipWhisperer...")
    scope = cw.scope()

    scope.default_setup()
    scope.io.tio1 = "serial_rx"
    scope.io.tio2 = "serial_tx"
    scope.io.tio4 = "high_z"  
    scope.trigger.triggers = "tio4"

    scope.io.target_pwr = True

    target = cw.target(scope, cw.targets.SimpleSerial)

    return scope, target



def program_target(scope):
    print("Configuring ChipWhisperer...")

    # Enter bootloader mode
    # scope.io.pdic = True
    # reset_target(scope)

    cw.program_target(scope, cw.programmers.STM32FProgrammer, FIRMWARE_PATH, baud=38400)

    time.sleep(1)

    # # Return to normal mode
    # scope.io.pdic = False
    reset_target(scope)

def setup_target(target):
    print("Setting up target communication...")
    target.baud = 115200
    time.sleep(0.1)
    target.flush()

def test_serial(target):
    print("Testing Serial communication with target...")
    cmd = 'p'
    try:
        target.simpleserial_write(cmd, b"")
        resp = target.simpleserial_read(cmd, 4, timeout=1)
        print("Target response:", resp)
        return resp is not None
    except Exception as e:
        print("Serial test failed:", e)
        return False
    
def perform_capture(scope, target):
    print("Performing capture...") 
    cmd = 'p' 
    scope.arm()
    target.simpleserial_write(cmd, b"") 

    ret = scope.capture() 

    if ret: 
        print("Capture failed (no trigger seen)") 
        return None 
    else: 
        print("Capture success") 

    trace = scope.get_last_trace() 
    print("Trace length:", len(trace)) 

    return trace

def reset_target(scope):
    scope.io.nrst = 'low'
    time.sleep(0.05)
    scope.io.nrst = 'high_z'
    time.sleep(0.05)

def disconnect_cw():
    print ("Disconnecting from ChipWhisperer...")
    scope.dis()
    target.dis()

if __name__ == '__main__':
    scope, target = connect_cw()
    
    program_target(scope)

    setup_target(target)

    # --- DEBUG: raw read ---
    print("Raw read (debug):", target.read()) 
    
    # --- SERIAL TEST ---
    if not test_serial(target):
        print("Serial communication test failed. Exiting.")
        disconnect_cw()
        exit(1)

    # --- CAPTURE ---
    trace = perform_capture(scope, target)

    if trace is not None:
        plt.plot(trace[:1000])
        plt.title("ChipWhisperer Capture Test Trace (first 1000 samples)")
        plt.show()

    print("=== DONE ===")

    disconnect_cw()
