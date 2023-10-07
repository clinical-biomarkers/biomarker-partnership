#!/usr/bin/env/python3
''' BiomarkerKB data dictionary processor. Reads in the data dictionary TSV and converts it to 
a JSON validation schema. 

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

_CONF_KEY = 'schema_generation'
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
    validate_filepath(options.file_path, 'input')

    generate_schema(options.file_path)

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
        'title': _output_file,
        'required': [],
        'properties': {}
    }
    
    with open(filepath, 'r', encoding = 'utf8') as f:
        data = csv.DictReader(f, delimiter = '\t')
        for row in data:
            if row['requirement'] == 'required':
                biomarkerkb_schema['required'].append(row['properties'])
            biomarkerkb_schema['properties'][row['properties']] = {
                'title': row['properties'],
                'description': row['description'],
                'type': row['type'],
                'examples': [row['example']],
                'pattern': row['pattern']
            }
            
    with open(f'{_output_path}/{_output_file}', 'w') as f:
        json.dump(biomarkerkb_schema, f)


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
    with open('../conf.json') as f:
        config = json.load(f)
        _version = config['version']
        _id_prefix = config[_CONF_KEY]['raw_url_prefix']
        _output_path = f"{config[_CONF_KEY]['output_path']}/v{_version}/"
        _output_file = config[_CONF_KEY]['output_file']
        _schema = config[_CONF_KEY]['schema']
    
    validate_filepath(_output_path, 'output')

    user_args() 

if __name__ == '__main__':
    main()