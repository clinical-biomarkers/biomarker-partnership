# Data Conversion 

The project's data can be viewed in multiple formats. The main view (the JSON data model), is the main format that comprehensively captures the complexity and nested nature of the biomarker data. However, for simple biomarker queries and searching, the data can also be viewed in a table (TSV) format. Due to the hierarchical and nested nature of the data model, the table view is a simplified version of the data model where each entry is unrolled into (if applicable) multiple rows. The third format is in N-Triples (NT). The triple conversion is a one-way conversion that goes from JSON to NT. 

The code in this directory handles the logic for the data conversion. The entry point is the `data_conversion.py` script. Right now the logic is updated for the `v0.3.1` data model schema and supports the following conversions:
- JSON -> TSV
- JSON -> NT
- TSV -> JSON 

## Prerequisites / Notes

In order for the TSV to JSON logic to fully fill out the supplementary information for the evidence source citation data, you will have to create a local environment `.env` file in this directory and include your email and a PubMed API key. The logic will work if you just include your email and no API key, however, the rate limit witout an API key is more limited, increasing the likelihood of a 429 Too Many Requests error. You can find the instructions for obtaining an API key [here](https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/). For example:

```
EMAIL='example@example.com'
API_KEY='key'
```

The [pymed](https://github.com/gijswobben/pymed) wrapper library is used for the PubMed API access. Due to the scrict rate limiting this might take a long time if you have a large TSV file. If performance becomes an issue, you can change the global `ADD_CITATION_DATA` flag to `False` in the `tsv_to_json.py` file, which will skip the citation build. Note: the code does not fill in any of the reference data, that will have to be done manually. 

The Uniprot KB API used to get the synonym names for a Uniprot accession has a more generous API rate limit that likely won't cause a significant bottleneck unless your TSV file is extremely large. There is some basic logic in place to make sure the rate limit is not hit during the TSV to JSON conversion. It is more likely that the PubMed API bottlenecks large file conversion. 

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
    - If the resource API call is supported, a warning will be logged and printed for each value where the name provided in the TSV file does not match the recommended name from the resource. 

## Namespace Support 

The full JSON data model version includes various supplementary data fields that is not captured by the simplified table (TSV) views such as synonym data and citation data. The TSV to JSON conversion supports the following resource API calls to automate the populating of these fields:

- PubMed
- Disease Ontology 
- UniprotKB
- Chemical Entities of Biological Interest (ChEBI)
- Cell Ontology 
- HUGO Gene Nomenclature Committee (HGNC) 
