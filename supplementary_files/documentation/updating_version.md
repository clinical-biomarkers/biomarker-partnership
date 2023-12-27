# Version Update Workflow/Checklist (Internal)

This is an internal documentation page for the steps that need to be taken when releasing a version update to the data model. 

- [Update Version Number](#update-version-number)
- [Update Sample/Reference Files](#update-samplereference-files)
- [Update Data Dictionary](#update-data-dictionary)
- [Update Schema](#update-schema)
- [Update Data Scripts](#update-data-scripts)
- [Testing](#testing)
- [Update Documentation](#update-documentation)

## Update Version Number

- Update the version number in the `conf.json` file located in the project root directory. 
- Create the new directories for the version in the `data_dictionary/` and `schema/` sub directories. 
    - Within the `data_dictionary/` sub directory for the new version, create the `release_notes.txt` and `README.md` files to log the new data dictionary changes from the previous version. 
- Create the version directory in the path `supplementary_files/sample_data_model_structures/`. 

## Update Sample/Reference Files

Within the new version directory in the `supplementary_files/sample_data_model_structures/` path, create the new sample/reference files. At minimum, there should be two reference files: 

- `sample_biomarker.json`: This is a simple entry of a sample biomarker conforming to the respective version schema. This is useful for seeing a basic example of how a biomarker entry is formatted for this data version. 
- `sample_structure.json`: This is an outline of the version data model with empty values. This is useful for quickly referencing to determine the data model structure. This file can also be used by the `skeleton_dictionary.py` script when updating the data dictionary. 

## Update Data Dictionary 

The data dictionary from the previous version can be updated directly or a sample file can be used to generate a new data dictionary with the `skeleton_dictionary.py` script. 

If updating the data dictionary directly, make sure the correct formatting is followed. Either refer to previous data dictionaries or the [data dictionary documentation](../../data_dictionary/README.md). 

If using the `skeleton_dictionary.py` script, you can pass in the file path to the newly updated `sample_structure.json` file and a skeleton dictionary will be generated in the correct data dictionary format. Once generated, you will have to fill in each field's metadata. 

## Update Schema 

Once the updated data dictionary has been finalized, you can follow the [generating a schema documentation](https://github.com/biomarker-ontology/biomarker-partnership/blob/updated_documentation/data_dictionary/README.md#generating-a-schema) to generate the new JSON schema. 

## Update Data Scripts 

The scripts in the `src/` directory will have to be updated in order to generate, wrangle, and transform the data in accordance with the new data dictionary and schema version. 

## Testing 

After the data scripts have been updated, create new testing files in the file path `supplemtary_files/tests/`. 

## Update Documentation 

If applicable, update any documentation needed. 