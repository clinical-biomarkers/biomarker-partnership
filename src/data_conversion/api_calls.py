''' Functions to handle API calls for getting supplementary data during the TSV to JSON conversion. 
'''

from pymed import PubMed
import logging
import requests 
import re 
from dotenv import load_dotenv
import os
from time import sleep
import json
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError

DOID_API_ENDPOINT = 'https://www.disease-ontology.org/api/metadata/DOID:'
UNIPROT_API_ENDPOINT = 'https://www.ebi.ac.uk/proteins/api/proteins/'
CHEBI_API_ENDPOINT = 'https://www.ebi.ac.uk/webservices/chebi/2.0/test/getCompleteEntity?chebiId='

def get_doid_data(doid_id: str, max_retries: int = 3, timeout: int = 5) -> dict:
    ''' Gets the DOID data for the given DOID ID.

    Parameters
    ----------
    doid_id: str
        The DOID ID to get the data for.
    max_retries: int
        The maximum number of times to retry the API call if it fails.
    timeout: int
        The number of seconds to wait before timing out the API call.

    Returns
    -------
    dict
        The synonym and description data for the given DOID ID.
    '''
    doid_id = doid_id.strip()
    # first check DOID cache and see if information is there to avoid duplicate API calls
    with open('../../mapping_data/doid_map.json', 'r') as f:
        doid_map = json.load(f)
    if doid_id in doid_map:
        return doid_map[doid_id]    

    attempt = 0
    while attempt < max_retries:
        try:
            response = requests.get(DOID_API_ENDPOINT + doid_id, timeout = timeout)

            # handle errors
            if response.status_code != 200:
                logging.error(f'Error during DOID API call for id {doid_id}:\n\tStatus Code: {doid_data.status_code}\n\tReturn Data: {doid_data.text}')
                print(f'Error during DOID API call for id {doid_id}:\n\tStatus Code: {doid_data.status_code}\n\tReturn Data: {doid_data.text}')
                return None
            
            # if no return error, continue to processing
            doid_data = response.json()

            # clean the doid description
            doid_description = doid_data.get('definition', '')
            doid_description = re.search('\"(.*)\"', doid_description).group(1)

            # only keep the synonyms that have the EXACT qualifier and remove the qualifier
            synonyms = doid_data.get('synonyms', [])
            synonyms = [] if synonyms is None else synonyms
            synonyms = [synonym.replace('EXACT', '').strip() for synonym in synonyms if 'EXACT' in synonym]
            return_data = {'description': doid_description, 'synonyms': synonyms} 
            with open('../../mapping_data/doid_map.json', 'w') as f:
                doid_map[doid_id] = return_data
                json.dump(doid_map, f, indent = 4)
            return return_data
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            logging.warning(f'Warning: Failed to connect to DOID API on attempt {attempt + 1}. Retrying...')
            print(f'Warning: Failed to connect to DOID API. Retrying...')
            attempt += 1
            sleep(1)
            continue
    
    logging.error(f'Failed to retrive DOID data after {max_retries} attempts.')
    return None

def get_pubmed_data(pubmed_id: str) -> tuple:
    ''' Gets the PubMed data for the given PubMed ID.

    Parameters
    ----------
    pubmed_id: str
        The PubMed ID to get the data for.

    Returns
    -------
    tuple
        Indicator if an api call was used and PubMed data for the given PubMed ID.
    '''
    pubmed_id = pubmed_id.strip()
    # check PubMed cache and see if information is there to avoid duplicate API calls
    with open('../../mapping_data/pubmed_map.json', 'r') as f:
        pubmed_map = json.load(f)
    if pubmed_id in pubmed_map:
        return 0, pubmed_map[pubmed_id]
    
    # load local environment variables
    load_dotenv()
    # get email from environment variables
    email = os.getenv('EMAIL') 
    # try to get api key from environment variables
    try:
        api_key = os.getenv('API_KEY')
    except Exception as e:
        logging.warning(f'Warning: Failed to find API_KEY environment variable. Consider adding one.')
        api_key = None
    if email is None:
        logging.error(f'Error: Failed to find EMAIL environment variable. Check .env file.')
        print(f'Error: Failed to find EMAIL environment variable. Check .env file. Skipping PubMed API calls...')
        return 0, None 

    # query PubMed for the given PubMed ID
    pubmed = PubMed(tool = 'CFDE Biomarker-Partnership', email = email)
    if api_key:
        pubmed.parameters.update({'api_key': api_key})
    query = f'PMID: {pubmed_id}'
    articles = pubmed.query(query)
    try:
        article = next(articles)
    except StopIteration:
        logging.error(f'Error: No articles found for PubMed ID {pubmed_id}')
        print(f'Error: No articles found for PubMed ID {pubmed_id}')
        return 1, None
    except ParseError as e:
        logging.error(f'XML Parsing Error: Failed to parse PubMed data for PubMed ID {pubmed_id}:\n\t{e}')
        print(f'XML Parsing Error: Failed to parse PubMed data for PubMed ID {pubmed_id}:\n\t{e}')
        return 1, None
    except Exception as e:
        logging.error(f'Unexpected error while fetching PubMed data for PubMed ID {pubmed_id}:\n\t{e}')
        print(f'Unexpected error while fetching PubMed data for PubMed ID {pubmed_id}:\n\t{e}')
        return 1, None

    # parse return data
    try:
        title = article.title
        journal = article.journal
        authors = ', '.join([f"{author['lastname']} {author['initials']}" for author in article.authors])
        publication_date = str(article.publication_date)
    except Exception as e:
        logging.error(f'Error: Failed to parse PubMed data for PubMed ID {pubmed_id}:\n\tReturn JSON: {article}\n\t{e}')
        print(f'Error: Failed to parse PubMed data for PubMed ID {pubmed_id}:\n\tReturn JSON: {article}\n\t{e}')
        return 1, None
    
    return_data = {
        'title': title,
        'journal': journal,
        'authors': authors,
        'publication_date': publication_date
    }
    # add data to cache
    with open('../../mapping_data/pubmed_map.json', 'w') as f:
        pubmed_map[pubmed_id] = return_data
        json.dump(pubmed_map, f, indent = 4)
    return 1, return_data

