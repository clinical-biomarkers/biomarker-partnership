''' Functions to handle API calls for getting supplementary data during the TSV to JSON conversion. 
'''

from pymed import PubMed
import logging
import requests 
import re 
from dotenv import load_dotenv
import os

DOID_API_ENDPOINT = 'https://www.disease-ontology.org/api/metadata/DOID:'

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

    pubmed = PubMed(tool = 'CFDE Biomarker-Partnership', email = os.getenv('EMAIL'))