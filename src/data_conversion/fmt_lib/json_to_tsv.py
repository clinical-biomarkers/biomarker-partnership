''' Handles the conversion from the JSON data model format to the TSV table format.
'''
from fmt_lib import misc_functions as misc_fns
from fmt_lib import json_to_tsv_utils as utils

def json_to_tsv(source_filepath: str, target_filepath: str, tsv_headers: list, chunk: int = 10_000, log: bool = False) -> None:
    ''' Entry point for the JSON -> TSV conversion.

    Parameters
    ----------
    source_filepath : str
        Filepath to the source JSON file.
    target_filepath : str
        Filepath to the target TSV file to generate. 
    tsv_headers : list
        List of the headers in the TSV file.
    chunk : int (default: 10,000)
        The write checkpoint. 
    log : bool (default: False)
        Whether to print a message when the write checkpoint is hit.

    Raises
    ------
    KeyError
    Exception
    '''
    json_data = misc_fns.load_json(source_filepath)
    tsv_content = '\t'.join(tsv_headers) + '\n'

    ### loop through entries in the JSON data 
    for top_level_entry_idx, top_level_entry in enumerate(json_data):

        if (top_level_entry_idx + 1) % chunk == 0:
            with open(target_filepath, 'a') as f:
                f.write(tsv_content)
            if log:
                misc_fns.print_and_log(f'Write checkpoint hit at row {top_level_entry_idx}, dumping...', 'info')
                print(f'Write checkpoint hit at row {top_level_entry_idx}, dumping...')
            tsv_content = ''

        biomarker_id, condition, condition_id, exposure_agent, exposure_agent_id, best_biomarker_roles, top_level_evidence \
                = utils.extract_top_level_fields(top_level_entry, top_level_entry_idx)
        
        ### loop through the biomarker component in the current entry 
        for component_idx, component_entry in enumerate(top_level_entry['biomarker_component']):

            # avoid duplicate evidence values between components and top level evidence
            overall_seen_evidence = set()

            biomarker, assessed_biomarker_entity, assessed_biomarker_entity_id, assessed_entity_type, component_evidence, specimens \
                    = utils.extract_component_fields(component_entry, component_idx)
                        
            # initialize specimen values to empty strings for the case specimen data is not present
            specimen = ''
            specimen_id = ''
            loinc_code = ''

            ### handle case where specimen data is available
            if specimens:

                # loop through specimen array
                for specimen_entry in specimens:
                    # parse specimen data
                    specimen = specimen_entry.get('name', '')
                    specimen_id = specimen_entry.get('id', '')
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
                    # set to make sure that evidence values aren't repeated between component and top level evidence in case of overlap
                    seen_evidence = set()

                    # loop through component evidence data
                    for evidence_source in component_evidence:

                        add_evidence_flag = False
                        evidence_columns = [''] * 3

                        # create the evidence source value 
                        evidence_source_value = f"{evidence_source['database']}:{evidence_source['id']}"
                        # initialize evidence and tag values lists
                        tag_values = []

                        # iterate through evidence tags
                        for tag in evidence_source['tags']:
                            raw_tag, tag_flag = utils.tag_parse(tag, object_evidence_fields)
                            if tag_flag:
                                tag_values.append(raw_tag)
                                add_evidence_flag = True
                        
                        # handle applicable evidence 
                        if add_evidence_flag:
                            evidence_values = utils.aggregate_evidence_values(evidence_source['evidence_list'])
                            seen_evidence.add(evidence_values)
                            overall_seen_evidence.add(evidence_values)
                            evidence_columns = [evidence_source_value, evidence_values, ';'.join(tag_values)]

                            # add evidence columns to row data
                            tsv_content += '\t'.join(row_data) + '\t' + '\t'.join(evidence_columns) + '\n'
                    
                    # loop through top level evidence data
                    for evidence_source in top_level_evidence:

                        add_evidence_flag = False
                        evidence_columns = [''] * 3

                        evidence_source_value = f"{evidence_source['database']}:{evidence_source['id']}"
                        tag_values = []

                        for tag in evidence_source['tags']:
                            raw_tag, tag_flag = utils.tag_parse(tag, object_evidence_fields, component_idx)
                            if tag_flag:
                                tag_values.append(raw_tag)
                                add_evidence_flag = True
                        
                        if add_evidence_flag:
                            evidence_values = utils.aggregate_evidence_values(evidence_source['evidence_list'])
                            top_level_duplicate_flag = False
                            # check if evidence has already been captured from component evidence,
                            # if so, check if any new tags should be included in existing line or to skip the line entirely 
                            if evidence_values in seen_evidence or evidence_values in overall_seen_evidence:
                                for line_idx, line in enumerate(tsv_content.split('\n')):
                                    # create a dictionary of the line data
                                    line_data = dict(zip(tsv_headers, line.split('\t')))
                                    if line_data['biomarker_id'] not in [None, ''] and line_data['evidence'] == evidence_values and line_data['tag'] != 'tag':
                                        existing_tags = set(line_data['tag'].split(';'))
                                        tag_set = set(tag_values)
                                        if tag_set.issubset(existing_tags):
                                            top_level_duplicate_flag = True
                                        else:
                                            tsv_content = tsv_content.replace(line, line + ';' + ';'.join(tag_set.difference(existing_tags)))
                                            break
                                if top_level_duplicate_flag:
                                    continue
                            else:
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
                    evidence_source_value = f"{evidence_source['database']}:{evidence_source['id']}"
                    tag_values = []

                    for tag in evidence_source['tags']:
                        raw_tag, tag_flag = utils.tag_parse(tag, object_evidence_fields)
                        if tag_flag:
                            tag_values.append(raw_tag)
                            add_evidence_flag = True
                    
                    if add_evidence_flag:
                        evidence_values = utils.aggregate_evidence_values(evidence_source['evidence_list'])
                        seen_evidence.add(evidence_values)
                        overall_seen_evidence.add(evidence_values)
                        evidence_columns = [evidence_source_value, evidence_values, ';'.join(tag_values)]
                    
                    tsv_content += '\t'.join(row_data) + '\t' + '\t'.join(evidence_columns) + '\n'
                
                # loop through top level evidence data
                for evidence_source in top_level_evidence:

                    add_evidence_flag = False
                    evidence_columns = [''] * 3

                    evidence_source_value = f"{evidence_source['database']}:{evidence_source['id']}"
                    tag_values = []

                    for tag in evidence_source['tags']:
                        raw_tag, tag_flag = utils.tag_parse(tag, object_evidence_fields, component_idx)
                        if tag_flag:
                            tag_values.append(raw_tag)
                            add_evidence_flag = True
                    
                    if add_evidence_flag:
                        evidence_values = utils.aggregate_evidence_values(evidence_source['evidence_list'])
                        top_level_duplicate_flag = False
                        # check if evidence has already been captured from component evidence,
                        # if so, check if any new tags should be included in existing line or to skip the line entirely 
                        if evidence_values in seen_evidence or evidence_values in overall_seen_evidence:
                            for line_idx, line in enumerate(tsv_content.split('\n')):
                                # create a dictionary of the line data
                                line_data = dict(zip(tsv_headers, line.split('\t')))
                                if line_data['biomarker_id'] not in [None, ''] and line_data['evidence'] == evidence_values and line_data['tag'] != 'tag':
                                    existing_tags = set(line_data['tag'].split(';'))
                                    tag_set = set(tag_values)
                                    if tag_set.issubset(existing_tags):
                                        top_level_duplicate_flag = True
                                    else:
                                        tsv_content = tsv_content.replace(line, line + ';' + ';'.join(tag_set.difference(existing_tags)))
                                        break
                            if top_level_duplicate_flag:
                                continue
                        else:
                            evidence_columns = [evidence_source_value, evidence_values, ';'.join(tag_values)]
                            tsv_content += '\t'.join(row_data) + '\t' + '\t'.join(evidence_columns) + '\n'
    
    with open(target_filepath, 'a') as f:
        f.write(tsv_content)
    misc_fns.print_and_log(f'Conversion complete. TSV file written to {target_filepath}', 'info')
