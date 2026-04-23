import chipwhisperer as cw
import numpy as np
import time

scope = cw.scope()
scope.default_setup()
target = cw.target(scope, cw.targets.SimpleSerial2)

cw.program_target(scope, cw.programmers.STM32FProgrammer, "chipWhisperer/firmware/memory_remnant/memory-remnant-asm-bench-CW308_STM32F3.hex")

time.sleep(0.1)
target.flush()

print(scope.trigger.triggers)  # should be "tio4"
print(scope.io.tio4)           # should be "high_z" - tio4 is the trigger input from target
print(scope.io.tio1)  # should be "serial_rx"
print(scope.io.tio2)  # should be "serial_tx"

scope.adc.samples = 100  # at 100 traces 

N = 10000  # number of traces
traces = []
shares = []

rng = np.random.default_rng()

for _ in range(N):
    secret = rng.integers(0, 2**32, dtype=np.uint32)
    x0     = rng.integers(0, 2**32, dtype=np.uint32)
    x1     = np.uint32(secret ^ x0)
    payload = bytearray(x0.tobytes() + x1.tobytes())

    scope.arm()
    time.sleep(0.01)

    target.send_cmd(0x01, 0x00, payload)
    ret = target.simpleserial_wait_ack(timeout=500)

    timeout = scope.capture() 
    if timeout:
        print("Scope timed out - trigger did not fire")
        continue

    trace = scope.get_last_trace()
    traces.append(trace)
    shares.append((int(x0), int(x1), int(secret)))

traces = np.array(traces)
shares = np.array(shares)  # columns: x0, x1, secret

np.save("traces.npy", traces)
np.save("shares.npy", shares)
print(f"Captured {len(traces)} traces")