# Biomarker Partnership  

The goal of this project is to develop a community-based biomarker-centric data model to harvest and organize biomarker knowledge for diverse biological data types. 

- [Intro](#intro)
    - [Background](#background)
    - [Scope and Goal of the Project](#scope-and-goal-of-the-project)
    - [Initial Biomarker Database Curation](#initial-biomarker-database-curation)
- [Biomarker Defition](#biomarker-definition)
- [Usage](#usage)
    - [Workflow](#workflow)
    - [General Notes](#general-notes)
    - [Start Environment](#starting-up-the-virtual-environment)
    - [Schema Generation](#generating-a-schema)
    - [Data Validation](#validating-a-data-file-against-a-schema)
- [Repository Structure](#repository-structure)
- [References](#references)

## Intro
### Background 
The FDA-NIH Biomarker Working Group (FNBWG) BEST resource<sup>1</sup> defines a biomarker as a "characteristic that is measured as an indicator of normal biological processes, pathogenic processes, or responses to an exposure or intervention, including therapeutic interventions". Biomarkers, measured in body fluids or tissues, are useful instrements for clinical inquiry and a growing focus of research. Biomarkers comprise important tools in the transition toward Predictive, Preventive, Personalized, Participatory medicine<sup>2</sup> and serve as valuable indicators in drug development, as well as surrogate endpoints in clinical trials.

### Scope and Goal of the Project
Biomarker research has led to distributed sets of data and the overall collection of relevant biomarker data in many different resources. The goal of this project is to provide systematic harmonization and organization of biomarker data by mapping biomarker data from public sources to Common Fund data elements. Importantly, biomarker discovery <ins>is not</ins> the goal of this project. 

### Initial Biomarker Database Curation
This project focuses on creating a biomarker database from different, relevant resources. So far we have extracted biomarkers from 5 different resources: OpenTargets, ClinVar, GWAS Catalog, MarkerDB (automated curation), and OncoMX (manual curation). The information and data extracted from the resources was done based on an agreed upon defintion of biomarkers and what the core elements were for a biomarker (indicated in Figure 1).

## Biomarker Definition

![DataModel](https://user-images.githubusercontent.com/116293652/226414788-89e71a90-de6d-47d0-b3a7-f3baa4e667e7.png)  
Figure 1

The elements highlighted in green are data types that would need to be extracted from the resources in order for a basic biomarker definition to be formed (assessed_biomarker_entity, condition_name, biomarker_status, evidence_source/type). Other data types such as loinc_code, specimen_type, and best_biomarker_type were not deemed as core elements but still provide context to the defintion of a particular biomarker (clinical lab measurements, where to measure the biomarker from, and what type of biomarker it is). These data types were mapped to the biomarker from outside resources such as LOINC and Uberon Ontology.

There is also a notes section present in this databse and that includes extra/miscellaneous deatils of the biomarker. This can include the exact mutation/amino acid change/expression data, Uniprot identifier, panel information, and the genome build. This data could be mapped from an outside resource or could be extracted directly from the reource the biomarker is being extracted from.

Based on the resource that was being studied there can be some variation in how the data was extracted, manipulted, and harmonized to fit the structre of the above figure. This repository will provide examples of this alonsgide the table generated and other resources needed to gain information/data for the biomarker.

## Usage

### Workflow

The general workflow is as described in the flowchart below. It starts with the most current data dictionary. The data dictionary can then be converted into a JSON schema following the steps in the [generating a schema](#generating-a-schema) section. Once the current version's schema has been generated, you can validate your data files against the schema to ensure they conform to the latest data dictionary. Instructions for validation are in the [validating a data file against a schema](#validating-a-data-file-against-a-schema) section. 

```mermaid
flowchart TD
    A[Data Dictionary] --> B{Generate JSON Schema}
    B --> D
    C[Data File] --> D{Validate Data File}
    D --> E[Log File Output]
```

### General Notes

The `.gitignore` file includes entries for the directories `home/` and `env/`. The `home/` directory can be used for any source files, temp files, log files, files larger than Github's limit of 100 MiB, or any other files that don't need to be pushed to the upstream repository. The `env/` directory should be the name of your virtual environment (instructions in next section). 

### Starting up the Virtual Environment

You can run the project locally or through a virtual environment. A virtual environment is recommended to avoid potential dependency and/or versioning issues. 

If your virtual environment has not been created yet, you can do so with:

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

### Generating a Schema

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

Move your current working directory to `data_dictionary/` and run the `process_dictonary.py` script passing in the filepath to the data dictionary TSV you want to process. 

```bash
cd data_dictionary
python process_dictionary.py <FILEPATH/TO/DICTIONARY>
```

### Validating a Data File Against a Schema

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

## Repository Structure 

| Directory             | Description                                                                           |
|-----------------------|---------------------------------------------------------------------------------------|
| `data_dictionary`     | Contains the information for the agreed upon data dictionary.             |
| `mapping_data`        | Contains some supporting data that can be used to map contextual data to the biomarkers.   |
| `schema`              | Contains the validation JSON schemas derived from the data dictonary.                 |
| `src`                 | Contains the scripts used for data extraction.                                                         |
| `supplementary_files` | Supplementary documents for the project.                                              | 

## References

- **<sup>1</sup>**: FDA-NIH_Biomarker_Working_Group. in BEST (Biomarkers, EndpointS, and other Tools) Resource [https://www.ncbi.nlm.nih.gov/books/NBK326791].     (2016). 
- **<sup>2</sup>**: Hood, L., Balling, R. & Auffray, C. Revolutionizing medicine in the 21st century through systems approaches. Biotechnol J 7, 992-1001 (2012). https://doi.org:10.1002/biot.201100306 