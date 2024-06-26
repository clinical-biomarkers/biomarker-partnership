#!/usr/bin/env/python3
''' Biomarker-Partnership data dictionary processor. Reads in the data dictionary JSON and converts it to 
a JSON validation schema. 

Usage: python process_dictionary.py [options]

    Positional arguments:
        file_path           filepath of the data dictionary JSON to convert

    Optional arguments: 
        -o --output         alternate output path for dumping the schema (for testing)
        -h --help           show the help message and exit
        -v --version        show current version number and exit
'''

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
    parser.add_argument('-o', '--output', type = str, help = 'Output file path', default = None)

    # print out help if script is called with no input arguments
    if len(sys.argv) <= 1:
        sys.argv.append('--help')
    
    options = parser.parse_args()
    # check that the filepath passed is a JSON file
    if not (options.file_path.endswith('.json')):
        raise ValueError(f'Error: Expects JSON file as input.')
    # check if an output path argument was passed
    custom_output_flag = False 
    if options.output:
        custom_output_flag = True
        validate_filepath(os.path.split(options.output)[0], 'output')
    # check that the user passed input filepath exists
    validate_filepath(options.file_path, 'input')

    if custom_output_flag:
        generate_schema_json(options.file_path, custom_output_flag = custom_output_flag, custom_output_path = options.output)
    else:
        generate_schema_json(options.file_path)

def generate_schema_json(filepath: str, custom_output_flag: bool = False, custom_output_path: str = None) -> None:
    ''' Converts the data dictionary into a JSON schema. 

    Parameters
    ----------
    filepath: str
        Filepath to the source data dictionary file. 
    custom_output_flag: bool (default False)
        Flag that determines if a custom output path was passed.
    custom_output_path: str (default None)
        Custom output path to write to. 
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
            'properties': {}
            # 'allOf': []
        }
    }

    # read in data dictionary from user passed filepath
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # iterate through top level items
    for key, value in data.items():
        
        # handle nested object element  
        if value['type'] == 'object':
            property_schema = process_nested_object(value)
        # handle nested array element
        elif value['type'] == 'array':
            property_schema = process_nested_array(value)
        # handle primitive element
        else:
            # build primitive element schema 
            property_schema = {
                'description': value['description'],
                'type': value['type']
            }
            # add examples if available in data dictionary 
            if 'example' in value:
                property_schema['examples'] = value['example']
            # allow null values for non-required fields
            if not value['required']['requirement'] or value['required']['requirement'] == 'conditional': 
                property_schema['type'] = [value['type'], 'null']
            # add regex pattern if available
            if 'pattern' in value:
                property_schema['pattern'] = value['pattern']

        # add to 'required' array if applicable 
        if value['required']['requirement'] and value['required']['requirement'] != 'conditional':
            biomarker_schema['items']['required'].append(key)
    
        # handling conditionals and exclusions
        if value['required']['requirement'] == 'conditional' and len(value['required']['conditionals']) > 0:
            handle_conditionals(key, value, biomarker_schema)
        if value['required']['requirement'] == 'conditional' and len(value['required']['exclusions']) > 0:
            handle_exclusions(key, value, biomarker_schema)
        
        # add the processed property to the schema
        biomarker_schema['items']['properties'][key] = property_schema
    
    # create output path
    if custom_output_flag:
        file_dump_path = custom_output_path
    else:
        file_dump_path = f'{_output_path}/{_output_file}'
    # write out schema
    with open(file_dump_path, 'w') as f:
        json.dump(biomarker_schema, f)

def process_primitive_item(item: dict) -> dict:
    ''' Function to handle generating the schema portion for primitive elements. 

    Parameters
    ----------
    item: dict
        The primitive element to generate the schema for. 
    
    Returns 
    -------
    dict
        Schema portion for the primitive element. 
    '''

    item_schema = {
        'description': item.get('description', ''),
        'type': item['type']
    }
    if ('required' in item and not item['required']['requirement']) or item['required']['requirement'] == 'conditional':
        item_schema['type'] = [item['type'], 'null']
    if 'pattern' in item:
        item_schema['pattern'] = item['pattern']
    if 'example' in item:
        item_schema['examples'] = item['example']
    
    return item_schema

def process_nested_object(nested_data: dict) -> dict:
    ''' Function to handle recursively generating the schema for object type fields and its children elements.

    Parameters
    ----------
    nested_data: dict
        The nested data of type object to recursively process.

    Returns
    -------
    dict
        The schema for the nested object type schema and its children elements. 
    '''

    # handle required nested properties
    properties = nested_data.get('properties', {})
    required_fields = [key for key, value in properties.items() if value['required']['requirement'] and value['required']['requirement'] != 'conditional']

    # build object schema
    nested_object_schema = {
        'description': nested_data['description'],
        'type': nested_data['type'],
        'required': required_fields,
        'properties': {}
    }
    # if not an explicitly required field allow null values
    if not nested_data['required']['requirement'] or nested_data['required']['requirement'] == 'conditional':
        nested_object_schema['type'] = [nested_data['type'], 'null']
    # add patterns if available
    if 'pattern' in nested_data:
        nested_object_schema['pattern'] = nested_data['pattern']

    # loop through children and recursively handle schema generation
    for child_key, child_value in nested_data['properties'].items():
        if child_value['type'] == 'object':
            nested_object_schema['properties'][child_key] = process_nested_object(child_value)
        elif child_value['type'] == 'array':
            nested_object_schema['properties'][child_key] = process_nested_array(child_value)
        else:
            nested_object_schema['properties'][child_key] = process_primitive_item(child_value)
    
    return nested_object_schema

def process_nested_array(nested_data: dict) -> dict:
    ''' Function to handle recursively generating the schema for array type fields and its children elements.

    Parameters
    ----------
    nested_data: dict
        The nested data of type object to recursively process.

    Returns
    -------
    dict
        The schema for the nested object type schema and its children elements. 
    '''

    # build array schema
    nested_array_schema = {
        'description': nested_data['description'],
        'type': 'array',
        'items': {
            "type": "object",
            "required": [],
            "properties": {}
        }
    }
    # if not explicitly required field allow null values
    if not nested_data['required']['requirement'] or nested_data['required']['requirement'] == 'conditional':
        nested_array_schema['type'] = [nested_data['type'], 'null']
    # add patterns if available
    if 'pattern' in nested_data:
        nested_array_schema['pattern'] = nested_data['pattern']
    
    # loop through children and handle recursively generation 
    for property_name, property_data in nested_data['items'].items():
        # process each property according to its type 
        if property_data['type'] == 'object':
            nested_array_schema['items']['properties'][property_name] = process_nested_object(property_data)
        elif property_data['type'] == 'array':
            nested_array_schema['items']['properties'][property_name] = process_nested_array(property_data)
        else:
            nested_array_schema['items']['properties'][property_name] = process_primitive_item(property_data)
        # add to required if applicable
        if property_data.get('required', {}).get('requirement'):
            nested_array_schema['items']['required'].append(property_name)

    # for child_key, child_value in nested_data['items'].items():
    #     if child_value['type'] == 'object':
    #         nested_array_schema['items'][child_key] = process_nested_object(child_value)
    #     elif child_value['type'] == 'array':
    #         nested_array_schema['items'][child_key] = process_nested_array(child_value)
    #     else:
    #         nested_array_schema['items'][child_key] = process_primitive_item(child_value)
    
    return nested_array_schema

def handle_conditionals(property_key: str, property_value: dict, schema: dict) -> None:
    '''
    '''
    pass 

def handle_exclusions(property_key: str, property_value: dict, schema: dict) -> None:
    '''
    '''
    pass 

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