include il "model_cortex_m0plus.il"
include il "leakage_model_cortex_m0plus.il"
include asm "pipelineRegisterOverwrite/pip_reg_overwrite.objdump"

annotate pip_reg_overwrite_bench
    region mem w32 x[0:1]       // two 32-bit values in memory
    region mem w32 y[0:0]

    init r3 [x 0]               
    init r4 [x 4]

    input public r1
    input public r2
    input public r3
    input public r4

    input sharing x;             // x contains secret data

---
addleakage:
  target: pip_reg_overwrite_bench;

print:
  kind: macrodef
  target: pip_reg_overwrite_bench
  verbosity: 1;

inlinecall:
  target: pip_reg_overwrite_bench;

partialeval:
  target: pip_reg_overwrite_bench;

print:
  kind: evaltrace
  target: pip_reg_overwrite_bench
  verbosity: 1;

infertaint:
  inputsAsPublic: true
  outputsAsPublic: false
  memoryAsPublicOut: false
  target: pip_reg_overwrite_bench;

check:
  kind: "Stateful SNI"
  target: pip_reg_overwrite_bench;
...
