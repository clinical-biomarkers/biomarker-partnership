# Data Conversion 

The project's data can be viewed in multiple formats. The main view (the JSON data model), is the main format that comprehensively captures the complexity and nested nature of the biomarker data. However, for simple biomarker queries and searching, the data can also be viewed in a table (TSV) format. Due to the hierarchical and nested nature of the data model, the table view is a simplified version of the data model where each entry is unrolled into (if applicable) multiple rows. The third format is in N-Triples (NT). The triple conversion is a one-way conversion that goes from JSON to NT. 

The code in this directory handles the logic for the data conversion. The entry point is the `data_conversion.py` script. Right now the logic is updated for the `v0.3.4` data model schema and supports the following conversions:
- JSON -> TSV
- JSON -> NT
- TSV -> JSON 

## TSV to JSON Prerequisites / Notes

The TSV to JSON conversion code can handle the filling in of some metadata automatically, for example, Pubmed paper citation data and some `assessed_biomarker_entity`/`condition` metadata such as retrieving synonyms. However, as written to handle dynamic on-the-fly retrieval from various sources without having to specify them before hand, this code is generally very expensive in terms of time complexity (requiring potentially many expensive I/O operations). For very large files, it is recommended to run the conversion with these features turned off (by specifying the `-m` flag) and then write a supplementary script to fill in the metadata fields separately. For large files, this will save you a significant amount of time during the conversion at the cost of having to fill in your own metadata. If you write a separate script to fill in metadata, you can make use of the [mapping data](../../mapping_data/) files and only call the resource's API if the data is not already contained locally.

In order for the TSV to JSON conversion to utilize the NCBI API (if you are converting data with PubMed papers used as evidence or converting NCBI entities that you want automated synonym retrieval for), it is recommended to create a local environment `.env` file in this directory and include your email and an API key. The code will work if you just include your email and no API key, however, the rate limit witout an API key is more limited, increasing the likelihood of a `429 Too Many Requests` error. You can find the instructions for obtaining an API key [here](https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/). For example:

```
EMAIL='example@example.com'
API_KEY='key'
```

The [pymed](https://github.com/gijswobben/pymed) wrapper library is used for the PubMed API access and the ESummary Utility is used directly for assessed biomarker entity synonym retrieval. Due to the scrict rate limiting this might take a long time if you have a large TSV file with many NCBI/PubMed references. The Pubmed citation retrieval is not handled by the `-m`/`--metadata` flag, but the `ADD_CITATION_DATA` global variable in the `fmt_lib/tsv_to_json.py` file. If needed or desired, you can set this to `False` to skip the ciation build.    

Note: the code does not fill in any of the `citation[evidence]` data, that will have to be done manually. 

## Usage 

The `data_conversion.py` script can take these arguments: 

``` 
Positional arguments:
    source_filepath     filepath of the source file
    target_filepath     filepath of the target file to generate (including the filename and extension)

Optional Arguments:
    -c --chunk          log/write checkpoint (if not provided, will default to 10,000)
    -l --log            whether to print a message indicating the progress (default False)
    -m --metadata       whether to attempt automatic metadata retrieval for TSV to JSON converstions (default True)
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
- NCBI Gene Database
- Disease Ontology 
- UniprotKB
- Chemical Entities of Biological Interest (ChEBI)
- Cell Ontology 
- HUGO Gene Nomenclature Committee (HGNC) 
