''' Helper functions for the JSON to TSV conversion.
'''

from fmt_lib import misc_functions as misc_fns
import traceback

SINGLE_EVIDENCE_FIELDS = {
    'biomarker',
    'assessed_biomarker_entity',
    'assessed_biomarker_entity_id',
    'assessed_entity_type',
    'condition',
    'exposure_agent',
    'best_biomarker_role'
}

def extract_top_level_fields(entry: dict, idx: int) -> tuple:
    ''' Takes a biomarker JSON entry and extracts the the 
    top level fields.

    Parameters
    ----------
    entry: dict
        The biomarker JSON entry.
    idx: int
        The index of the entry.

    Raises
    ------
    KeyError: On missing key requesets.
    Exception: On unexpected errors.

    Returns
    -------
    tuple
        (biomarker_id, condition, condition_id, exposure_agent, 
         exposure_agent_id, best_biomarker_roles, top_level_evidence)
    '''
    try:
        best_biomarker_roles_dict = entry['best_biomarker_role']
        return_data = (
            entry['biomarker_id'], 
            entry.get('condition', {}).get('recommended_name', {}).get('name', ''),
            entry.get('condition', {}).get('condition_id', ''),
            entry.get('exposure_agent', {}).get('recommended_name', {}).get('name', ''),
            entry.get('exposure_agent', {}).get('exposure_agent_id', ''),
            ';'.join([role['role'] for role in best_biomarker_roles_dict]),
            entry.get('evidence_source', [])
        )
    except KeyError as e:
        misc_fns.print_and_log(
            f'KeyError: Error parsing top level element in JSON data:\n\t\
            Index: {idx}\n\tError: {e}\n\n{traceback.format_exc()}',
            'error'
        )
        raise KeyError(e)
    except Exception as e:
        misc_fns.print_and_log(
            f'Unexpected error parsing top level elements in JSON data:\n\t\
            Index: {idx}\n\tError: {e}\n\n{traceback.format_exc()}',
            'error'
        )
        raise Exception(e)
    
    return return_data

def extract_component_fields(component_entry: dict, idx: int) -> tuple:
    ''' Takes a biomarker component and extracts component fields.

    Parameters
    ----------
    component_entries: dict
        The biomarker component.
    idx: int
        The index of the component.

    Raises
    ------
    KeyError: On missing key requesets.
    Exception: On unexpected errors.

    Returns
    -------
    tuple
        (biomarker, assessed_biomarker_entity, assessed_biomarker_entity_id,
         assessed_entity_type, component_evidence, specimen)
    '''
    try:
        return_data = (
            component_entry['biomarker'],
            component_entry['assessed_biomarker_entity']['recommended_name'],
            component_entry['assessed_biomarker_entity_id'],
            component_entry['assessed_entity_type'],
            component_entry['evidence_source'],
            component_entry.get('specimen', [])
        )
    except KeyError as e:
        misc_fns.print_and_log(
            f'KeyError: Error parsing biomarker component element in JSON data:\n\t\
            Index: {idx}\n\tError: {e}\n\n{traceback.format_exc()}',
            'error'
        )
        raise KeyError(e)
    except Exception as e:
        misc_fns.print_and_log(
            f'Unexpected error parsing biomarker component elements in JSON data:\n\t\
            Index: {idx}\n\tError: {e}\n\n{traceback.format_exc()}',
            'error'
        )
        raise Exception(e)

    return return_data

def tag_parse(tag: dict, object_evidence_fields: dict, component_idx: int = -1) -> tuple:
    ''' Parses the evidence tag data in the JSON model.

    Parameters
    ----------
    tag : dict
        Dictionary containing the tag data.
    object_evidence_fields : dict 
        Dictionary containing the object/array evidence fields and their values.
    component_idx : int, optional (default = -1)
        Index of the current component entry for top level evidence parsing.

    Returns
    -------
    tuple
        Tuple of the raw extracted tag value and a boolean flag indicating whether the evidence is applicable for the current row.
    '''
    evidence_flag = False
    tag_value = tag['tag'].split(':')[0]
    tag_index = tag['tag'].split(':')[-1]

    if component_idx == -1 and tag_value != tag_index and component_idx != tag_index:
        return (None, evidence_flag)

    # check that tag is applicable to the current row
    if tag_value in SINGLE_EVIDENCE_FIELDS:
        evidence_flag = True
    if tag_value in set(object_evidence_fields.keys()):
        if tag['tag'][tag['tag'].find(':') + 1] == object_evidence_fields[tag_value]:
            evidence_flag = True
    return (tag_value, evidence_flag)

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
    return ';|'.join(evidence_values)    
