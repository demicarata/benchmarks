include il "model_cortex_m0plus.il"
include il "memoryRemnant/leakage_model_memRem.il"
include asm "memoryRemnant/mitigated_memRemnant.objdump"

annotate mem_remnant_bench
    region mem w32 x[0:1]     // x = sensitive value input
    region mem w32 y[0:0]


    init r3 [x 0]               // r3 = pointer to x
    init r4 [x 4]                // r4 = pointer to y
    init r0 [y 0]                // r0 = pointer to whatever - for use in the mitigated version

    // these are used for testing with the big leakage model
    // input public opA  
    // input public opB
    // input public opR
    // input public opW
    input public r0
    input public r1
    input public r2
    input public r3
    input public r4
    input public r5
    input public lastLoad
    input public y
    input sharing x;

---
addleakage:
  target: mem_remnant_bench;

print:
  kind: macrodef
  target: mem_remnant_bench
  verbosity: 1;

inlinecall:
  target: mem_remnant_bench;

partialeval:
  target: mem_remnant_bench;

print:
  kind: evaltrace
  target: mem_remnant_bench
  verbosity: 1;

infertaint:
  inputsAsPublic: false
  outputsAsPublic: false
  memoryAsPublicOut: false
  target: mem_remnant_bench;

check:
  kind: "Stateful SNI"
  target: mem_remnant_bench;
...
