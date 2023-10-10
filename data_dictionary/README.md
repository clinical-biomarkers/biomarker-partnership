# Data Dictionary

The data dictionary is used to aid in the integration of BiomarkerKB data from many disparate sources. The data dictionary sets the format and standard for all data incororated into the Biomarker Knowledge Base.

## Starting up the Virtual Environment

You can run the project locally or through a virtual environment. A virtual environment is recommended to avoid potential dependency and/or versioning issues. 

If your virtual environment has not been created yet, you can run the following command from the project's root directory:

```bash
virtualenv env 
```

To activate the virtual environment on Windows:

```bash 
env/Scripts/activate
```

To start the virtual environemnt on MacOS/Linus:

```bash
source env/bin/activate
```

Then install the project dependencies using:

```bash
pip install -r requirements.txt
```

## Generating a Schema

If applicable, in the project root directory, update the `conf.json` file with the updated version number. 

Make sure the corresponding schema directories exist prior to running `process_dictionary.py`. 

While inside the project root directory:

```bash
mkdir schema/<VERSION>
```

The `process_dictionary.py` can take these arguments:

```
Positional arguments:
    file_path           filepath of the data dictionary TSV to convert

Optional arguments 
    -h --help           show the help message and exit
    -v --version        show current version number and exit
```

Move your current working directory to this directory and run the `process_dictonary.py` script passing in the filepath to the data dictionary TSV you want to process. 

```bash
cd data_dictionary
python process_dictionary.py <FILEPATH/TO/DICTIONARY>
```