def get_uniprot_data(uniprot_id: str, assessed_entity_type: str) -> tuple:
    ''' Gets the UniProt data for the given UniProt ID.

    Parameters
    ----------
    uniprot_id: str
        The UniProt ID to get the data for.
    assessed_entity_type: str
        The type of assessed entity. (ex. protein or gene)
    
    Returns
    -------
    tuple
        Inicator if an api call was used and the UniProt name and synonym data for the given UniProt ID protein.
    '''
    uniprot_id = uniprot_id.strip()
    # check UniProt cache and see if information is there to avoid duplicate API calls
    with open('../../mapping_data/uniprot_map.json', 'r') as f:
        uniprot_map = json.load(f)
    if uniprot_id in uniprot_map:
        return 0, uniprot_map[uniprot_id]
    
    uniprot_data = requests.get(UNIPROT_API_ENDPOINT + uniprot_id)

    # handle errors
    if uniprot_data.status_code != 200:
        logging.error(f'Error during UniProt API call for id {uniprot_id}:\n\tStatus Code: {uniprot_data.status_code}\n\tReturn Data: {uniprot_data.text}')
        print(f'Error during UniProt API call for id {uniprot_id}:\n\tStatus Code: {uniprot_data.status_code}\n\tReturn Data: {uniprot_data.text}')
        return 1, None
    
    # get protein name and synonyms
    uniprot_data = uniprot_data.json()['protein']
    synonyms = []
    for recommended_short_name in uniprot_data.get('recommendedName', {}).get('shortName', []):
        synonyms.append(recommended_short_name['value'])
    for alternative_name in uniprot_data.get('alternativeName', []):
        synonyms.append(alternative_name['fullName']['value'])
        for alternative_short_name in alternative_name.get('shortName', []):
            synonyms.append(alternative_short_name['value'])

    return_data = {
        'recommended_name': uniprot_data['recommendedName']['fullName']['value'],
        'synonyms': synonyms
    }
    # add data to cache
    with open('../../mapping_data/uniprot_map.json', 'w') as f:
        uniprot_map[uniprot_id] = return_data
        json.dump(uniprot_map, f, indent = 4)
    return 1, return_data

def get_chebi_data(chebi_id: str, max_retries: int = 3, timeout: int = 5) -> dict:
    ''' Gets the ChEBI data for the given ChEBI ID.

    Parameters
    ----------
    chebi_id: str
        The ChEBI ID to get the data for.
    max_retries: int
        The maximum number of times to retry the API call if it fails.
    timeout: int
        The number of seconds to wait before timing out the API call.
    
    Returns
    -------
    dict
        The ChEBI name and synonym data for the given ChEBI ID.
    '''
    chebi_id = chebi_id.strip()
    # check ChEBI cache and see if information is there to avoid duplicate API calls
    with open('../../mapping_data/chebi_map.json', 'r') as f:
        chebi_map = json.load(f)
    if chebi_id in chebi_map:
        return chebi_map[chebi_id]
    
    ns = {'chebi': 'https://www.ebi.ac.uk/webservices/chebi'}
    attempt = 0
    while attempt < max_retries:
        try:
            response = requests.get(CHEBI_API_ENDPOINT + chebi_id, timeout = timeout)
            if response.status_code != 200:
                logging.error(f'Error during ChEBI API call for id {chebi_id}:\n\tStatus Code: {response.status_code}\n\tReturn Data: {response.text}')
                print(f'Error during ChEBI API call for id {chebi_id}:\n\tStatus Code: {response.status_code}\n\tReturn Data: {response.text}')
                return None
            root = ET.fromstring(response.content)
            chebi_name_element = root.find('.//chebi:chebiAsciiName', ns)
            synonym_elements = root.findall('.//chebi:Synonyms', ns)
            synonyms = [synonym.find('chebi:data', ns).text for synonym in synonym_elements]
            return_data = {
                'recommended_name': chebi_name_element.text,
                'synonyms': [synonym for synonym in synonyms]
            }
            # add data to cache
            with open('../../mapping_data/chebi_map.json', 'w') as f:
                chebi_map[chebi_id] = return_data
                json.dump(chebi_map, f, indent = 4)
            return return_data

        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            logging.warning(f'Warning: Failed to connect to ChEBI API on attempt {attempt + 1}. Retrying...')
            print(f'Warning: Failed to connect to ChEBI API. Retrying...')
            attempt += 1
            sleep(1)
            continue
        except Exception as e:
            logging.error(f'Unexpected error while fetching ChEBI data for ChEBI ID {chebi_id}:\n\t{e}')
            print(f'Unexpected error while fetching ChEBI data for ChEBI ID {chebi_id}:\n\t{e}')
            return None
    
    logging.error(f'Failed to retrive ChEBI data after {max_retries} attempts.')
    return None
