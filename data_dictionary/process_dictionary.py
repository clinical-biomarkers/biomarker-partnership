#!/usr/bin/env/python3
''' BiomarkerKB data dictionary processor. Reads in the data dictionary TSV and converts it to 
a JSON validation schema. 

This script will perform various functions related to processing the BiomarkerKB data dicitonary
and associated schemas. 

Usage: python dictionary_utils [options]

    Positional arguments:
        file_path           filepath of the data dictionary TSV to convert

    optional arguments 
        -h --help           show the help message and exit
        -v --version        show current version number and exit

'''

import csv 
import json
import argparse
import sys
import os 

_version = None 
_id_prefix = None
_output_path = None
_output_file = None
_schema = None

def user_args():
    ''' Parses the command line arguments. 
    '''

    # argument parser
    parser = argparse.ArgumentParser(
        prog = 'biomarkerkb_schema_generator',
        usage = 'python process_dictionary.py [options]'
    )
    
    parser.add_argument('file_path', help = 'filepath of the data dictionary TSV')
    parser.add_argument('-v', '--version', action = 'version', version = f'%(prog)s {_version}')

    # print out help if script is called with no input arguments
    if len(sys.argv) <= 1:
        sys.argv.append('--help')
    
    options = parser.parse_args()
    validate_filepath(options.filepath, 'input')

    generate_schema(options.filepath)

def generate_schema(filepath):
    ''' Converts the data dictionary into a JSON schema. 

    Parameters
    ----------
    filepath: str
        Filepath to the source data dictionary file. 
    '''

    raw_url = _id_prefix + f'v{_version}/{_output_file}'

    biomarkerkb_schema = {
        '$schema': _schema,
        '$id': raw_url,
        'type': 'object',
        'title': _output_file
    }
    

def validate_filepath(filepath, mode):
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
            raise ValueError(f'Error: The (input) file {filepath} does not exist.')
    elif mode == 'output':
        if not os.path.isdir(filepath):
            raise ValueError(f'Error: The (output) directory {filepath} does not exist.')
    else:
        raise ValueError(f'validate_filepath error: Invalid mode {mode}')

def main():

    global _version
    global _id_prefix
    global _output_path
    global _output_file
    global _schema

    # grab version number from the config file
    with open('conf.json') as f:
        config = json.load(f)
        _version = config['version']
        _id_prefix = config['raw_url_prefix']
        _output_path = f"{config['output_path']}/{_version}/{config['output_file']}"
        _output_file = config['output_file']
        _schema = config['schema']

    user_args() 

if __name__ == '__main__':
    main()