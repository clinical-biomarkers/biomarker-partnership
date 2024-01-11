''' Functions to handle API calls for getting supplementary data during the TSV to JSON conversion. 
'''

from pymed import PubMed
import logging
import requests 
import re 
from dotenv import load_dotenv
import os

DOID_API_ENDPOINT = 'https://www.disease-ontology.org/api/metadata/DOID:'
UNIPROT_API_ENDPOINT = 'https://www.ebi.ac.uk/proteins/api/proteins/'

def get_doid_data(doid_id: str) -> dict:
    ''' Gets the DOID data for the given DOID ID.

    Parameters
    ----------
    doid_id: str
        The DOID ID to get the data for.

    Returns
    -------
    dict
        The synonym and description data for the given DOID ID.
    '''
    doid_data = requests.get(DOID_API_ENDPOINT + doid_id)

    # handle errors
    if doid_data.status_code != 200:
        logging.error(f'Error during DOID API call for id {doid_id}:\n\tStatus Code: {doid_data.status_code}\n\tReturn Data: {doid_data.text}')
        print(f'Error during DOID API call for id {doid_id}:\n\tStatus Code: {doid_data.status_code}\n\tReturn Data: {doid_data.text}')
        return None
    
    # if no return error, continue to processing
    doid_data = doid_data.json()

    # clean the doid description
    doid_description = doid_data.get('definition', '')
    doid_description = re.search('\"(.*)\"', doid_description).group(1)

    # only keep the synonyms that have the EXACT qualifier and remove the qualifier
    synonyms = doid_data.get('synonyms', [])
    synonyms = [synonym.replace('EXACT', '').strip() for synonym in synonyms if 'EXACT' in synonym]

    return_data = {
        'description': doid_description,
        'synonyms': synonyms
    }

    return return_data

def get_pubmed_data(pubmed_id: str) -> dict:
    ''' Gets the PubMed data for the given PubMed ID.

    Parameters
    ----------
    pubmed_id: str
        The PubMed ID to get the data for.

    Returns
    -------
    dict
        The PubMed data for the given PubMed ID.
    '''
    
    # load local environment variables
    load_dotenv()
    # get email from environment variables
    email = os.getenv('EMAIL') 
    if email is None:
        logging.error(f'Error: Failed to find EMAIL environment variable. Check .env file.')
        print(f'Error: Failed to find EMAIL environment variable. Check .env file. Skipping PubMed API calls...')
        return None 

    # query PubMed for the given PubMed ID
    pubmed = PubMed(tool = 'CFDE Biomarker-Partnership', email = email)
    query = f'PMID: {pubmed_id}'
    articles = pubmed.query(query)
    try:
        article = next(articles)
    except StopIteration:
        logging.error(f'Error: No articles found for PubMed ID {pubmed_id}')
        print(f'Error: No articles found for PubMed ID {pubmed_id}')
        return None

    # parse return data
    try:
        title = article.title
        journal = article.journal
        authors = ', '.join([f"{author['lastname']} {author['initials']}" for author in article.authors])
        publication_date = str(article.publication_date)
    except Exception as e:
        logging.error(f'Error: Failed to parse PubMed data for PubMed ID {pubmed_id}:\n\tReturn JSON: {article}\n\t{e}')
        print(f'Error: Failed to parse PubMed data for PubMed ID {pubmed_id}:\n\tReturn JSON: {article}\n\t{e}')
        return None
    
    return_data = {
        'title': title,
        'journal': journal,
        'authors': authors,
        'publication_date': publication_date
    }
    return return_data

def get_uniprot_data(uniprot_id: str) -> dict:
    ''' Gets the UniProt data for the given UniProt ID.

    Parameters
    ----------
    uniprot_id: str
        The UniProt ID to get the data for.
    
    Returns
    -------
    dict
        The UniProt name and synonym data for the given UniProt ID protein.
    '''
    uniprot_data = requests.get(UNIPROT_API_ENDPOINT + uniprot_id)

    # handle errors
    if uniprot_data.status_code != 200:
        logging.error(f'Error during UniProt API call for id {uniprot_id}:\n\tStatus Code: {uniprot_data.status_code}\n\tReturn Data: {uniprot_data.text}')
        print(f'Error during UniProt API call for id {uniprot_id}:\n\tStatus Code: {uniprot_data.status_code}\n\tReturn Data: {uniprot_data.text}')
        return None
    
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
    return return_data
