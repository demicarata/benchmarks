import chipwhisperer as cw
import time
import matplotlib.pyplot as plt
from numpy import trace

FIRMWARE_PATH = "chipWhisperer/firmware/simpleserial-aes-CW308_STM32F3.hex"

def connect_cw(target_type=cw.targets.SimpleSerial2):
    print("Connecting to ChipWhisperer...")
    scope = cw.scope(scope_type=cw.scopes.OpenADC)

    scope.default_setup()
    scope.io.hs2 = "clkgen"  
    scope.clock.adc_src = "clkgen_x1"
    scope.adc.trigger_src = "tio4"
    time.sleep(0.1)

    print("Clock freq:", scope.clock.clkgen_freq)

    target = cw.target(scope, cw.targets.SimpleSerial2)

    return scope, target

def program_target(scope, target):
    print("Configuring ChipWhisperer...")
    cw.program_target(scope, cw.programmers.STM32FProgrammer, FIRMWARE_PATH)

    time.sleep(1)
    reset_target(scope, target)
    time.sleep(1)

def setup_target(target):
    print("Setting up target communication...")

    target.baud = 38400
    time.sleep(0.1)
    target.flush()

def test_serial(target):
    print("Testing Serial communication...")

    msg = bytearray([0]*16)

    target.simpleserial_write('i', msg)
    response = target.simpleserial_read('j', 16)
    print("Response:", response)

    return response is not None

def perform_capture(scope, target):
    print("Performing capture...")

    msg = bytearray([0]*16)

    scope.arm()
    target.simpleserial_write('i', msg)
    ret = scope.capture()

    if ret:
        print("Capture failed (no trigger seen)")
        return None

    print("Capture success")

    trace = scope.get_last_trace()
    print("Trace length:", len(trace))

    return trace

def reset_target(scope, target):
    scope.io.nrst = 'low'
    time.sleep(0.5)
    scope.io.nrst = 'high_z'
    time.sleep(0.5)
    
    target.flush()

def disconnect_cw():
    print ("Disconnecting from ChipWhisperer...")
    scope.dis()
    target.dis()

if __name__ == '__main__':
    scope, target = connect_cw()
    
    program_target(scope, target)
    setup_target(target)
    reset_target(scope, target)
    time.sleep(2)
    target.flush()
    time.sleep(0.5)
    print(target.read())
    time.sleep(1)
    
    print("Scope clock:", scope.clock.clkgen_freq)
    print("Target baud:", target.baud)
    print("tio1:", scope.io.tio1)
    print("tio2:", scope.io.tio2)
    print("hs2:", scope.io.hs2)
    print("Target power:", scope.io.target_pwr)
    print("nrst:", scope.io.nrst)


    # --- SERIAL TEST ---
    if not test_serial(target):
        print("Serial communication test failed. Exiting.")
        disconnect_cw()
        exit(1)

    # --- CAPTURE TEST ---
    trace = perform_capture(scope, target)

    if trace is not None:
        plt.plot(trace[:1000])
        plt.title("Capture Test (first 1000 samples)")
        plt.show()

    print("=== DONE ===")

    disconnect_cw()
