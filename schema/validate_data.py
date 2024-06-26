#!/usr/bin/env/python3
''' BiomarkerKB data validator. Validates a given input set against the data dictionary JSON schema. 

Usage: python validate_data.py [options]

    Positional arguments:
        data_filepath       filepath of the input data file to validate (accepts tab delimited tsv or txt files or JSON)
        schema_filepath     filepath to the schema file to validate against
    
    Optional arguments
        -o --output         whether to save the intermediate json (store_true argument)
        -c --chunk          chunk size to process the source data
        -h --help           show the help message and exit
        -v --version        show current version number and exit 
'''

import json
from jsonschema import validate, ValidationError
import argparse
import sys 
import os 
import logging
import pandas as pd

_VAL_KEY = 'validation'
_version = None 

def user_args(intermediate_path: str = None) -> None:
    ''' Parses the command line arguments.

    Parameters
    ----------
    intermediate_path: str
        Filepath to store the intermediate JSON. 
    '''

    # argument parser
    parser = argparse.ArgumentParser(
        prog = 'biomarkerkb_data_validator',
        usage = 'python validate_data.py [options]'
    )

    parser.add_argument('data_filepath', help = 'filepath of the input file to validate (tsv, txt, or json)')
    parser.add_argument('schema_filepath', help = 'filepath of the schema file to validate against (json)')
    parser.add_argument('-o', '--output', action = 'store_true', help = 'whether to save the intermediate json, only applicable if input file is tsv or txt format (store_true argument)')
    # parser.add_argument('-c', '--chunk', action = 'store', help = 'chunk size to process the source data, only applicable if input file is tsv or txt format')
    parser.add_argument('-v', '--version', action = 'version', version = f'%(prog)s {_version}')

    # print out help if script is called with no arguments 
    if len(sys.argv) <= 1:
        sys.argv.append('--help')
    
    options = parser.parse_args()

    # log the user passed arguments
    logging.info(f'Arguments passed:\ndata_filepath = {options.data_filepath}\nschema_filepath = {options.schema_filepath}\noutput flag = {options.output}')

    # check that the correct file types were passed
    if not (options.data_filepath.endswith('.tsv') or options.data_filepath.endswith('.txt') or options.data_filepath.endswith('.json')):
        raise ValueError(f'The source data filepath must be of type .tsv, .txt, or .json.')
    if not options.schema_filepath.endswith('.json'):
        raise ValueError(f'The schema must be of type .json.')
    
    # check that the user passed input filepath exists
    validate_filepath(options.data_filepath, 'input')
    # check that the user passed schema filepath exists
    validate_filepath(options.schema_filepath, 'input')

    output_flag = False
    chunk_size = None
    source_type_json = True
    if (options.data_filepath.endswith('.tsv') or options.data_filepath.endswith('.txt')):
        source_type_json = False
        if options.output:
            output_flag = True 
            input_filename = os.path.split(options.data_filepath)[1]
            intermediate_path += f'v{_version}/'
            validate_filepath(intermediate_path, 'output')
            intermediate_path += f"{input_filename.split('.')[0]}.json"
        if options.chunk:
            try:
                chunk_size = int(options.chunk)
            except ValueError:
                raise ValueError(f'Chunk value must be of type integer.')

    validate_data(options.data_filepath, source_type_json, options.schema_filepath, output_flag, intermediate_path, chunk_size)

def convert_to_json(source: str, output_flag: bool = False, intermediate_path: str = None, chunk_size: int = None) -> dict:
    ''' Converts the input data to a JSON file for schema validation. In cases where the source 
    data is extremely large, the output_flag and chunk_size parameters can be used to prevent 
    hitting the system's memory limit.

    Parameters
    ----------
    source: str 
        Filepath of the source file to convert to a JSON file for validation.
    output_flag: bool
        Whether to save the intermediate json (optional, default False).
    intermediate_path: str
        Filepath to store the intermediate JSON. 
    chunk_size: int 
        Chunk size to process the source data with (optional, default None).

    Returns
    -------
    dict    
        JSON for the converted data sheet to validate. 
    '''

    json_data = []

    # handle parsing by chunk
    if chunk_size: 
        for chunk in pd.read_csv(source, delimiter = '\t', chunksize = chunk):
            chunk_json = chunk.to_json(orient = 'records')
            json_data.extend(json.loads(chunk_json))
    # normal parsing 
    else: 
        df = pd.read_csv(source, delimiter = '\t')
        json_string = df.to_json(orient = 'records')
        json_data = json.loads(json_string)

    if output_flag:
        with open(intermediate_path, 'w', encoding = 'utf-8') as f:
            json.dump(json_data, f, indent = 4)
    
    return json_data

def validate_data(source: str, source_type_json: bool, schema: str, output_flag: bool = False, intermediate_path: str = None, chunk_size: int = None):
    ''' Validates the user passed source file against the user passed schema file. 

    Parameters
    ----------
    source: str
        Filepath of the data file to validate. 
    source_type: bool
        Denotes whether the input file is json or not json (True for json, False for non json).
    schema: str
        Filepath of the schema file to validate against. 
    output_flag: bool
        Whether to save the intermediate json (optional, default False).
    intermediate_path: str
        Filepath to store the intermediate JSON. 
    chunk_size: int
        Chunk size to process the source data with (optional, default None).
    '''

    # if input is not json than no need to convert first
    if not source_type_json:
        data = convert_to_json(source, output_flag, intermediate_path, chunk_size)
    elif source_type_json:
        with open(source, 'r') as f:
            data = json.load(f) 

    with open(schema, 'r') as f:
        schema_data = json.load(f)
    
    try:
        # attempt to validate the data
        validate(instance = data, schema = schema_data)
        print(f'Validation successful.')
        logging.info('Validation successful.')
    except ValidationError as e:
        print(f'Validation error: check log file.')
        logging.error(f'Validation error:\n{e}')

def validate_filepath(filepath: str, mode: str) -> None:
    ''' Validates the filepaths for the user inputted source path and
    the destination path.

    Parameters
    ----------
    filepath: str
        Filepath to the source data dictionary file or the output path.
    mode: str
        Whether checking the output directory path or the input file. ('input' or 'output')
    '''

    if mode == 'input':
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f'Error: The (input) file {filepath} does not exist.')
    elif mode == 'output':
        if not os.path.isdir(filepath):
            raise FileNotFoundError(f'Error: The (output) directory {filepath} does not exist.')
    else:
        raise ValueError(f'Validate_filepath error: Invalid mode {mode}')

def setup_logging(log_path: str) -> None:
    ''' Configures the logger to write to a file.

    Parameters
    ----------
    log_path: str
        The path of the log file.
    '''
    logging.basicConfig(filename = log_path, level = logging.INFO, 
                        format = '%(asctime)s - %(levelname)s - %(message)s')

def main() -> None:
    
    global _version

    # grab version number from config file
    with open('../conf.json') as f:
        config = json.load(f)
        _version = config['version']
        log_path = config[_VAL_KEY]['log_path']
        intermediate_path = config[_VAL_KEY]['intermediate_path']
    
    # make sure directory to dump logs in exists 
    validate_filepath(os.path.split(log_path)[0], 'output')
    setup_logging(log_path)

    # log start delimiter for a new run
    logging.info('################################## Start ##################################')

    # parse the user arguments 
    user_args(intermediate_path)
    
    # log the end delimiter for the run 
    logging.info('################################## End ##################################\n')

if __name__ == '__main__':
    main()
