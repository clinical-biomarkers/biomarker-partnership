import tempfile
import os
import json
from typing import Union
from fmt_lib import misc_functions as misc_fns
from fmt_lib import synonym_utils as syn_utils
from fmt_lib import api_calls as data_api

COMP_SINGULAR_EVIDENCE_FIELDS = {'biomarker', 'assessed_biomarker_entity', 
                                'assessed_biomarker_entity_id', 'assessed_entity_type'}
TOP_LEVEL_EVIDENCE_FIELDS = {'condition', 'exposure_agent', 'best_biomarker_role'}

def build_base_biomarker_component_entry(row: dict, name_space_map: dict, metadata: bool = True) -> tuple:
    ''' Builds a the base for a biomarker component entry. Everything up until the specimen and 
    evidence source fields.

    Parameters
    ----------
    row : dict
        The current row in the TSV file being processed.
    name_space_map : dict
        Dictionary that provides mappings for name space acronym's to full name space names.
    metadata : bool (default: True)
         Whether to attempt automatic metadata retrieval.
    
    Returns
    -------
    tuple
        Returns a dictionary used for api rate limit control and the dictionary containing the biomarker component entry.
    '''
    api_call_counter = {value: 0 for _, value in name_space_map.items()}
    assessed_entity_type = row['assessed_entity_type'].lower().strip()
    assessed_entity_type_name_space = row['assessed_biomarker_entity_id'].split(':')[0].lower().strip()
    assessed_entity_type_accession = row['assessed_biomarker_entity_id'].split(':')[1].strip()
    recommended_name = None
    synonyms = []

    if metadata:
        # check if resource namespace is supported for retrieving synonym data
        if assessed_entity_type_name_space in set(name_space_map.keys()):

            synonyms, recommended_name, api_calls_used = syn_utils.handle_entity_type_synonyms(
                assessed_entity_type, assessed_entity_type_name_space, assessed_entity_type_accession, name_space_map
            )
            if api_calls_used:
                api_call_counter['uniprot'] += api_calls_used.get('uniprot', 0)
                api_call_counter['chebi'] += api_calls_used.get('chebi', 0)
                api_call_counter['cell ontology'] += api_calls_used.get('cell ontology', 0)
                api_call_counter['ncbi'] += api_calls_used.get('ncbi', 0)
            
        # provide warning if name space is not supported
        else:
            misc_fns.log_once(f'Assessed entity type name space \'{assessed_entity_type_name_space}\' not supported for synonym data.', 'info')
    
    # give a warning if the API retrieved recommended name does not match the TSV assessed biomarker entity value 
    if recommended_name:
        if misc_fns.clean_string(row['assessed_biomarker_entity']) != misc_fns.clean_string(recommended_name):
            misc_fns.log_once(f'Warning: Resource recommended name \'{recommended_name}\' does not match the TSV assessed biomarker entity \'{row["assessed_biomarker_entity"]}\'', 'warning')

    entry = {
        'biomarker': row['biomarker'],
        'assessed_biomarker_entity': {
            'recommended_name': row['assessed_biomarker_entity'],
            'synonyms': synonyms 
        },
        'assessed_biomarker_entity_id': row['assessed_biomarker_entity_id'],
        'assessed_entity_type': row['assessed_entity_type']
    }

    return api_call_counter, entry 

def add_specimen_entry(row: dict, biomarker_component_object: dict, url_map: dict) -> dict:
    ''' Builds and appends the specimen entry for the biomarker component object.

    Parameters
    ----------
    row : dict
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
            misc_fns.log_once(f'Specimen database \'{specimen_database}\' not in the url map.', 'info')
    if row['specimen'] or row['loinc_code']:
        specimen = {
            'name': row.get('specimen', ''),
            'id': row.get('specimen_id', ''),
            'name_space': specimen_database.title() if specimen_database else '',
            'url': specimen_url if specimen_url else '',
            'loinc_code': row.get('loinc_code', '')
        }
        biomarker_component_object['specimen'].append(specimen)
    return biomarker_component_object

def parse_tags(row: dict, component_object_evidence_fields: dict) -> tuple:
    ''' Parses the tag string and returns the component and top level evidence tag information formatted per the 
    JSON data model.

    Parameters
    ----------
    row : dict
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

