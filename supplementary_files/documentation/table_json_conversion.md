# Table and JSON Data Conversion 

The project's data can be viewed in multiple formats. The main view (the JSON data model), is the main format that comprehensively captures the complexity and nested nature of the biomarker data. However, for simple biomarker queries and searching, the data can also be viewed in a table (TSV) format. Due to the hierarchical and nested nature of the data model, the table view is a simplified version of the data model where each entry is unrolled into (if applicable) multiple rows. 

## Data Conversion 

The `table_json_conversion.py` script in the `src/` directory can be used to convert the data between the two formats. The script takes these arguments: 

``` 
Positional arguments:
    source_filepath     filepath of the source file (accepts JSON or TSV)
    target_filepath     filepath of the target file (accepts JSON or TSV)

Optional Arguments:
    -h --help           show the help message and exit 
    -v --version        show the current version number and exit
```

Move your current working directory to `src/` and run the `table_json_conversion.py` script passing in the filepath to the source and target file path's: 

```
cd src
python table_json_conversion.py <FILEPATH/TO/SOURCE> <FILEPATH/TO/TARGET>
```

The script will automatically detect the conversion direction. If a JSON file is passed as the source, it will check that a TSV file was passed as the output (or target) file and vice versa. The script expects the filepath to the log path to exist (set in the `conf.json` file). By default, the filepath is `../home/logs/conversion_log.log`. 

Some notes for the JSON to TSV conversion (updated for version 0.3 of the data model schema): 
- The output table will have the columns `biomarker_id`, `biomarker`, `assessed_biomarker_entity`, `assessed_biomarker_entity_id`, `assessed_entity_type`, `condition`, `condition_id`, `exposure_agent`, `exposure_agent_id`, `best_biomarker_role`, `specimen`, `specimen_id`, `loinc_code`, `evidence_source`, `evidence`, and `tag` in that exact order.
- If any of the non-required fields are not present, they will be populated with empty strings.
- 

For the TSV to JSON conversion: 
- 