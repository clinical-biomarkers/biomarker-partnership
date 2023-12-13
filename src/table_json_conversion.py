#!/usr/bin/env/python3
''' Biomarker-Partnership data converter. Can convert table formatted data to the data model JSON 
or JSON data to the table format. Script is not agnostic to the formatting of the current table 
format/structure or the current data model JSON schema. If those are updated in the future, this 
script needs to be updated. 

Usage: table_json_conversion.py [options]

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

import json 
import argparse 
import sys 
import os 

_version = None
TSV_HEADERS = ['biomarker_id', 'biomarker', 'assessed_biomarker_entity', 'assessed_biomarker_entity_id', 
            'assessed_entity_type', 'condition', 'condition_id', 'exposure_agent', 'exposure_agent_id', 
            'best_biomarker_role', 'specimen', 'specimen_id', 'loinc_code', 'evidence_source', 'evidence', 'tag']

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

def user_args() -> None:
    ''' Parses the command line arguments.
    '''

    # argument parser 
    parser = argparse.ArgumentParser(
        prog = 'biomarkerdb_data_converter',
        usage = 'python table_json_conversion.py [options]'
    )

    # add arguments 
    parser.add_argument('source_filepath', help = 'filepath of the source file to convert (JSON or TSV)')
    parser.add_argument('target_filepath', help = 'filepath of the target filepath to generate (JSON or TSV)')

    # print out help if script is called without enough  
    if len(sys.argv) <= 2:
        sys.argv.append('--help')
    
    options = parser.parse_args() 
    # check that the filepaths exist
    validate_filepath(options.source_filepath, 'input')
    validate_filepath(os.path.split(options.target_filepath)[0], 'output')
    # check that the source and target file types follow correct guidelines 
    if options.source_filepath.endswith('.json'): 
        if not (options.target_filepath.endswith('.tsv')):
            raise ValueError(f'Incorrect target_filepath file type for source type of json, expects tsv.')
        # if the right filetypes were passed, continue to processing
        json_to_tsv(options.source_filepath, options.target_filepath)
    if options.source_filepath.endswith('.tsv'):
        if not (options.target_filepath.endswith('.json')):
            raise ValueError(f'Incorrect target_filepath file type for source type of tsv, expects json.')
        # if the right filetypes were passed, continue to processing
        tsv_to_json(options.source_filepath, options.target_filepath)

def json_to_tsv(source: str, target: str) -> None:
    ''' Logic to convert the source JSON file to a TSV format.

    Parameters
    ----------
    source: str 
        Filepath to the source file of type JSON. 
    target: str 
        Filepath to the output file of type TSV. 
    '''

    # get json source data 
    with open(source, 'r') as f:
        data = json.load(f)

    tsv_content = '\t'.join(TSV_HEADERS) + '\n'

    # loop through top level array 
    for entry in data: 
        
        # get top level elements
        biomarker_id = entry.get('biomarker_id', '')
        condition = entry.get('condition', {}).get('recommended_name', {}).get('name', '')
        condition_id = entry.get('condition', {}).get('condition_id', '')
        exposure_agent = entry.get('exposure_agent', {}).get('recommended_name', {}).get('name', '')
        exposure_agent_id = entry.get('exposure_agent', {}).get('exposure_agent_id', '')
        best_biomarker_role = entry['best_biomarker_role']

        # loop through biomarker component
        for component in entry['biomarker_component']:

            biomarker = component['biomarker']
            assessed_biomarker_entity = component['assessed_biomarker_entity']['recommended_name']
            assessed_biomarker_entity_id = component['assessed_biomarker_entity_id']
            assessed_entity_type = component['assessed_entity_type']

            specimens = component.get('specimen', [])
            if specimens:
                # loop through specimen array 
                for specimen_entry in component.get('specimen', []):
                        
                    specimen = specimen_entry.get('name', '')
                    specimen_id = specimen_entry.get('id', '')
                    loinc_code = specimen_entry.get('loinc_code', '')
                
                    row_data = [
                        biomarker_id,
                        biomarker,
                        assessed_biomarker_entity,
                        assessed_biomarker_entity_id,
                        assessed_entity_type,
                        condition,
                        condition_id,
                        exposure_agent,
                        exposure_agent_id,
                        best_biomarker_role,
                        specimen,
                        specimen_id,
                        loinc_code
                    ]
            else:
                row_data = [
                        biomarker_id,
                        biomarker,
                        assessed_biomarker_entity,
                        assessed_biomarker_entity_id,
                        assessed_entity_type,
                        condition,
                        condition_id,
                        exposure_agent,
                        exposure_agent_id,
                        best_biomarker_role,
                        '',
                        '',
                        ''
                    ]
            
            tsv_content += '\t'.join(row_data) + '\n'
    
    with open(target, 'w') as f:
        f.write(tsv_content)


def tsv_to_json(source: str, target: str) -> None:
    ''' Logic to convert the source TSV file to a JSON format.

    Parameters
    ----------
    source: str 
        Filepath to the source file of type TSV.
    target: str 
        Filepath to the output file of type JSON. 
    '''

def main() -> None: 

    global _version 
    # grab version number 
    with open('../conf.json', 'r') as f:
        config = json.load(f) 
        _version = config['version']
    
    # parse the user arguments
    user_args() 

if __name__ == '__main__': 
    main() 