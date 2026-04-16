include il "model_cortex_m0plus.il"
include il "leakage_model_cortex_m0plus.il"
include asm "basicTest/test.objdump"

annotate test_bench
    region mem w32 x[0:1]       // two 32-bit values in memory
    init r0 [x 0]               // r0 = pointer to x0
    init r1 [x 4]               // r1 = pointer to x1
    input sharing x;             // x contains secret data

---
addleakage:
  target: test_bench;

print:
  kind: macrodef
  target: test_bench
  verbosity: 1;

inlinecall:
  target: test_bench;

partialeval:
  target: test_bench;

print:
  kind: evaltrace
  target: test_bench
  verbosity: 1;

infertaint:
  inputsAsPublic: true
  outputsAsPublic: false
  memoryAsPublicOut: false
  target: test_bench;

check:
  kind: "Stateful SNI"
  target: test_bench;
...
