include il "model_cortex_m0plus.il"
include il "full_experiment/leakage_model_f3.il"
include asm "full_experiment/gadget.objdump"

annotate isw_gadget
    region mem w32 a[0:1]
    region mem w32 b[0:1]
    region mem w32 c[0:1]
    region mem w32 s[0:0]

    init r4 [a 0]
    init r5 [a 4]
    init r6 [b 0]
    init r7 [b 4]
    init r8 [c 0]
    init r9 [c 4]
    init sl [s 0]

    input public r0
    input public r1
    input public r2
    input public r3
    input public r4
    input public r5
    input public r6
    input public r7
    input public r8
    input public r9
    input public sl
    input public lastLoad
    input public A1
    input public B1
    input public A2
    input public B2
    input public A3
    input public B3
    input public b
    input public c
    input public s
    input sharing a;
---
addleakage:
  target: isw_gadget;
print:
  kind: macrodef
  target: isw_gadget
  verbosity: 1;
inlinecall:
  target: isw_gadget;
partialeval:
  target: isw_gadget;
print:
  kind: evaltrace
  target: isw_gadget
  verbosity: 1;
infertaint:
  inputsAsPublic: false
  outputsAsPublic: false
  memoryAsPublicOut: false
  target: isw_gadget;
check:
  kind: "Stateful SNI"
  target: isw_gadget;
...
