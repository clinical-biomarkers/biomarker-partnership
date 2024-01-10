#!/usr/bin/env/python3
''' Biomarker-Partnership data converter. This script is the entry point for the data conversion
logic. Can convert table formatted data to the data model JSON or JSON data to the table format. 
Will eventually support converting data to an nt file for RDF triples. 

Script is not agnostic to the formatting of the current table format/structure or the current data
model JSON schema. If those are updated in the future, this script needs to be updated. 

Currently written for the v0.3.1 data model schema and supports the following conversions:
    - JSON -> TSV
    - TSV -> JSON

Usage: data_conversion.py [options]

    If the source file passed is of type JSON, then it will assume the conversion is JSON -> TSV 
    and the target_filepath should be of type .tsv. If the source file passed is of type TSV, then 
    it will assume the conversion is TSV -> JSON and the target_filepath should be of type .json. 

    Positional arguments:
        source_filepath     filepath of the source file (accepts JSON or TSV)
        target_filepath     filepath of the target file (accepts JSON or TSV)
    
    Optional arguments: 
        -h --help           show the help message and exit 
        -v --version        show current version number and exit 
'''

import logging 
import argparse
import os
import sys
import misc_functions as misc_fns
import json_to_tsv as j_to_t
import tsv_to_json as t_to_j

_CONF_KEY = 'data_conversion'
_version = None
URL_MAP = None
NAMESPACE_MAP = None

# if table format changes in the future this will need to be updated
TSV_HEADERS = ['biomarker_id', 'biomarker', 'assessed_biomarker_entity', 'assessed_biomarker_entity_id', 
            'assessed_entity_type', 'condition', 'condition_id', 'exposure_agent', 'exposure_agent_id', 
            'best_biomarker_role', 'specimen', 'specimen_id', 'loinc_code', 'evidence_source', 'evidence',
            'tag']

def user_args() -> None:
    ''' Parse user inputted arguments and call the appropriate function to convert the data.
    '''

    # argument parser
    parser = argparse.ArgumentParser(
        prog = 'biomarker-partnership data conversion',
        usage = 'python data_conversion.py [options] source_filepath target_filepath'
    )

    # add arguments
    parser.add_argument('source_filepath', help = 'filepath of the source file')
    parser.add_argument('target_filepath', help = 'filepath of the target file to generate')
    parser.add_argument('-v', '--version', action = 'version', version = f'%(prog)s {_version}')

    # print out help if script is called without enough arguments
    if len(os.sys.argv) <= 2:
        sys.argv.append('-h')
    
    options = parser.parse_args()
    # check that the user provided filepaths for both the source and target files exist
    misc_fns.validate_filepath(options.source_filepath, 'input')
    misc_fns.validate_filepath(os.path.split(options.target_filepath)[0], 'output')

    # log the user passed arguments
    logging.info(f'Arguments passed:\n\tsource_filepath = {options.source_filepath}\n\ttarget_filepath = {options.target_filepath}')

    ### check that the source and target file types passed indicate a supported conversion type and pass 
    ### to the appropriate function for processing 

    # checking for the JSON -> TSV conversion
    if options.source_filepath.endswith('.json'):
        if not (options.target_filepath.endswith('.tsv')):
            logging.error(f'Error: Incorrect target_filepath file type for source type of JSON, expects TSV.')
            print(f'Error: Incorrect target_filepath file type for source type of JSON, expects TSV.')
            sys.exit(1)
        # if a valid source JSON conversion called, continue to processing
        j_to_t.json_to_tsv(options.source_filepath, options.target_filepath)
    
    # checking for the TSV -> JSON conversion
    if options.source_filepath.endswith('.tsv'):
        if not (options.target_filepath.endswith('.json')):
            logging.error(f'Error: Incorrect target_filepath file type for source type of TSV, expects JSON.')
            print(f'Error: Incorrect target_filepath file type for source type of TSV, expects JSON.')  
            sys.exit(1)
        # if a valid source TSV conversion called, continue to processing
        t_to_j.tsv_to_json(options.source_filepath, options.target_filepath)
        
def main():
    ''' Main entry point for the data conversion logic.
    '''
    
    global _version
    global URL_MAP
    global NAMESPACE_MAP
    
    # grab config information
    config = misc_fns.load_json('../../config.json')
    _version = config['version']
    log_path = config[_CONF_KEY]['log_path']
    url_map_path = config[_CONF_KEY]['url_map_path']
    namespace_map_path = config[_CONF_KEY]['namespace_map_path']

    # load in the URL map and namespace map
    URL_MAP = misc_fns.load_json(url_map_path)
    NAMESPACE_MAP = misc_fns.load_json(namespace_map_path)
    
    # make sure directory to dump logs in exists
    misc_fns.validate_filepath(os.path.split(log_path)[0], 'output')
    # set up logging
    misc_fns.setup_logging(log_path)

    # log start delimiter for new run
    logging.info('################################## Start ##################################')

    # parse command line arguments
    user_args()

    # log end delimiter for run
    logging.info('---------------------------------- End ----------------------------------')

if __name__ == '__main__':
    main()