# DOOM for GIMP
This is a GIMP port of DOOM using the prerelease 3.0 API.
## What?
One popular question is "*are you mentally insane?*". I don't quite know the answer to that question.  
## How?
I would not recommend anyone try to port DOOM to GIMP on their own. It hurt me.
## GIMP Setup
Pull down the submodules:
```bash
git submodule init
```
Install SPECIFICALLY `python3.10` on your system (no other version is compatible, as this compiles C code for each Python version), with `pip` and `setuptools`. Then, create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
Install `cython` and `numpy`:
```bash
pip install numpy cython
```
Then, run these following commands to setup and install the dependency CyDOOMGeneric:
```bash
cd cydoomgeneric/cydoomgeneric
python setup.py bdist_wheel
cd dist/
pip install *.whl
cd ../../../
```
Finally, install the GIMP plugin:
```bash
./install.sh
```
## Input Setup
Install `pynput`:
```bash
pip install pynput
```
When you start DOOM in GIMP, run `input-client.py`:
```bash
python input-client.py
```
