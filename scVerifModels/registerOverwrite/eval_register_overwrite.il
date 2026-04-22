include il "model_cortex_m0plus.il"
include il "registerOverwrite/leakage_model_regOver.il"
include asm "registerOverwrite/reg_overwrite.objdump"

annotate reg_overwrite_bench
    region mem w32 x[0:1]       // two 32-bit values in memory
    region mem w32 y[0:0]

    init r3 [x 0]               
    init r4 [x 4]
    init r6 [y 0]

    input public r0
    input public r1
    input public r2
    input public r3
    input public r4
    input public r5
    input public r6

    input public y
    input sharing x;             // x contains secret data

---
addleakage:
  target: reg_overwrite_bench;

print:
  kind: macrodef
  target: reg_overwrite_bench
  verbosity: 1;

inlinecall:
  target: reg_overwrite_bench;

partialeval:
  target: reg_overwrite_bench;

print:
  kind: evaltrace
  target: reg_overwrite_bench
  verbosity: 1;

infertaint:
  inputsAsPublic: true
  outputsAsPublic: false
  memoryAsPublicOut: false
  target: reg_overwrite_bench;

check:
  kind: "Stateful SNI"
  target: reg_overwrite_bench;
...
