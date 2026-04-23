# Side-Channel Leakage Benchmarks

This repository holds a set of benchmarks targeting different microarchitectural leakage effects. It includes `scVerif` models for analysing the effects, as well as `ChipWhisperer` firmware for running the benchmarks on target processors. Python scripts for analysing the benchmark captures are also provided.

## Implemented Effects
### 1. Memory Remnant Effect
triggered by load-load sequences

### 2. Register Overwrite Effect
triggered by loading into the same register

### 3. Pipeline Register Overwrite Effect
triggered by xor-xor

TODO: Explain each effect

## Layout

- `/chipWhisperer` - firmware and software necessary for running benchmarks on ChipWhisperer target boards, capturing power traces, and analysing them
    - `/chipWhisperer/firmware` - folder with the firmware; Each subfolder keeps the firmware implementing the specified effect, as well as the .c source code and the Makefile. NOTE: to actually compile the firmware, more files from the chipwhisperer repository are needed. There are also files with generic firmware for testing purposes
    - `/chipwhisperer/anything_else` - TODO: structure this better

- `scVerifModels` - all the files necessary for modelling the leakage effects using scVerif; Each subfolder represents an effect:
    - `eval_[effect].il` - The evaluation file, describing where things are in memory, the register structure, and also what to evaluate
    - `leakage_model_[effect].il` - Leakage model targeting the singular effect
    - `[effect].objdump` - Simple assembly code implementing the effect
    - `mitigated_[effect].objdump` - The same assembly code implementing the effect, but with instructions added for mitigating it

- `/other_stuff` - TODO: put graphs in a better place

## Usage
TODO