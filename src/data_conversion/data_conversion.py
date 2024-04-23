''' Biomarker-Partnership data converter. This script is the entry point for the data conversion
logic. Can convert table formatted data to the data model JSON, JSON data to the table format, and
JSON data to N-Triples.

Script is not agnostic to the formatting of the current table format/structure or the current data
model JSON schema. If those are updated in the future, this script needs to be updated. 

Currently written for the v0.3.2 data model schema and supports the following conversions:
    - JSON -> TSV
    - TSV -> JSON
    - JSON -> NT

Usage: data_conversion.py [options]

    If the source file passed is of type JSON, then it will assume the conversion is JSON -> TSV 
    and the target_filepath should be of type .tsv. If the source file passed is of type TSV, then 
    it will assume the conversion is TSV -> JSON and the target_filepath should be of type .json. 

    Positional arguments:
        source_filepath     filepath of the source file (accepts JSON or TSV)
        target_filepath     filepath of the target file (accepts JSON or TSV)
    
    Optional arguments: 
        -c --chunk          log/write checkpoint (if not provided, will default to 10,000)
        -l --log            whether to print a message indicating the progress (default False)
        -m --metadata       whether to attempt automatic metadata retrieval for TSV to JSON converstions (default True)
        -h --help           show the help message and exit 
        -v --version        show current version number and exit 
'''

import logging 
import argparse
import os
import sys
import time
from fmt_lib import misc_functions as misc_fns
from fmt_lib import json_to_tsv as j_to_t
from fmt_lib import tsv_to_json as t_to_j
from fmt_lib import json_to_nt as j_to_nt

_CONF_KEY = 'data_conversion'
_version = None
TSV_HEADERS = ['biomarker_id', 'biomarker', 'assessed_biomarker_entity', 'assessed_biomarker_entity_id', 
            'assessed_entity_type', 'condition', 'condition_id', 'exposure_agent', 'exposure_agent_id', 
            'best_biomarker_role', 'specimen', 'specimen_id', 'loinc_code', 'evidence_source', 'evidence',
            'tag']

def user_args(url_map: dict, triples_map: dict, namespace_map: dict) -> None:
    ''' Parse user inputted arguments and call the appropriate function to convert the data.

    Parameters
    ----------
    url_map: dict
        Map for URL building.
    triples_map: dict 
        Map to build RDF triples.
    namespace_map: dict
        Map for resource namespaces.
    '''
    parser = argparse.ArgumentParser(
        prog = 'biomarker-partnership data conversion',
        usage = 'python data_conversion.py [options] source_filepath target_filepath'
    )
    parser.add_argument('source_filepath', help = 'filepath of the source file')
    parser.add_argument('target_filepath', help = 'filepath of the target file to generate')
    parser.add_argument('-c', '--chunk', type = int, default = 10_000, help = 'write checkpoint (default will dump to disk every 10,000 records/rows)')
    parser.add_argument('-l', '--log', action = 'store_true', help = 'whether to print a message indicating the write checkpoin has been hit (default False)')
    parser.add_argument('-m', '--metadata', action = 'store_false', help = 'whether to attempt automatic metadata retrieval for TSV to JSON converstions (default True)')
    parser.add_argument('-v', '--version', action = 'version', version = f'%(prog)s {_version}')
    if len(sys.argv) <= 2:
        sys.argv.append('-h')
    options = parser.parse_args()
    misc_fns.validate_filepath(options.source_filepath, 'input')
    misc_fns.validate_filepath(os.path.split(options.target_filepath)[0], 'output')

    logging.info(
        f'Arguments passed:\n\tsource_filepath = {options.source_filepath}\
            \n\ttarget_filepath = {options.target_filepath}\
            \n\tchunk = {options.chunk}\
            \n\tlog = {options.log}\
            \n\tmetadata = {options.metadata}'
    )

    ### check that the source and target file types passed indicate a supported conversion type and pass 
    ### to the appropriate function for processing 

    if options.source_filepath.endswith('.json'):
        if not (options.target_filepath.endswith('.tsv')) and not (options.target_filepath.endswith('.nt')):
            misc_fns.print_and_log('Error: Incorrect target_filepath file type for source type of JSON, expects TSV or NT.', 'error')
            print('Error: Incorrect target_filepath file type for source type of JSON, expects TSV or NT.')
            sys.exit(1)
        if options.target_filepath.endswith('.tsv'):
            j_to_t.json_to_tsv(options.source_filepath, options.target_filepath, TSV_HEADERS, options.chunk, options.log)
        elif options.target_filepath.endswith('.nt'):
            j_to_nt.json_to_nt(options.source_filepath, options.target_filepath, triples_map, namespace_map)
    elif options.source_filepath.endswith('.tsv'):
        if not (options.target_filepath.endswith('.json')):
            misc_fns.print_and_log('Error: Incorrect target_filepath file type for source type of TSV, expects JSON.', 'error')
            print('Error: Incorrect target_filepath file type for source type of TSV, expects JSON.')  
            sys.exit(1)
        t_to_j.tsv_to_json(options.source_filepath, options.target_filepath, TSV_HEADERS, url_map, namespace_map, options.chunk, options.log, options.metadata)
        
def main():
    ''' Main entry point for the data conversion logic.
    '''
    
    global _version
    
    config = misc_fns.load_json('../../conf.json')
    _version = config['version']
    log_path = config[_CONF_KEY]['log_path']
    url_map = misc_fns.load_json(config[_CONF_KEY]['url_map_path'])
    namespace_map = misc_fns.load_json(config[_CONF_KEY]['namespace_map_path'])
    triples_map = misc_fns.load_json(config[_CONF_KEY]['triples_map_path'])

    misc_fns.validate_filepath(os.path.split(log_path)[0], 'output')
    misc_fns.setup_logging(log_path)

    logging.info('################################## Start ##################################')
    start_time = time.time()
    user_args(url_map, triples_map, namespace_map)
    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.info(f'Estimated execution time: {elapsed_time} seconds (this is a rough estimate for debugging).')
    logging.info('---------------------------------- End ----------------------------------')

if __name__ == '__main__':
    main()
