# DyRes
A simple tool for loading Dymola result files in Python. Uses OOP concepts similar to modelica, to make simulation postprocessing easier.

## Description - What can it do?
- Load Dymola results files into python (like modelicares.Simres)
- Store result files in different forms (.mat, .JSON, .h5)
- Extend to make custom result objects to fit you needs

## Installation
prerequisites:
- numpy
- scipy
- pandas
- python 3.11+
- h5py (`conda install h5py`)

In your environment use `pip install git+https://github.com/DLR-TT-ESI-EHT/DyRes.git` and you're good to go.
To update, just run the command above 

## Usage
Look at the notebooks for examples #TODO

## Support
Please make an issue and describe your problem or suggestion. We will try to accomodate where we can.

## Roadmap
Currently nothing new planned apart from general maintenance

## Contributing
- First make issues
- You can test your suggestions on an editable installation 
    - First pull the repo and activate your environment in the repo
    - `pip install -e .` (making sure you're in the folder)
    - Make your branch and then make your changes, push and make a merge request pointing to the issue you want to fix

## Project status
Ongoing. Suggestions for improvement welcome
