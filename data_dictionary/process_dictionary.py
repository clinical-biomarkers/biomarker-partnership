#!/usr/bin/env/python3
''' Biomarker-Partnership data dictionary processor. Reads in the data dictionary JSON and converts it to 
a JSON validation schema. 

Usage: python process_dictionary.py [options]

    Positional arguments:
        file_path           filepath of the data dictionary JSON to convert

    Optional arguments: 
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
    
    parser.add_argument('file_path', help = 'filepath of the data dictionary JSON')
    parser.add_argument('-v', '--version', action = 'version', version = f'%(prog)s {_version}')

    # print out help if script is called with no input arguments
    if len(sys.argv) <= 1:
        sys.argv.append('--help')
    
    options = parser.parse_args()
    # check that the filepath passed is a JSON file
    if not (options.file_path.endswith('.json')):
        raise ValueError(f'Error: Expects JSON file as input.')
    # check that the user passed input filepath exists
    validate_filepath(options.file_path, 'input')

    generate_schema_json(options.file_path)

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
        'items': {
            'type': 'object',
            'required': [],
            'properties': {},
            'allOf': []
        }
    }
    
    with open(filepath, 'r', encoding = 'utf8') as f:
        data = csv.DictReader(f, delimiter = '\t')
        for row in data:

            # skip empty rows
            if all(v == '' or v == '-' for v in row.values()):
                continue 

            # trim whitespace from each value
            # row = {k: v.strip() for k, v in row.items()}

            property_name = row['properties']
            property_type = [row['type'], 'null'] if row['requirement'] != 'required' else row['type']

            # handle required properties 
            if row['requirement'] == 'required':
                biomarkerkb_schema['items']['required'].append(row['properties'])
            
            # construct property schema 
            property_schema = {
                'title': property_name,
                'description': row['description'],
                'type': property_type,
                'examples': [row['example']]
            }

            # check if property type is an array 
            if property_type == 'array':
                item_type = row['content_type']
                item_pattern = row['pattern'] if row['pattern'] and row['pattern'] != '-' else None 
                property_schema['items'] = {'type': item_type}
                if item_pattern:
                    property_schema['items']['pattern'] = item_pattern
            # for non-array properties 
            else:
                if row['pattern'] and row['pattern'] != '-':
                    property_schema['pattern'] = row['pattern']

            # add property details to schema
            biomarkerkb_schema['items']['properties'][property_name] = property_schema

            # handle conditional properties 
            if row['conditionals'] != '-':
                conditional_reqs = [req.strip() for req in row['conditionals'].split(',')] 
                conditional_fragment = {
                    'if': {
                        'properties': {
                            row['properties']: {'not': {'const': None}}
                        },
                        'required': [row['properties']]
                    },
                    'then': {
                        'allOf': [
                            {
                                'properties': {
                                    conditional_req: {'not': {'const': None}}
                                },
                                'required': [conditional_req]
                            } for conditional_req in conditional_reqs
                        ]
                    }
                }
                biomarkerkb_schema['items']['allOf'].append(conditional_fragment)

            # handle exclusion properties
            if row['exclusions'] != '-':
                exclusions = [exclusion.strip() for exclusion in row['exclusions'].split(',')]
                exclusion_fragment = {
                    'if': {
                        'properties': {
                            row['properties']: {'not': {'type': "null"}}
                        },
                        'required': [row['properties']]
                    },
                    'then': {
                        'allOf': [
                            {
                                'properties': {
                                    exclusion: {'anyOf': [{'type': 'null'}, {'const': None}]}
                                },
                                'required': [exclusion]
                            } for exclusion in exclusions
                        ]
                    }
                }
                biomarkerkb_schema['items']['allOf'].append(exclusion_fragment)
            
    with open(f'{_output_path}/{_output_file}', 'w') as f:
        json.dump(biomarkerkb_schema, f)

def generate_schema_json(filepath: str) -> None:
    ''' Converts the data dictionary into a JSON schema. 

    Parameters
    ----------
    filepath: str
        Filepath to the source data dictionary file. 
    '''

    # construct root of json schema 
    raw_url = _id_prefix + f'v{_version}/{_output_file}'
    biomarker_schema = {
        '$schema': _schema,
        '$id': raw_url,
        'type': 'array',
        'title': _output_file,
        'items': {
            'type': 'object',
            'required': [],
            'properties': {},
            'allOf': []
        }
    }

    # read in data dictionary
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # iterate through top level keys
    for key in data.keys():
        
        # parse property metadata
        prop_description = data[key]['description']
        prop_type = [data[key]['type']]
        prop_required = data[key]['required']['requirement'] 
        # if conditional requirement, parse conditional and exclusion fields
        if prop_required == 'conditional':
            prop_conditionals = data[key]['required']['conditionals']
            prop_exclusions = data[key]['required']['exclusions']
        # if top level property, parse examples and pattern  
        if prop_type != 'object' and prop_type != 'array':
            prop_example = data[key]['example']
            prop_pattern = data[key]['pattern']
            # create top level property schema portion
            property_schema = {
                'title': key, 
                'description': prop_description,
                'type': [prop_type, 'null'] if prop_required != True else prop_type,
                'examples': prop_example
            }

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
    with open('../conf.json', 'r') as f:
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