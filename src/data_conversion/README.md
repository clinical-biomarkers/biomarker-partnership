# Data Conversion 

The project's data can be viewed in multiple formats. The main view (the JSON data model), is the main format that comprehensively captures the complexity and nested nature of the biomarker data. However, for simple biomarker queries and searching, the data can also be viewed in a table (TSV) format. Due to the hierarchical and nested nature of the data model, the table view is a simplified version of the data model where each entry is unrolled into (if applicable) multiple rows. 

The code in this directory handles the logic for the data conversion. The entry point is the `data_conversion.py` script. Right now the logic is written for the `v0.3.1` data model schema and supports the following conversions:
- JSON -> TSV
- TSV -> JSON 

In order for the TSV to JSON logic to fully fill out the supplementary information for the evidence source data, you will have to create a local environment `.env` file in this directory and include your email. This is required because the PubMed API requires an email in case of API rate limiting/abuse. For example:

```
EMAIL='example@example.com'
```

The [pymed](https://github.com/gijswobben/pymed) wrapper library used for the PubMed API access *should* handle request batching so rate limiting is not exceeded 

## Usage 

The `data_conversion.py` script can take these arguments: 

``` 
Positional arguments:
    source_filepath     filepath of the source file
    target_filepath     filepath of the target file to generate (including the filename and extension)

Optional Arguments:
    -h --help           show the help message and exit 
    -v --version        show the current version number and exit
```

Move your current working directory to `src/data_conversion/` and run the `data_conversion.py` script passing in the filepath to the source and target file path's: 

```
cd src/data_conversion
python data_conversion.py <FILEPATH/TO/SOURCE> <FILEPATH/TO/TARGET>
```

The script will automatically detect the conversion direction. For example, if a JSON file is passed as the source, it will check that a TSV file was passed as the output (or target) file and vice versa. The script expects the filepath to the log path to exist (set in the `conf.json` file). By default, the filepath is `../../home/logs/conversion_log.log`. 

Some notes for the JSON to TSV conversion: 
- The output table will have the columns `biomarker_id`, `biomarker`, `assessed_biomarker_entity`, `assessed_biomarker_entity_id`, `assessed_entity_type`, `condition`, `condition_id`, `exposure_agent`, `exposure_agent_id`, `best_biomarker_role`, `specimen`, `specimen_id`, `loinc_code`, `evidence_source`, `evidence`, and `tag` in that exact order.
- If any of the non-required fields are not present, they will be populated with empty strings.

For the TSV to JSON conversion: 
- The values for `assessed_biomarker_entity`, `condition`, `exposure_agent` are assumed to already be the recommended name for the entities, and are populated in the `recommended_name` field for each. 