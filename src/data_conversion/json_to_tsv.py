''' Handles the conversion from the JSON data model format to the TSV table format.
'''

import logging 
import traceback
import sys 
import misc_functions as misc_fns

# valid evidence tags for singular fields
SINGLE_EVIDENCE_FIELDS = {
    'biomarker',
    'assessed_biomarker_entity',
    'assessed_biomarker_entity_id',
    'assessed_entity_type',
    'condition',
    'exposure_agent'
}

def json_to_tsv(source_filepath: str, target_filepath: str, tsv_headers: list) -> None:
    ''' Entry point for the JSON -> TSV conversion. 

    Parameters
    ----------
    source_filepath : str
        Filepath to the source JSON file.
    target_filepath : str
        Filepath to the target TSV file to generate. 
    tsv_headers : list
        List of the headers in the TSV file.
    '''

    # get the JSON source data
    json_data = misc_fns.load_json(source_filepath)

    # avoid duplicate evidence values between component and top level evidence
    overall_seen_evidence = set()

    # create the end result TSV content file and write the headers
    tsv_content = '\t'.join(tsv_headers) + '\n'

    ### loop through entries in the JSON data 

    for top_level_entry_idx, top_level_entry in enumerate(json_data):

        # parse top level elements from the entry 
        try:
            biomarker_id = top_level_entry['biomarker_id']
            condition = top_level_entry.get('condition', {}).get('recommended_name', {}).get('name', '')
            condition_id = top_level_entry.get('condition', {}).get('condition_id', '')
            exposure_agent = top_level_entry.get('exposure_agent', {}).get('recommended_name', {}).get('name', '')
            exposure_agent_id = top_level_entry.get('exposure_agent', {}).get('exposure_agent_id', '') 
            best_biomarker_roles_dict = top_level_entry['best_biomarker_role']
            best_biomarker_roles = ';'.join([role['role'] for role in best_biomarker_roles_dict])
            top_level_evidence = top_level_entry.get('evidence_source', [])
        except KeyError as e:
            logging.error(f'KeyError: Error parsing top level element in JSON data:\n\tIndex: {top_level_entry_idx}\n\Error: {e}\n\n{traceback.format_exc()}')
            print(f'KeyError: Error parsing top level element in JSON data:\n\tIndex: {top_level_entry_idx}\n\tError: {e}\n\n{traceback.format_exc()}')
            sys.exit(1)
        except Exception as e:
            logging.error(f'Unexpected error parsing top level elements in JSON data:\n\tIndex: {top_level_entry_idx}\n\tError: {e}\n\n{traceback.format_exc()}')
            print(f'Unexpected error parsing top level elements in JSON data:\n\tIndex: {top_level_entry_idx}\n\tError: {e}\n\n{traceback.format_exc()}')
            sys.exit(1)
        
        ### loop through the biomarker component in the current entry 

        for component_idx, component_entry in enumerate(top_level_entry['biomarker_component']):

            # get the biomarker component elements for the current component entry
            try:
                biomarker = component_entry['biomarker']
                assessed_biomarker_entity = component_entry['assessed_biomarker_entity']['recommended_name']
                assessed_biomarker_entity_id = component_entry['assessed_biomarker_entity_id']
                assessed_entity_type = component_entry['assessed_entity_type']
                component_evidence = component_entry['evidence_source']
            except KeyError as e:
                logging.error(f'KeyError: Error parsing biomarker component element in JSON data:\n\tIndex: {component_idx}\n\Error: {e}\n\n{traceback.format_exc()}')
                print(f'KeyError: Error parsing biomarker component element in JSON data:\n\tIndex: {component_idx}\n\Error: {e}\n\n{traceback.format_exc()}')
                sys.exit(1)
            except Exception as e:
                logging.error(f'Unexpected error parsing biomarker component elements in JSON data:\n\tIndex: {component_idx}\n\tError: {e}\n\n{traceback.format_exc()}')
                print(f'Unexpected error parsing biomarker component elements in JSON data:\n\tIndex: {component_idx}\n\tError: {e}\n\n{traceback.format_exc()}')
                sys.exit(1)
            
            # initialize specimen values to empty strings for the case specimen data is not present
            specimen = ''
            specimen_id = ''
            loinc_code = ''

            # get specimen data if present
            specimens = component_entry.get('specimen', [])

            ### handle case where specimen data is available

            if specimens:

                # loop through specimen array
                for specimen_entry in specimens:
                    # parse specimen data
                    specimen = specimen_entry.get('name', '')
                    specimen_id = specimen_entry.get('specimen_id', '')
                    loinc_code = specimen_entry.get('loinc_code', '')
                    # object/array dictionary for object field tags
                    object_evidence_fields = {
                        'specimen': specimen_id,
                        'loinc_code': loinc_code
                    }

                    # create the row data for everything up until the evidence columns
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
                        best_biomarker_roles,
                        specimen,
                        specimen_id,
                        loinc_code
                    ]

                    ### start evidence data 
                    # start handling component evidence data

                    # set to make sure that evidence values aren't repeated between component and top level evidence in case of overlap
                    seen_evidence = set()

                    # loop through component evidence data
                    for evidence_source in component_evidence:

                        add_evidence_flag = False
                        evidence_columns = [''] * 3

                        # create the evidence source value 
                        evidence_source_value = f"{evidence_source['database']}:{evidence_source['evidence_id']}"
                        # initialize evidence and tag values lists
                        tag_values = []

                        # iterate through evidence tags
                        for tag in evidence_source['tags']:
                            raw_tag, tag_flag = tag_parse(tag, object_evidence_fields)
                            if tag_flag:
                                tag_values.append(raw_tag)
                                add_evidence_flag = True
                        
                        # handle applicable evidence 
                        if add_evidence_flag:
                            evidence_values = aggregate_evidence_values(evidence_source['evidence_list'])
                            seen_evidence.add(evidence_values)
                            overall_seen_evidence.add(evidence_values)
                            evidence_columns = [evidence_source_value, evidence_values, ';'.join(tag_values)]

                        # add evidence columns to row data
                        tsv_content += '\t'.join(row_data) + '\t' + '\t'.join(evidence_columns) + '\n'
                    
                    # start handling top level evidence data
                    
                    # loop through top level evidence data
                    for evidence_source in top_level_evidence:

                        add_evidence_flag = False
                        evidence_columns = [''] * 3

                        evidence_source_value = f"{evidence_source['database']}:{evidence_source['evidence_id']}"
                        tag_values = []

                        for tag in evidence_source['tags']:
                            raw_tag, tag_flag = tag_parse(tag, object_evidence_fields)
                            if tag_flag:
                                tag_values.append(raw_tag)
                                add_evidence_flag = True
                        
                        if add_evidence_flag:
                            evidence_values = aggregate_evidence_values(evidence_source['evidence_list'])
                            # check if evidence has already been captured from component evidence and skip if so
                            if evidence_values in seen_evidence or evidence_values in overall_seen_evidence:
                                continue
                            evidence_columns = [evidence_source_value, evidence_values, ';'.join(tag_values)]

                        tsv_content += '\t'.join(row_data) + '\t' + '\t'.join(evidence_columns) + '\n'

            ### handle case where specimen data is NOT available
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
                    best_biomarker_roles,
                    specimen,
                    specimen_id,
                    loinc_code
                ]
                object_evidence_fields = {
                    'specimen': specimen_id,
                    'loinc_code': loinc_code 
                }

                seen_evidence = set()

                # loop through component evidence data
                for evidence_source in component_evidence:
                    
                    add_evidence_flag = False
                    evidence_columns = [''] * 3
                    evidence_source_value = f"{evidence_source['database']}:{evidence_source['evidence_id']}"
                    tag_values = []

                    for tag in evidence_source['tags']:
                        raw_tag, tag_flag = tag_parse(tag, object_evidence_fields)
                        if tag_flag:
                            tag_values.append(raw_tag)
                            add_evidence_flag = True
                    
                    if add_evidence_flag:
                        evidence_values = aggregate_evidence_values(evidence_source['evidence_list'])
                        seen_evidence.add(evidence_values)
                        overall_seen_evidence.add(evidence_values)
                        evidence_columns = [evidence_source_value, evidence_values, ';'.join(tag_values)]
                    
                    tsv_content += '\t'.join(row_data) + '\t' + '\t'.join(evidence_columns) + '\n'
                
                # loop through top level evidence data
                for evidence_source in top_level_evidence:

                    add_evidence_flag = False
                    evidence_columns = [''] * 3
                    evidence_source_value = f"{evidence_source['database']}:{evidence_source['evidence_id']}"
                    tag_values = []

                    for tag in evidence_source['tags']:
                        raw_tag, tag_flag = tag_parse(tag, object_evidence_fields)
                        if tag_flag:
                            tag_values.append(raw_tag)
                            add_evidence_flag = True
                    
                    if add_evidence_flag:
                        evidence_values = aggregate_evidence_values(evidence_source['evidence_list'])
                        if evidence_values in seen_evidence or evidence_values in overall_seen_evidence:
                            continue
                        evidence_columns = [evidence_source_value, evidence_values, ';'.join(tag_values)]
                    
                    tsv_content += '\t'.join(row_data) + '\t' + '\t'.join(evidence_columns) + '\n'
    
    # write the TSV content to the target file
    with open(target_filepath, 'w') as f:
        f.write(tsv_content)
    logging.info(f'Conversion complete. TSV file written to {target_filepath}')

