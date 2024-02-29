# Schema

Using the JSON schema, data can be validated to ensure it conforms to the latest version of the data model.

## Validating a Data File Against a Schema

If applicable, in the project root directory, update the `conf.json` file with the updated version number. 

In the `schema/` directory, the `validate_data.py` script can take multiple input arguments: 

```
Positional arguments:
    data_filepath       filepath of the input data file to validate, accepts JSON
    schema_filepath     filepath to the schema file to validate against

Optional arguments:
    -h --help           show the help message and exit
    -v --version        show current version number and exit
```

Note: The script expects the `home/logs/` directory to exist. This is where the output logs will be dumped. 

Validating a data file against the schema:

```bash
python validate_schema.py <FILEPATH/TO/SOURCE/DATA> <FILEPATH/TO/SCHEMA>
```
