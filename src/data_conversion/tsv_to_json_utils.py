import api_calls as data_api
import misc_functions as misc_fns
import time

RATE_LIMIT_CHECKS = {
    'uniprot': {
        'rate_limit': 200,
        'sleep_time': 1
    },
    'hgnc': {
        'rate_limit': 10,
        'sleep_time': 1
    },
    'pubmed': {
        'rate_limit': 10,
        'sleep_time': 1
    },
    'ncbi': {
        'rate_limit': 10,
        'sleep_time': 1
    }
}
api_counters = {
    'uniprot': {
        'count': 0,
        'total': 0
    },
    'hgnc': {
        'count': 0,
        'total': 0
    },
    'pubmed': {
        'count': 0,
        'total': 0
    },
    'ncbi': {
        'count': 0,
        'total': 0
    }
}

def get_total_api_calls() -> dict:
    ''' Returns the total number of API calls made for each resource during the conversion.

    Returns
    -------
    dict
        Dictionary containing the total number of API calls made for each resource.
    '''
    return_data = {}
    for resource in api_counters:
        return_data[resource] = api_counters[resource]['total']
    return return_data

def _update_resource_api_counters(resource: str, call_count: int) -> None:
    ''' Updates the resource API call counters.

    Parameters
    ----------
    resource : str
        The resource name.
    call_count : int
        The number of API calls made.
    '''
    global api_counters
    api_counters[resource]['count'] += call_count
    api_counters[resource]['total'] += call_count

def _reset_resource_api_counter(resource: str) -> None:
    ''' Resets the resource API call counter.

    Parameters
    ----------
    resource : str
        The resource name.
    '''
    global api_counters
    api_counters[resource]['count'] = 0

def handle_rate_limits(api_calls: dict) -> None:
    ''' Checks the rate limit and sleeps if required.

    Parameters
    ----------
    api_calls : dict
        Dictionary containing the API call indicators.
    '''

    for resource in api_calls:
        if resource not in api_counters:
            continue 
        _update_resource_api_counters(resource, api_calls.get(resource, 0))

    check_pubmed_ncbi_rate_limit = True
    for resource in api_calls:
        if resource not in RATE_LIMIT_CHECKS:
            continue 
        if api_counters[resource]['count'] >= RATE_LIMIT_CHECKS[resource]['rate_limit']:
            misc_fns.print_and_log(f'Rate limit reached for \'{resource}\' API calls. Sleeping for {RATE_LIMIT_CHECKS[resource]["sleep_time"]} seconds...', 'info')
            time.sleep(RATE_LIMIT_CHECKS[resource]['sleep_time'])
            check_pubmed_ncbi_rate_limit = False
            for resource in api_counters:
                _reset_resource_api_counter(resource)
            break 
        
    if check_pubmed_ncbi_rate_limit:
        if api_counters['pubmed']['count'] + api_counters['ncbi']['count'] >= RATE_LIMIT_CHECKS['pubmed']['rate_limit']:
            misc_fns.print_and_log(f'Rate limit reached for \'PubMed and NCBI\' combined API calls. Sleeping for {RATE_LIMIT_CHECKS["pubmed"]["sleep_time"]} seconds...', 'info')
            time.sleep(RATE_LIMIT_CHECKS['pubmed']['sleep_time'])
            for resource in api_counters:
                _reset_resource_api_counter(resource)

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
        Tuple containing the synonyms, recommended name, and api call indicator dictionary.
    '''
    entity_type_fn_map = {
        'protein': _handle_protein_synonyms,
        'metabolite': _handle_metabolite_synonyms,
        'cell': _handle_cell_synonyms,
        'gene': _handle_gene_synonyms
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

def _handle_gene_synonyms(assessed_entity_type_name_space: str, assessed_entity_type_accession: str, name_space_map: dict) -> tuple:
    ''' Handles the gene synonym data returned from the API call for assessed biomarker entity data.

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
    if name_space_map[assessed_entity_type_name_space] == 'ncbi':
        api_call_count, resource_data = data_api.get_ncbi_data(assessed_entity_type_accession, 'gene')
    else:
        misc_fns.log_once(f'Assessed entity type name space \'{assessed_entity_type_name_space}\' not supported for automated gene synonym data retrieval.', 'info')
        return None, None
    api_call_counter[name_space_map[assessed_entity_type_name_space]] = api_call_count
    return resource_data, api_call_counter

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
    elif name_space_map[assessed_entity_type_name_space] == 'hgnc':
        api_call_count, resource_data = data_api.get_hgnc_data(assessed_entity_type_accession)
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