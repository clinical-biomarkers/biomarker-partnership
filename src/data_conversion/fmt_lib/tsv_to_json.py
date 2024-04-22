''' Handles the conversion from the TSV table format to the JSON data model format.
'''

import csv 
from fmt_lib import misc_functions as misc_fns
from fmt_lib import tsv_to_json_utils as utils
from fmt_lib import synonym_utils as syn_utils

ADD_CITATION_DATA = True

def tsv_to_json(source_filepath: str, target_filepath: str, tsv_headers: list, url_map: dict, name_space_map: dict, chunk: int = 10_000, log: bool = False, metadata: bool = True) -> None:
    ''' Entry point for the TSV -> JSON conversion.

    Parameters
    ----------
    source_filepath : str
        Filepath to the source TSV file.
    target_filepath : str
        Filepath to the target JSON file to generate.
    tsv_headers : list
        List of the headers in the TSV file.
    url_map : dict
        Dictionary that provides mappings for name space's to base URL's. This assists with URL construction.
    name_space_map : dict
        Dictionary that provides mappings for name space acronym's to full name space names.
    chunk : int (default: 10,000)
        Log checkpoint.
    log : bool (default: False)
        Whether to print a message when the log checkpoint is hit.
    metadata : bool (default: True)
         Whether to attempt automatic metadata retrieval.
    '''

    f = open(source_filepath, 'r')
    data = csv.DictReader(f, delimiter = '\t', quotechar = '"')
    for header in data.fieldnames:
        if header not in tsv_headers:
            misc_fns.print_and_log(f'Error: Invalid header \'{header}\' in the TSV file.', 'error')
            raise ValueError(f'Error: Invalid header \'{header}\' in the TSV file.')
    result_data: list = []
    temp_files_list: list[str] = []
    biomarker_id_map: dict = {}
    curr_id_idx = 0

    for row_idx, row in enumerate(data):

        if (row_idx + 1) % chunk == 0:
            if log:
                misc_fns.print_and_log(f'Log checkpoint at row {row_idx}...', 'info')
                print(f'Log checkpoint hit at row {row_idx}...')

        row = {key: value.strip() if isinstance(value, str) else value for key, value in row.items()}

        # object/array dictionary for object field tags
        component_object_evidence_fields = {
            'specimen': row['specimen_id'],
            'loinc_code': row['loinc_code']
        }

        ### build component and evidence level objects 
        comp_evidence_tags, top_evidence_tags = utils.parse_tags(row, component_object_evidence_fields)
        comp_evidence_source = utils.build_evidence_entry(row, comp_evidence_tags, url_map)
        top_evidence_source = utils.build_evidence_entry(row, top_evidence_tags, url_map)

        ### build biomarker component object
        api_counts, base_biomarker_component_object = utils.build_base_biomarker_component_entry(row, name_space_map, metadata)
        if metadata:
            syn_utils.handle_rate_limits(api_counts)

        ### build and add the spcimen entry to the biomarker component object
        biomarker_component = utils.add_specimen_entry(row, base_biomarker_component_object, url_map)

        # add component evidence source to the biomarker component object
        biomarker_component['evidence_source'] = comp_evidence_source

        ### build condition entry 
        condition_entry = utils.build_condition_entry(row, url_map, name_space_map, metadata)

        ### build top level entry
        biomarker_entry = utils.build_biomarker_entry(row, biomarker_component, condition_entry, top_evidence_source)

        ### check if the biomarker entry should be added to the result data or if it already exists
        ### if it already exists, the existing component will be updated

        # entry does not exist, add to the result data
        if row['biomarker_id'] not in biomarker_id_map.keys():
            # add to id map and increment index 
            biomarker_id_map[row['biomarker_id']] = curr_id_idx
            curr_id_idx += 1 
            # add entry to the result data
            result_data.append(biomarker_entry)
        
        # entry already exists, update as appropriate
        else:
            existing_entry_index = biomarker_id_map[row['biomarker_id']]
            existing_entry = result_data[existing_entry_index]
            
            # find the component element that matches the current component object
            component_to_update_idx = -1 
            for component_idx, existing_component in enumerate(existing_entry['biomarker_component']):
                component_found = (biomarker_component['biomarker'] == existing_component['biomarker']) and \
                                    (biomarker_component['assessed_biomarker_entity']['recommended_name'] == existing_component['assessed_biomarker_entity']['recommended_name']) and \
                                    (biomarker_component['assessed_biomarker_entity_id'] == existing_component['assessed_biomarker_entity_id']) and \
                                    (biomarker_component['assessed_entity_type'] == existing_component['assessed_entity_type'])
                if component_found:
                    component_to_update_idx = component_idx
                    break
            
            # if the component was not found, add the entire current biomarker component as a new entry
            if component_to_update_idx == -1:
                result_data[existing_entry_index]['biomarker_component'].append(biomarker_component)
            # if the component was found, update the existing component
            else:
                # add new specimen entry if applicable
                if biomarker_component['specimen'] is not None:
                    add_specimen = True
                    # determine whether the the specimen entry should be added or if it already exists
                    specimen_list = existing_entry['biomarker_component'][component_to_update_idx]['specimen']
                    for existing_specimen in specimen_list:
                        specimen_found = existing_specimen in biomarker_component['specimen']
                        # specimen_found = (biomarker_component['specimen']['name'] == existing_specimen['name']) and \
                        #                    (biomarker_component['specimen']['loinc_code'] == existing_specimen['loinc_code']) 
                        if specimen_found:
                            add_specimen = False
                            break
                    if add_specimen:
                        for specimen_to_add in biomarker_component['specimen']:
                            result_data[existing_entry_index]['biomarker_component'][component_to_update_idx]['specimen'].append(specimen_to_add)

                # add new component evidence source entry if applicable
                if comp_evidence_source != []:
                    add_comp_evidence = True
                    for existing_comp_evidence in existing_entry['biomarker_component'][component_to_update_idx]['evidence_source']:
                        if comp_evidence_source[0] == existing_comp_evidence:
                            add_comp_evidence = False
                            break
                        existing_comp_evidence_no_tags = {k: v for k, v in existing_comp_evidence.items() if k != 'tags'}
                        existing_comp_tags = [tag['tag'] for tag in existing_comp_evidence['tags']]
                        new_comp_evidence_no_tags = {k: v for k, v in comp_evidence_source[0].items() if k != 'tags'}
                        new_comp_tags = [tag['tag'] for tag in comp_evidence_source[0]['tags']]
                        if existing_comp_evidence_no_tags == new_comp_evidence_no_tags:
                            add_comp_evidence = False
                            # handle case where evidence matches but tags do not 
                            for tag in new_comp_tags:
                                if tag not in existing_comp_tags:
                                    existing_comp_evidence['tags'].append({'tag': tag})
                        else:
                            continue
                    if add_comp_evidence:
                        result_data[existing_entry_index]['biomarker_component'][component_to_update_idx]['evidence_source'].append(comp_evidence_source[0])

            # handle adding top level evidence if applicable
            if top_evidence_source != []:
                add_top_evidence = True
                for existing_top_evidence in existing_entry['evidence_source']:
                    if top_evidence_source[0] == existing_top_evidence:
                        add_top_evidence = False
                        break
                    existing_top_evidence_no_tags = {k: v for k, v in existing_top_evidence.items() if k != 'tags'}
                    existing_top_tags = [tag['tag'] for tag in existing_top_evidence['tags']]
                    new_top_evidence_no_tags = {k: v for k, v in top_evidence_source[0].items() if k != 'tags'}
                    new_top_tags = [tag['tag'] for tag in top_evidence_source[0]['tags']]
                    if existing_top_evidence_no_tags == new_top_evidence_no_tags:
                        add_top_evidence = False
                        # handle case where evidence matches but tags do not 
                        for tag in new_top_tags:
                            if tag not in existing_top_tags:
                                existing_top_evidence['tags'].append({'tag': tag})
                    else:
                        continue
                if add_top_evidence:
                    result_data[existing_entry_index]['evidence_source'].append(top_evidence_source[0])
    
    total_api_calls = syn_utils.get_total_api_calls()
    for resource, count in total_api_calls.items():
        misc_fns.print_and_log(f'Total {resource} API calls: {count}', 'info')
    
    if ADD_CITATION_DATA:
        result_data = utils.add_citation_data(result_data)
    
    misc_fns.write_json(target_filepath, result_data)

    f.close()