def build_condition_entry(row: dict, url_map: dict, name_space_map: dict, metadata: bool = True) -> Union[dict, None]:
    ''' If applicable, builds the condition entry. 

    Parameters
    ----------
    row : dict
        The current row in the TSV file being processed.
    url_map : dict
        Dictionary that provides mappings for name space's to base URL's. This assists with URL construction.
    name_space_map : dict
        Dictionary that provides mappings for name space acronym's to full name space names.
    metadata : bool (default: True)
         Whether to attempt automatic metadata retrieval.
    
    Returns
    -------
    dict or None
        Dictionary containing the condition entry.
    '''
    condition = None
    if row['condition']:
        # check for full resource name 
        condition_name_space = row['condition_id'].split(':')[0].lower()
        if condition_name_space in set(url_map.keys()):
            condition_resource = name_space_map[condition_name_space].title()
        else:
            misc_fns.log_once(f'Condition name space \'{condition_name_space}\' not in the name space map.', 'info')
            condition_resource = condition_name_space
        # try to build condition url
        condition_url = None
        if condition_name_space in set(url_map.keys()):
            condition_url = f"{url_map[condition_name_space]}{row['condition_id'].split(':')[1]}"
        else:
            misc_fns.log_once(f'Condition name space \'{condition_name_space}\' not in the url map.', 'warning')
        # build entry
        condition = {
            'id': row['condition_id'],
            'recommended_name': {
                'id': row['condition_id'],
                'name': row['condition'],
                'description': None,
                'resource': condition_resource,
                'url': condition_url
            },
            'synonyms': []
        }

        # handle getting the condition description and synonyms
        if metadata:
            if condition_name_space == 'doid':
                doid_data = data_api.get_doid_data(row['condition_id'].split(':')[1])
                if doid_data:
                    if row['condition'] != doid_data['recommended_name']:
                        misc_fns.log_once(f'Warning: Resource recommended name \'{doid_data["recommended_name"]}\' does not match the TSV condition name \'{row["condition"]}\'', 'warning')
                    condition['recommended_name']['description'] = doid_data['description']
                    synonym_entries = []
                    for synonym in doid_data['synonyms']:
                        synonym_entry = {
                            'id': row['condition_id'],
                            'name': synonym,
                            'resource': condition_resource,
                            'url': condition_url
                        }
                        synonym_entries.append(synonym_entry)
                    condition['synonyms'] = synonym_entries 
            else:
                misc_fns.log_once(f'Condition name space \'{condition_name_space}\' not supported for automated condition description and synonyms retrieval.', 'info')
    
    return condition

def build_biomarker_entry(row: dict, biomarker_component_object: dict, condition_entry: Union[dict, None], top_evidence_source: list) -> dict:
    ''' Builds the top level biomarker entry.

    Parameters
    ----------
    row : dict
        The current row in the TSV file being processed.
    biomarker_component_object : dict
        The biomarker component object to add to the biomarker entry.
    condition_entry : dict or None
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

def build_evidence_entry(row: dict, tag_list: list, url_map: dict) -> list:
    ''' Builds the evidence entry.

    Parameters
    ----------
    row : dict
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
            misc_fns.log_once(f'Evidence database \'{evidence_database}\' not in the url map.', 'warning')
            evidence_url = None 
        # build evidence object
        evidence_entry.append(
            {
                'id': evidence_id,
                'database': evidence_database.title(),
                'url': evidence_url,
                'evidence_list': [{'evidence': evidence_txt.strip()} for evidence_txt in row['evidence'].split(';|')] if row['evidence'] else [],
                'tags': tag_list
            }
        )
    
    return evidence_entry

def add_citation_data(result_data: list) -> list:
    ''' Adds the citation data to the current chunk of result data.

    Parameters
    ----------
    result_data : list
        The current chunk of result data JSON.

    Returns
    -------
    list
        The updated result data.
    '''  
    # holds the evidence sources to build the citation entries for
    evidence_sources = []
    # get the evidence source data for each biomarker entry
    for entry_idx, entry in enumerate(result_data):
        seen_pubmed_set = set()
        # get the evidence source data for each biomarker component entry
        for biomarker_componennt_entry in entry['biomarker_component']:
            # get each component evidence source
            for evidence_source in biomarker_componennt_entry['evidence_source']:
                if evidence_source['id'] not in seen_pubmed_set:
                    evidence_sources.append((entry_idx, evidence_source))
                    seen_pubmed_set.add(evidence_source['id'])
        # get the evidence source data for the top level entry
        for evidence_source in entry['evidence_source']:
            if evidence_source['id'] not in seen_pubmed_set:
                evidence_sources.append((entry_idx, evidence_source))
    misc_fns.print_and_log(f'Adding citation data for {len(evidence_sources)} evidence sources...', 'info')

    # get the citation data for each evidence source
    for evidence_source in evidence_sources:
        if evidence_source[1]['database'].lower() == 'pubmed':
            pubmed_api_call_indicator, pubmed_data = data_api.get_pubmed_data(evidence_source[1]['id'])
            syn_utils.handle_rate_limits({'pubmed': pubmed_api_call_indicator})
            if not pubmed_data:
                continue
            citation_entry = {
                'title': pubmed_data['title'],
                'journal': pubmed_data['journal'],
                'authors': pubmed_data['authors'],
                'date': pubmed_data['publication_date'],
                'evidence': [],
                'reference': [
                    {
                        'id': evidence_source[1]['id'],
                        'type': evidence_source[1]['database'].title(),
                        'url': evidence_source[1]['url']
                    }
                ]
            }
            result_data[evidence_source[0]]['citation'].append(citation_entry)
        else:
            misc_fns.log_once(f'Evidence source database \'{evidence_source[1]["database"]}\' not supported for citation data.', 'info')

    misc_fns.print_and_log('Finished adding citation data!', 'info')
    return result_data
