#!/usr/bin/env/python3
''' BiomarkerKB data dictionary processor. Reads in the data dictionary TSV and converts it to 
a JSON validation schema. 

Usage: python dictionary_utils.py [options]

    Positional arguments:
        file_path           filepath of the data dictionary TSV to convert

    Optional arguments 
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

def user_args() -> None:
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
    # check that the filepath passed is a TSV file
    if not (options.file_path.endswith('.tsv') or options.file_path.endswith('txt')):
        raise ValueError(f'Error: Expects TSV file as input.')
    # check that the user passed input filepath exists
    validate_filepath(options.file_path, 'input')

    generate_schema(options.file_path)

def generate_schema(filepath: str) -> None:
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
        'type': 'array',
        'title': _output_file,
        'required': [],
        'properties': {},
        'allOf': []
    }
    
    with open(filepath, 'r', encoding = 'utf8') as f:
        data = csv.DictReader(f, delimiter = '\t')
        for row in data:

            # skip empty rows
            if all(v == '' or v == '-' for v in row.values()):
                continue 

            # trim whitespace from each value
            # row = {k: v.strip() for k, v in row.items()}

            # handle required properties 
            if row['requirement'] == 'required':
                biomarkerkb_schema['required'].append(row['properties'])
            
            # add property details 
            biomarkerkb_schema['properties'][row['properties']] = {
                'title': row['properties'],
                'description': row['description'],
                'type': row['type'],
                'examples': [row['example']],
                'pattern': row['pattern']
            }

            # handle conditional properties 
            if row['conditionals'] != '-':
                conditional_reqs = [req.strip() for req in row['conditionals'].split(',')] 
                conditional_fragment = {
                    'if': {
                        'properties': {
                            row['properties']: {}
                        },
                        'required': [row['properties']]
                    },
                    'then': {
                        'anyOf': [
                            {
                                'properties': {
                                    conditional_req: {}
                                },
                                'required': [conditional_req]
                            } for conditional_req in conditional_reqs
                        ]
                    }
                }
                biomarkerkb_schema['allOf'].append(conditional_fragment)

            # handle exclusion properties
            if row['exclusions'] != '-':
                exclusions = [exclusion.strip() for exclusion in row['exclusions'].split(',')]
                exclusion_fragment = {
                    'if': {
                        'properties': {
                            row['properties']: {}
                        },
                        'required': [row['properties']]
                    },
                    'then': {
                        'not': {
                            'anyOf': [
                                {'required': [exclusion]} for exclusion in exclusions
                            ]
                        }
                    }
                }
                biomarkerkb_schema['allOf'].append(exclusion_fragment)

            
    with open(f'{_output_path}/{_output_file}', 'w') as f:
        json.dump(biomarkerkb_schema, f)


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
            raise ValueError(f'Error: The (input) file {filepath} does not exist.')
    elif mode == 'output':
        if not os.path.isdir(filepath):
            raise ValueError(f'Error: The (output) directory {filepath} does not exist.')
    else:
        raise ValueError(f'Validate_filepath error: Invalid mode {mode}')

def main() -> None:

    global _version
    global _id_prefix
    global _output_path
    global _output_file
    global _schema

    # grab configuration variables from config file  
    with open('../conf.json') as f:
        config = json.load(f)
        _version = config['version']
        _id_prefix = config[_CONF_KEY]['raw_url_prefix']
        _output_path = f"{config[_CONF_KEY]['output_path']}/v{_version}/"
        _output_file = config[_CONF_KEY]['output_file']
        _schema = config[_CONF_KEY]['schema']
    
    # make sure the schema output directory exists
    validate_filepath(_output_path, 'output')

    # parse the user arguments 
    user_args() 

if __name__ == '__main__':
    main()