''' Handles the conversion from the TSV table format to the JSON data model format.
'''

import json
import csv 
import logging 
import time 
import api_calls as data_api

COMP_SINGULAR_EVIDENCE_FIELDS = {'biomarker', 'assessed_biomarker_entity', 
                                'assessed_biomarker_entity_id', 'assessed_entity_type'}
TOP_LEVEL_EVIDENCE_FIELDS = {'condition', 'exposure_agent', 'best_biomarker_role'}

UNIPROT_RATE_LIMIT_CHECK = 200
UNIPROT_SLEEP_TIME = 1

ADD_CITATION_DATA = True
PUBMED_RATE_LIMIT_CHECK = 10 
PUBMED_SLEEP_TIME = 1

# TODO: multiple specimen issue 

def tsv_to_json(source_filepath: str, target_filepath: str, tsv_headers: list, url_map: dict, name_space_map: dict) -> None:
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
    '''

    header_check = False

    # set rate limit variables to locals for better performance
    uniprot_rate_limit_counter = 0
    uniprot_rate_limit_check = UNIPROT_RATE_LIMIT_CHECK
    uniprot_sleep_time = UNIPROT_SLEEP_TIME
    pubmed_rate_limit_check = PUBMED_RATE_LIMIT_CHECK
    pubmed_sleep_time = PUBMED_SLEEP_TIME

    with open(source_filepath, 'r') as f:
        data = csv.DictReader(f, delimiter = '\t', quotechar = '"')
        # list to hold the resulting converted data
        result_data = []
        # dictionary to hold the biomarker id's and their corresponding entry indices
        biomarker_id_map = {}
        idx = 0

        for row in data:
            
            row = {key: value.strip() if isinstance(value, str) else value for key, value in row.items()}

            # make sure the headers are valid
            if not header_check:
                for header in data.fieldnames:
                    if header not in tsv_headers:
                        logging.error(f'Error: Invalid header {header} in the TSV file.')
                        raise ValueError(f'Error: Invalid header {header} in the TSV file.')
                header_check = True
            
            # object/array dictionary for object field tags
            component_object_evidence_fields = {
                'specimen': row['specimen_id'],
                'loinc_code': row['loinc_code']
            }

            ### build component and evidence level objects 
            comp_evidence_tags, top_evidence_tags = parse_tags(row, component_object_evidence_fields)
            comp_evidence_source = build_evidence_entry(row, comp_evidence_tags, url_map)
            top_evidence_source = build_evidence_entry(row, top_evidence_tags, url_map)

            ### build biomarker component object
            uniprot_count, base_biomarker_component_object = build_base_biomarker_component_entry(row, name_space_map)
            uniprot_rate_limit_counter += uniprot_count
            if uniprot_rate_limit_counter == uniprot_rate_limit_check:
                logging.info(f'UniProt API rate limit check ({uniprot_rate_limit_check})reached, sleeping for {uniprot_sleep_time} seconds...')
                time.sleep(uniprot_sleep_time)
                uniprot_rate_limit_counter = 0

            ### build and add the spcimen entry to the biomarker component object
            biomarker_component = add_specimen_entry(row, base_biomarker_component_object, url_map)

            # add component evidence source to the biomarker component object
            biomarker_component['evidence_source'] = comp_evidence_source

            ### build condition entry 
            condition_entry = build_condition_entry(row, url_map, name_space_map)

            ### build top level entry
            biomarker_entry = build_biomarker_entry(row, biomarker_component, condition_entry, top_evidence_source)

            ### check if the biomarker entry should be added to the result data or if it already exists
            ### if it already exists, the existing component will be updated

            # entry does not exist, add to the result data
            if row['biomarker_id'] not in biomarker_id_map.keys():
                # add to id map and increment index 
                biomarker_id_map[row['biomarker_id']] = idx
                idx += 1 
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
                    if biomarker_component['specimen'] != None:
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
        
        ### add citation data
        if ADD_CITATION_DATA:
            seen_pubmed_set = set()
            # holds the evidence sources to build the citation entries for
            evidence_sources = []
            # get the evidence source data for each biomarker entry
            for entry_idx, entry in enumerate(result_data):
                # get the evidence source data for each biomarker component entry
                for biomarker_componennt_entry in entry['biomarker_component']:
                    # get each component evidence source
                    for evidence_source in biomarker_componennt_entry['evidence_source']:
                        evidence_sources.append((entry_idx, evidence_source))
                        seen_pubmed_set.add(evidence_source['evidence_id'])
                # get the evidence source data for the top level entry
                for evidence_source in entry['evidence_source']:
                    if evidence_source['evidence_id'] not in seen_pubmed_set:
                        evidence_sources.append((entry_idx, evidence_source))
            logging.info(f'Adding citation data for {len(evidence_sources)} evidence sources...')

            pubmed_api_rate_limit_counter = 0
            # get the citation data for each evidence source
            for evidence_source in evidence_sources:
                if evidence_source[1]['database'].lower() != 'pubmed':
                    continue 
                if pubmed_api_rate_limit_counter == pubmed_rate_limit_check:
                    logging.info(f'PubMed API rate limit check ({pubmed_rate_limit_check}) reached, sleeping for {pubmed_sleep_time} second...')
                    time.sleep(pubmed_sleep_time)
                    pubmed_api_rate_limit_counter = 0
                pubmed_data = data_api.get_pubmed_data(evidence_source[1]['evidence_id'])
                if not pubmed_data:
                    continue
                citation_entry = {
                    'citation_title': pubmed_data['title'],
                    'journal': pubmed_data['journal'],
                    'authors': pubmed_data['authors'],
                    'date': pubmed_data['publication_date'],
                    'evidence_source': {
                        'evidence_id': evidence_source[1]['evidence_id'],
                        'database': evidence_source[1]['database'].title(),
                        'url': evidence_source[1]['url']
                    },
                    'reference': []
                }
                result_data[evidence_source[0]]['citation'].append(citation_entry)
                pubmed_api_rate_limit_counter += 1

            logging.info(f'Finished adding citation data!')
        
        with open(target_filepath, 'w') as f:
            json.dump(result_data, f, indent = 4)

def build_biomarker_entry(row: list, biomarker_component_object: dict, condition_entry: dict, top_evidence_source: list) -> dict:
    ''' Builds the top level biomarker entry.

    Parameters
    ----------
    row : list
        The current row in the TSV file being processed.
    biomarker_component_object : dict
        The biomarker component object to add to the biomarker entry.
    condition_entry : dict
        The condition entry to add to the biomarker entry.
    top_evidence_source : list
        List of the top level evidence sources to add to the biomarker entry.
    
    Returns
    -------
    dict
        Dictionary containing the biomarker entry.
    '''
    best_biomarker_roles = [{'role': role} for role in row['best_biomarker_role'].split(';')]
    biomarker_entry = {
        'biomarker_id': row['biomarker_id'],
        'biomarker_component': [biomarker_component_object],
        'best_biomarker_role': best_biomarker_roles,
        'condition': condition_entry,
        'evidence_source': top_evidence_source,
        'citation': []
    }

    return biomarker_entry

def build_condition_entry(row: list, url_map: dict, name_space_map: dict) -> dict:
    ''' If applicable, builds the condition entry. 

    Parameters
    ----------
    row : list
        The current row in the TSV file being processed.
    url_map : dict
        Dictionary that provides mappings for name space's to base URL's. This assists with URL construction.
    name_space_map : dict
        Dictionary that provides mappings for name space acronym's to full name space names.
    
    Returns
    -------
    dict
        Dictionary containing the condition entry.
    '''
    condition = None
    if row['condition']:
        # check for full resource name 
        condition_name_space = row['condition_id'].split(':')[0].lower()
        if condition_name_space in set(url_map.keys()):
            condition_resource = name_space_map[condition_name_space].title()
        else:
            logging.info(f'Warning: Condition name space {condition_name_space} not in the name space map.')
            condition_resource = condition_name_space
        # try to build condition url
        condition_url = None
        if condition_name_space in set(url_map.keys()):
            condition_url = f"{url_map[condition_name_space]}{row['condition_id'].split(':')[1]}"
        else:
            logging.info(f'Warning: Condition name space {condition_name_space} not in the url map.')
        # build entry
        condition = {
            'condition_id': row['condition_id'],
            'recommended_name': {
                'condition_id': row['condition_id'],
                'name': row['condition'],
                'description': None,
                'resource': condition_resource,
                'url': condition_url
            },
            'synonyms': []
        }

        # handle getting the condition description and synonyms
        if condition_name_space == 'doid':
            doid_data = data_api.get_doid_data(row['condition_id'].split(':')[1])
            if doid_data:
                condition['recommended_name']['description'] = doid_data['description']
                synonym_entries = []
                for synonym in doid_data['synonyms']:
                    synonym_entry = {
                        'synonym_id': row['condition_id'],
                        'name': synonym,
                        'resource': condition_resource,
                        'url': condition_url
                    }
                    synonym_entries.append(synonym_entry)
                condition['synonyms'] = synonym_entries 
    
    return condition

def add_specimen_entry(row: list, biomarker_component_object: dict, url_map: dict) -> dict:
    ''' Builds and appends the specimen entry for the biomarker component object.

    Parameters
    ----------
    row : list
        The current row in the TSV file being processed.
    biomarker_component_object : dict
        The biomarker component object to add the specimen entry to.
    url_map : dict
        Dictionary that provides mappings for name space's to base URL's. This assists with URL construction.
    
    Returns
    -------
    dict
        Dictionary containing the specimen entry.
    '''
    biomarker_component_object['specimen'] = []

    specimen_url = None 
    specimen_database = None
    specimen = {}
    if row['specimen']:
        specimen_database = row['specimen_id'].split(':')[0].lower()
        if specimen_database in set(url_map.keys()):
            specimen_url = f"{url_map[specimen_database]}{row['specimen_id'].split(':')[1]}"
        else:
            logging.info(f'Warning: Specimen database {specimen_database} not in the url map.')
    if row['specimen'] or row['loinc_code']:
        specimen = {
            'name': row.get('specimen', ''),
            'specimen_id': row.get('specimen_id', ''),
            'name_space': specimen_database.title() if specimen_database else '',
            'url': specimen_url if specimen_url else '',
            'loinc_code': row.get('loinc_code', '')
        }
    biomarker_component_object['specimen'].append(specimen)
    return biomarker_component_object

def build_base_biomarker_component_entry(row: list, name_space_map: dict) -> tuple:
    ''' Builds a the base for a biomarker component entry. Everything up until the specimen and 
    evidence source fields.

    Parameters
    ----------
    row : list
        The current row in the TSV file being processed.
    name_space_map : dict
        Dictionary that provides mappings for name space acronym's to full name space names.
    
    Returns
    -------
    tuple
        Returns an integer used for uniprot api rate limit control and the dictionary containing the biomarker component entry.
    '''
    uniprot_call_counter = 0
    assessed_entity_type = row['assessed_entity_type'].lower().strip()
    assessed_entity_type_name_space = row['assessed_biomarker_entity_id'].split(':')[0].lower()
    synonyms = []
    if assessed_entity_type == 'protein' and assessed_entity_type_name_space in set(name_space_map.keys()):
        if name_space_map[assessed_entity_type_name_space] == 'uniprot':
            uniprot_data = data_api.get_uniprot_data(row['assessed_biomarker_entity_id'].split(':')[1])
            uniprot_call_counter = 1
            if uniprot_data:
                synonyms = [{'synonym': synonym} for synonym in uniprot_data['synonyms']]

    entry = {
        'biomarker': row['biomarker'],
        'assessed_biomarker_entity': {
            'recommended_name': row['assessed_biomarker_entity'],
            'synonyms': synonyms 
        },
        'assessed_biomarker_entity_id': row['assessed_biomarker_entity_id'],
        'assessed_entity_type': row['assessed_entity_type']
    }

    return uniprot_call_counter, entry 

def build_evidence_entry(row: list, tag_list: list, url_map: dict) -> list:
    ''' Builds the evidence entry.

    Parameters
    ----------
    row : list
        The current row in the TSV file being processed.
    tag_list : list
        List of the evidence tags.
    url_map : dict
        Dictionary that provides mappings for name space's to base URL's. This assists with URL construction.
    
    Returns
    -------
    list
        List of the evidence entry. Returns an empty list if no tags passed. 
    '''

    evidence_entry = []
    if tag_list:
        evidence_database = row['evidence_source'].split(':')[0].lower()
        evidence_id = row['evidence_source'].split(':')[1]
        if evidence_database in set(url_map.keys()):
            evidence_url = f"{url_map[evidence_database]}{evidence_id}"
        else:
            logging.info(f'Warning: Evidence database {evidence_database} not in the url map.')
            evidence_url = None 
        # build evidence object
        evidence_entry.append(
            {
                'evidence_id': evidence_id,
                'database': evidence_database.title(),
                'url': evidence_url,
                'evidence_list': [{'evidence': evidence_txt.strip()} for evidence_txt in row['evidence'].split(';|')],
                'tags': tag_list
            }
        )
    
    return evidence_entry


def parse_tags(row: list, component_object_evidence_fields: dict) -> tuple:
    ''' Parses the tag string and returns the component and top level evidence tag information formatted per the 
    JSON data model.

    Parameters
    ----------
    row : list
        The current row in the TSV file being processed.
    component_object_evidence_fields : dict
        Dictionary containing the component object evidence fields and their corresponding values.
    
    Returns
    -------
    tuple
        Tuple containing the component and top level evidence tags.
    '''
    tags = [tag.strip() for tag in row['tag'].split(';')]
    comp_evidence_tags = []
    top_evidence_tags = []
    for tag in tags:
        if tag in COMP_SINGULAR_EVIDENCE_FIELDS:
            comp_evidence_tags.append(
                {
                    'tag': tag
                }
            )
        if tag.split(':')[0].lower() in set(component_object_evidence_fields.keys()):
            comp_evidence_tags.append(
                {
                    'tag': f"{tag.split(':')[0].lower()}:{component_object_evidence_fields[tag.split(':')[0].lower()]}"
                }
            )
        if tag in TOP_LEVEL_EVIDENCE_FIELDS:
            top_evidence_tags.append(
                {
                    'tag': tag
                }
            )
    
    return comp_evidence_tags, top_evidence_tags
