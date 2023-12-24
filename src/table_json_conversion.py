#!/usr/bin/env/python3
''' Biomarker-Partnership data converter. Can convert table formatted data to the data model JSON 
or JSON data to the table format. Script is not agnostic to the formatting of the current table 
format/structure or the current data model JSON schema. If those are updated in the future, this 
script needs to be updated. 

Currently written for the v0.3 data model schema. 

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
import logging

_CONF_KEY = 'format_conversion'
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

    # log the user passed arguments 
    logging.info(f'Arguments passed:\nsource_filepath = {options.source_filepath}\ntarget_filepath = {options.target_filepath}')

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
    ''' Logic to convert the source JSON file to a TSV format. The function unrolls the JSON data model format
    into a table format. Because of the nested/hierarchical nature of the data model format, each entry gets
    unrolled into potentially many rows in the table (TSV) format. Essentially generates each permuation of the 
    JSON data based on some conditional logic (such as making sure evidence values are only added for rows where
    the tags fit).

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

    # create the header row for the TSV file
    tsv_content = '\t'.join(TSV_HEADERS) + '\n'

    # loop through top level array 
    for idx, entry in enumerate(data): 
        
        # get top level elements
        biomarker_id = entry.get('biomarker_id', '')
        condition = entry.get('condition', {}).get('recommended_name', {}).get('name', '')
        condition_id = entry.get('condition', {}).get('condition_id', '')
        exposure_agent = entry.get('exposure_agent', {}).get('recommended_name', {}).get('name', '')
        exposure_agent_id = entry.get('exposure_agent', {}).get('exposure_agent_id', '')
        best_biomarker_role = entry['best_biomarker_role']

        # loop through biomarker component
        for comp_idx, component in enumerate(entry['biomarker_component']):

            # get biomarker component elements for the current component entry
            biomarker = component['biomarker']
            assessed_biomarker_entity = component['assessed_biomarker_entity']['recommended_name']
            assessed_biomarker_entity_id = component['assessed_biomarker_entity_id']
            assessed_entity_type = component['assessed_entity_type']
            # set specimen values to empty strings for the case specimen data is not provided
            specimen = ''
            specimen_id = ''
            loinc_code = ''

            # get evidence from component 
            component_evidence = component.get('evidence_source', [])
            # get top level evidence    
            top_level_evidence = entry.get('evidence_source', [])
            # singular evidence fields
            single_evidence_fields = {
                'biomarker',
                'assessed_biomarker_entity',
                'assessed_biomarker_entity_id',
                'assessed_entity_type',
                'condition',
                'exposure_agent',
                'best_biomarker_role'
            }

            # get the component specimen data
            specimens = component.get('specimen', [])
            # handle case where specimen data is available
            if specimens:
                # loop through specimen array 
                for specimen_idx, specimen_entry in enumerate(specimens):
                        
                    # parse specimen data
                    specimen = specimen_entry.get('name', '')
                    specimen_id = specimen_entry.get('specimen_id', '')
                    loinc_code = specimen_entry.get('loinc_code', '')
                    # set object/array dictionary that evidence can tag to
                    object_evidence_fields = {
                        'specimen': specimen_id,
                        'loinc_code': loinc_code
                    }

                    # set the row data for everything up until the evidence columns
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

                    # initialize evidence columns to empty strings 
                    evidence_columns = ['', '', '']
                    # flag to confirm component evidence is applicable for current row data
                    add_comp_evidence_values_flag = False
                    # flag to confirm top level evidence is applicable for current row data 
                    add_top_level_evidence_values_flag = False
                    # set to make sure that evidence values aren't repeated between component and top level evidence in case of duplicates
                    seen_evidence = set()
                    
                    # loop through component evidence data
                    for evidence_source in component_evidence:
                        # create evidence source 
                        evidence_source_value = f"{evidence_source['database']}:{evidence_source['evidence_id']}"
                        # initialize evidence values and tag values to empty lists
                        evidence_values = []
                        tag_values = []

                        # iterate through tags
                        for tag in evidence_source['tags']:
                            # handle evidence for singlular field tags
                            if tag['tag'].split(':')[0] in single_evidence_fields:
                                # if tag is a valid singular field tag add to tag values
                                tag_values.append(tag['tag'])
                                add_comp_evidence_values_flag = True
                            # handle evidence for array/object field tags 
                            if tag['tag'].split(':')[0] in set(object_evidence_fields.keys()):
                                # if tag specifies an array field, make sure it is applicable to current row data
                                if tag['tag'][tag['tag'].find(':') + 1:] == object_evidence_fields[tag['tag'].split(':')[0]]:
                                    tag_values.append(tag['tag'])
                                    add_comp_evidence_values_flag = True
                        
                        if add_comp_evidence_values_flag:
                            # if evidence is applicable, loop through evidence list and add to list 
                            for evidence_text in evidence_source['evidence_list']:
                                evidence_values.append(evidence_text['evidence'])
                            # add evidence to set for reference in top level evidence handling
                            seen_evidence.add(' '.join(evidence_values))
                        
                        # reset flag for next evidence entry 
                        add_comp_evidence_values_flag = False
                            
                        # populate evidence columns and add to current row
                        evidence_columns = [evidence_source_value, ' '.join(evidence_values), '; '.join(tag_values)]
                        tsv_content += '\t'.join(row_data) + '\t' + '\t'.join(evidence_columns) + '\n'
                    
                    # re-initialize evidence column values to empty strings 
                    evidence_columns = ['', '', '']

                    # loop through top level evidence data
                    for evidence_source in top_level_evidence:
                        evidence_source_value = f"{evidence_source['database']}:{evidence_source['evidence_id']}"
                        evidence_values = []
                        tag_values = []

                        # iterate through tags
                        for tag in evidence_source['tags']:
                            # handle evidence for singular field tags
                            if tag['tag'].split(':')[0] in single_evidence_fields:
                                tag_values.append(tag['tag'])
                                add_top_level_evidence_values_flag = True
                            # handle evidence for array/object field tags
                            if tag['tag'].split(':')[0] in set(object_evidence_fields.keys()):
                                if tag['tag'][tag['tag'].find(':') + 1:] == object_evidence_fields[tag['tag'].split(':')[0]]:
                                    tag_values.append(tag['tag'])
                                    add_top_level_evidence_values_flag = True
                        
                        # add evidence if applicable
                        if add_top_level_evidence_values_flag:
                            # if evidence is applicable, loop through evidence list and add to list
                            for evidence_text in evidence_source['evidence_list']:
                                evidence_values.append(evidence_text['evidence'])
                            # check if evidence is already captured from component evidence
                            if ' '.join(evidence_values) in seen_evidence:
                                continue
                        
                        # reset flag for next evidence entry
                        add_top_level_evidence_values_flag = False 

                        # populate evidence columns and add to current row
                        evidence_columns = [evidence_source_value, ' '.join(evidence_values), '; '.join(tag_values)]
                        tsv_content += '\t'.join(row_data) + '\t' + '\t'.join(evidence_columns) + '\n'

            # handle case where specimen data is not available
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
                        specimen,
                        specimen_id,
                        loinc_code
                    ]
                
                object_evidence_fields = {
                    'specimen': specimen_id,
                    'loinc_code': loinc_code
                }
                evidence_columns = ['', '', '']
                add_comp_evidence_values_flag = False
                add_top_level_evidence_values_flag = False
                seen_evidence = set()
                
                # loop through component evidence data
                for evidence_source in component_evidence:
                    evidence_source_value = f"{evidence_source['database']}:{evidence_source['id']}"
                    evidence_values = []
                    tag_values = []

                    # iterate through tags
                    for tag in evidence_source['tags']:
                        # handle evidence for singlular field tags
                        if tag['tag'].split(':')[0] in single_evidence_fields:
                            tag_values.append(tag['tag'])
                            add_comp_evidence_values_flag = True
                        # handle evidence for array/object field tags 
                        if tag['tag'].split(':')[0] in set(object_evidence_fields.keys()):
                            if tag['tag'][tag['tag'].find(':') + 1:] == object_evidence_fields[tag['tag'].split(':')[0]]:
                                tag_values.append(tag['tag'])
                                add_comp_evidence_values_flag = True
                    
                    # add evidence if applicable
                    if add_comp_evidence_values_flag:
                        for evidence_text in evidence_source['evidence_list']:
                            evidence_values.append(evidence_text['evidence'])
                        seen_evidence.add(' '.join(evidence_values))
                    
                    add_comp_evidence_values_flag = False
                    evidence_columns = [evidence_source_value, ' '.join(evidence_values), '; '.join(tag_values)]
                    tsv_content += '\t'.join(row_data) + '\t' + '\t'.join(evidence_columns) + '\n'
                
                # re-initialize evidence column values to empty strings
                evidence_columns = ['', '', '']

                # loop through top level evidence data
                for evidence_source in top_level_evidence:
                    evidence_source_value = f"{evidence_source['database']}:{evidence_source['evidence_id']}"
                    evidence_values = []
                    tag_values = []

                    # iterate through tags
                    for tags in evidence_source['tags']:
                        # handle evidence for singular field tags
                        if tag['tag'].split(':')[0] in single_evidence_fields:
                            tag_values.append(tag['tag'])
                            add_top_level_evidence_values_flag = True
                        # handle evidence for array/object field tags
                        if tag['tag'].split(':')[0] in set(object_evidence_fields.keys()):
                            if tag['tag'][tag['tag'].find(':') + 1:] == object_evidence_fields[tag['tag'].split(':')[0]]:
                                tag_values.append(tag['tag'])
                                add_top_level_evidence_values_flag = True
                    
                    # add evidence if applicable 
                    if add_top_level_evidence_values_flag:
                        for evidence_text in evidence_source['evidence_list']:
                            evidence_values.append(evidence_text['evidence'])
                        if ' '.join(evidence_values) in seen_evidence:
                            continue
                    
                    add_top_level_evidence_values_flag = False
                    evidence_columns = [evidence_source_value, ' '.join(evidence_values), '; '.join(tag_values)]
                    tsv_content += '\t'.join(row_data) + '\t' + '\t'.join(evidence_columns) + '\n'
            
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

def setup_logging(log_path: str) -> None:
    ''' Configures the logger. 

    Parameters
    ----------
    log_path: str 
        The path to the log file.
    '''
    logging.basicConfig(filename = log_path, level = logging.INFO,
                        format = '%(asctime)s - %(levelname)s - %(message)s')

def main() -> None: 

    global _version 
    # grab version number 
    with open('../conf.json', 'r') as f:
        config = json.load(f) 
        _version = config['version']
        log_path = config[_CONF_KEY]['log_path']
    
    # make sure directory to dump logs in exists
    validate_filepath(os.path.split(log_path)[0], 'output')
    setup_logging(log_path)

    # log start delimiter for a new run
    logging.info('################################## Start ##################################')
    
    # parse the user arguments
    user_args() 

    # log the end delmiter for the run
    logging.info('---------------------------------- End ----------------------------------')

if __name__ == '__main__': 
    main() 