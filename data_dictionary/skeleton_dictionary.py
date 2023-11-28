#!/usr/bin/env/python3
''' Biomarker-Partnership data dicitonary skeleton generator. Reads in a sample structure of the JSON
and converts it to a skeleton data dictionary. The metadata fields for each property will still have to
manually filled in by the user.

Usage: python skeleton_dictionary.py [options]

    Positional arguments:
        file_path           filepath of the sample data model JSON
    
    Optional arguments:
        -h --help           show the help message and exit
        -v --version        show the current version number and exit
'''

import json 
import argparse 
import sys
import os 
from process_dictionary import validate_filepath

_version = None

# placeholder for metadata values
PLACEHOLDER = "### PLACEHOLDER ###"

def user_args() -> None:
    ''' Parses the command line arguments.
    '''

    # argument parser 
    parser = argparse.ArgumentParser(
        prog = 'biomarkerkb_skeleton_data_dictionary_generator',
        usage = 'python skeleton_dictionary.py [options]'
    )

    parser.add_argument('file_path', help = 'filepath of the sample data model JSON')
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

    generate_skeleton_dictionary(options.file_path)

def generate_leaf_metadata() -> dict:
    ''' Generates generic metadata for leaf fields. 

    Returns
    -------
    dict
        The metadata dictionary to be JSON serialized.
    '''
    return {
        'description': PLACEHOLDER,
        'type': PLACEHOLDER,
        'required': {'requirement': PLACEHOLDER},
        'example': [PLACEHOLDER],
        'pattern': PLACEHOLDER,
        'pattern_notes': PLACEHOLDER
    }

def generate_skeleton_for_value(value: str | dict | list) -> dict:
    ''' Recursively processes the skeleton structure based on the type of the value.

    Parameters
    ----------
    value: str, dict, or list
        The field value.
    '''

    # if the value is a dict, process each key-value pair recursively
    if isinstance(value, dict):
        return {k: wrap_with_metadata(k, v) for k, v in value.items()}
    # if value is a list, check if it contains a dict or a primitive 
    elif isinstance(value, list):
        if value and isinstance(value[0], dict):
            return generate_skeleton_for_value(value[0])
        else:
            return generate_leaf_metadata()
    # if primitive value, generate leaf metadata
    else:
        return generate_leaf_metadata()

def wrap_with_metadata(key: str, value: str | dict | list) -> dict:
    ''' Wraps a key-value pair with appropriate metadata structure. 

    Parameters
    ----------
    key: str
        The current field. 
    value: str, dict, or list
        The field value. 
    
    Returns
    -------
    dict
        The metadata dictionary to be JSON serialized. 
    '''

    # if the field is of type array, create the required metadata fields and recursively
    # generate the nested items
    if isinstance(value, list):
        metadata = {
            'description': PLACEHOLDER,
            'type': 'array',
            'required': {'requirement': PLACEHOLDER},
            'items': generate_skeleton_for_value(value)
        }
    # if the field is of type object (or dict), create the required metadata fields and 
    # recursively generate the nested items
    elif isinstance(value, dict):
        metadata = {
            'description': PLACEHOLDER,
            'type': 'object',
            'required': {'requirement': PLACEHOLDER},
            'items': generate_skeleton_for_value(value)
        }
    # if a leaf value, generate the metadata
    else:
        metadata = generate_leaf_metadata()

    return metadata

def generate_skeleton_dictionary(filepath: str) -> None:
    ''' Converts a sample data model into a skeleton data dictionary JSON. 

    Parameters
    ----------
    filepath: str
        Filepath to the sample data model JSON.
    '''

    # read in sample data model JSON 
    with open(filepath, 'r') as f:
        model = json.load(f)

    # recursively create the skeleton data dictionary
    skeleton_dict = {k: wrap_with_metadata(k, v) for k, v in model.items()}

    # Write the skeleton dictionary to a file 
    with open(f'./v{_version}/skeleton_data_dictionary.json', 'w') as f:
        json.dump(skeleton_dict, f, indent=4)

def main() -> None:

    global _version

    with open('../conf.json', 'r') as f:
        config = json.load(f)
        _version = config['version']
    
    # parse the user arguments
    user_args()

if __name__ == '__main__':
    main()