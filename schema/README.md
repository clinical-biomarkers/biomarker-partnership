# Schema

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

## Validating a Data File Against a Schema

If applicable, in the project root directory, update the `conf.json` file with the updated version number. 

In the `schema/` directory, the `validate_data.py` script can take multiple input arguments: 

```
Positional arguments:
    data_filepath       filepath of the input data file to validate, accepts TSV or CSV
    schema_filepath     filepath to the schema file to validate against

Optional arguments:
    -o --output         whether to save the intermediate json (store_true argument)
    -c --chunk          chunk size to process the source data
    -h --help           show the help message and exit
    -v --version        show current version number and exit
```

The `-o` flag is a `store_true` argument, meaning just the presence of the flag will set the value to `True`. By omitting it, it will default to `False`. If set to `True`, by default the intermediate json will be saved in the `home/intermediate_data/<VERSION>/` directory (as specified in `conf.json`). If the `output` argument is passed, make sure this directory exists. 

If processing a potentially very large source data file, the `-c` flag can be set to process the source data file in chunks. This can help prevent running out of system memory. 

The script also expects the `home/logs/` directory to exist. This is where the output logs will be dumped. 

Validating a file schema (without saving the intermediate JSON or processing in chunks):

```bash
python validate_schema.py <FILEPATH/TO/SOURCE/DATA> <FILEPATH/TO/SCHEMA>
```