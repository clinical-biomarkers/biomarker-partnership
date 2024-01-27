import api_calls as data_api
import misc_functions as misc_fns
import sys

def handle_entity_type_synonyms(entity_type: str, assessed_entity_type_name_space: str, assessed_entity_type_accession: str, name_space_map: dict) -> tuple:
    ''' For supported resources, handles the synonym and recommended name data returned from the API call for assessed biomarker entity data.

    Parameters
    ----------
    entity_type : str
        The entity type.
    assessed_entity_type_name_space : str
        The namespace (resource) of the assessed entity type.
    assessed_entity_type_accession : str
        The accession (ID) of the assessed entity type.
    name_space_map : dict
        Dictionary containing the namespace mappings.
    
    Returns
    -------
    tuple
        Tuple containing the recommended name, synonyms, and api call indicator dictionary.
    '''
    entity_type_fn_map = {
        'protein': _handle_protein_synonyms,
        'metabolite': _handle_metabolite_synonyms,
        'cell': _handle_cell_synonyms
    }

    if entity_type not in entity_type_fn_map:
        misc_fns.log_once(f'Assessed entity type \'{entity_type}\' not supported for automated synonym data retrieval.', 'info')
        return [], None, None
    
    resource_data, api_call_counter = entity_type_fn_map[entity_type](assessed_entity_type_name_space, assessed_entity_type_accession, name_space_map)
    if not resource_data and not api_call_counter:
        return [], None, None
    synonyms, recommended_name = _handle_synonym_rec_name_data(resource_data)
    return synonyms, recommended_name, api_call_counter

def _handle_synonym_rec_name_data(data: dict) -> tuple:
    ''' Handles the synonym and recommended name data formatting according to the data model.

    Parameters
    ----------
    data : dict
        Dictionary containing the API call response data.
    
    Returns
    -------
    tuple
        Tuple containing the recommended name and synonym entries.
    '''
    if data:
        synonyms = [{'synonym': synonym} for synonym in data['synonyms']]
        recommended_name = data['recommended_name']
        return synonyms, recommended_name
    return [], None

def _handle_protein_synonyms(assessed_entity_type_name_space: str, assessed_entity_type_accession: str, name_space_map: dict) -> tuple:
    ''' Handles the protein synonym data returned from the API call for assessed biomarker entity data.

    Parameters
    ----------
    assessed_entity_type_name_space : str
        The namespace (resource) of the assessed entity type.
    assessed_entity_type_accession : str
        The accession of the assessed entity type.
    name_space_map : dict
        Dictionary containing the namespace mappings.
    
    Returns
    -------
    tuple
        Tuple containing the recommended name and synonyms dictionary, and api call indicator dictionary.
    '''
    api_call_counter = {}
    if name_space_map[assessed_entity_type_name_space] == 'uniprot':
        api_call_count, resource_data = data_api.get_uniprot_data(assessed_entity_type_accession, 'protein')
    elif name_space_map[assessed_entity_type_name_space] == 'chebi':
        api_call_count, resource_data = data_api.get_chebi_data(assessed_entity_type_accession)
    else:
        misc_fns.log_once(f'Assessed entity type name space \'{assessed_entity_type_name_space}\' not supported for automated protein synonym data retrieval.', 'info')
        return None, None
    api_call_counter[name_space_map[assessed_entity_type_name_space]] = api_call_count
    return resource_data, api_call_counter

def _handle_metabolite_synonyms(assessed_entity_type_name_space: str, assessed_entity_type_accession: str, name_space_map: dict) -> tuple:
    ''' Handles the metabolite synonym data returned from the API call for assessed biomarker entity data.

    Parameters
    ----------
    assessed_entity_type_name_space : str
        The namespace (resource) of the assessed entity type.
    assessed_entity_type_accession : str
        The accession of the assessed entity type.
    name_space_map : dict
        Dictionary containing the namespace mappings.
    
    Returns
    -------
    tuple
        Tuple containing the recommended name and synonyms dictionary, and api call indicator dictionary.
    '''
    api_call_counter = {}
    if name_space_map[assessed_entity_type_name_space] == 'chebi':
        api_call_count, resource_data = data_api.get_chebi_data(assessed_entity_type_accession)
    else:
        misc_fns.log_once(f'Assessed entity type name space \'{assessed_entity_type_name_space}\' not supported for automated metabolite synonym data retrieval.', 'info')
        return None, None
    api_call_counter[name_space_map[assessed_entity_type_name_space]] = api_call_count
    return resource_data, api_call_counter

def _handle_cell_synonyms(assessed_entity_type_name_space: str, assessed_entity_type_accession: str, name_space_map: dict) -> tuple:
    ''' Handles the cell synonym data returned from the API call for assessed biomarker entity data.

    Parameters
    ----------
    assessed_entity_type_name_space : str
        The namespace (resource) of the assessed entity type.
    assessed_entity_type_accession : str
        The accession of the assessed entity type.
    name_space_map : dict
        Dictionary containing the namespace mappings.
    
    Returns
    -------
    tuple
        Tuple containing the recommended name and synonyms dictionary, and api call indicator dictionary.
    '''
    api_call_counter = {}
    if name_space_map[assessed_entity_type_name_space] == 'cell ontology':
        api_call_count, resource_data = data_api.get_co_data(assessed_entity_type_accession)
    else:
        misc_fns.log_once(f'Assessed entity type name space \'{assessed_entity_type_name_space}\' not supported for automated cell synonym data retrieval.', 'info')
        return None, None
    api_call_counter[name_space_map[assessed_entity_type_name_space]] = api_call_count
    return resource_data, api_call_counter