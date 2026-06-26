# 𓆣 SCARAB 𓆣
## Side-Channel Automated Reporting of micro-Architectural Behaviour

This repository presents a tool meant to streamline the process of capturing and analysing side-channel traces to obtain an `scVerif` leakage model. It can be run both from CLI and through a GUI created with Streamlit. It works by running benchmarks representing different micro-architectural leakage effects on a micro-processor, then analysing the traces to decide if they are actually present on the device under test. The output is a JSON file containing information about all the benchmarks and the verdicts. This can also be converted into an `scVerif` leakage model, to be used for eliminating side-channel leakage on code running on the target device. 

## Usage 

### Running using the GUI

- Change directory to the `/chipwhisperer/scripts/frontend` directory
- Make sure to activate a python environment
- Run `streamlit run app.py` and go to the url that appears in the terminal
- Go through the instructions on screen to capture and analyse traces

### Running using the CLI

- Change directory to the `/chipwhisperer/scripts` directory
- Make sure to activate a python environment
- Run `python3 cli.py`
- Go through the instructions to use the tool
- To create a leakage model from a JSON report, run `leakage_model.py`


## Implemented Effects
### 1. Memory Remnant Effect
triggered by load-load sequences

### 2. Register Overwrite Effect
triggered by loading into the same register

### 3. Pipeline Register Overwrite Effect
triggered by xor-xor; 8 variants, targeting different combinations of vulnerable operand position

## Layout

- `/chipWhisperer` - firmware and software necessary for running benchmarks on ChipWhisperer target boards, capturing power traces, and analysing them
    - `/chipWhisperer/firmware` - folder with the firmware; Each subfolder keeps the firmware implementing the specified effect, as well as the .c source code and the Makefile. NOTE: to actually compile the firmware, more files from the chipwhisperer repository are needed. There are also files with generic firmware for testing purposes
    - `/chipwhisperer/scripts` - folder with all the logic of the program
        - `../../frontend` - folder with all the Streamlit files. `app.py` is the main file, which runs the application
        - `../../cli.py` - main file for the terminal interface of the app
        - `../../capture.py` - responsible for the capture part of the process
        - `../../analysis.py` - responsible for the analysis and JSON report creation 
        - `../../leakage_model.py` - responsible for creating a leakage model out of a JSON report
        - `../../others` - various helper files

- `scVerifModels` - all the files necessary for modelling the leakage effects using scVerif; Each subfolder represents an effect, and th files have the following structur
    - `eval_[effect].il` - The evaluation file, describing where things are in memory, the register structure, and also what to evaluate
    - `leakage_model_[effect].il` - Leakage model targeting the singular effect
    - `[effect].objdump` - Simple assembly code implementing the effect
    - `mitigated_[effect].objdump` - The same assembly code implementing the effect, but with instructions added for mitigating it

- `/data` - where traces and shares `.npy` files go after capture; Structured based on the effect and the chip

- `/plots` - where plots of specific traces go; Also structured based on the effect and the chip