def tag_parse(tag: dict, object_evidence_fields: dict) -> tuple:
    ''' Parses the evidence data in the JSON data model. 

    Parameters
    ----------
    tag : dict
        Dictionary containing the tag data.
    object_evidence_fields : dict 
        Dictionary containing the object/array evidence fields and their values.
    
    Returns
    -------
    tuple
        Tuple of the raw extracted tag value and a boolean flag indicating whether the evidence is applicable for the current row.
    '''
    add_evidence_flag = False

    # isolate the tag value from the index value
    tag_value = tag['tag'].split(':')[0]

    # check that tag is applicable to current row 
    if tag_value in SINGLE_EVIDENCE_FIELDS:
        add_evidence_flag = True
    if tag_value in set(object_evidence_fields.keys()):
        if tag['tag'][tag['tag'].find(':') + 1:] == object_evidence_fields[tag_value]:
            add_evidence_flag = True
    
    return (tag_value, add_evidence_flag)

def aggregate_evidence_values(evidence_list: list) -> str:
    ''' Aggregates the evidence values into a single string. 

    Parameters
    ----------
    evidence_list : list
        List of evidence values to aggregate.

    Returns
    -------
    str
        String of aggregated evidence values delimited by a semi-colon.
    '''
    evidence_values = []
    for evidence_text in evidence_list:
        evidence_values.append(evidence_text['evidence'])
    return ';'.join(evidence_values)    