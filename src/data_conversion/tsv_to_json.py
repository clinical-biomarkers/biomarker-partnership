''' Handles the conversion from the TSV table format to the JSON data model format.
'''

import json
import logging 

def tsv_to_json(source_filepath: str, target_filepath: str, url_map: dict, name_space_map: dict) -> None:
    ''' Entry point for the TSV -> JSON conversion.

    Parameters
    ----------
    source_filepath : str
        Filepath to the source TSV file.
    target_filepath : str
        Filepath to the target JSON file to generate.
    url_map : dict
        Dictionary that provides mappings for name space's to base URL's. This assists with URL construction.
    name_space_map : dict
        Dictionary that provides mappings for name space acronym's to full name space names.
    '''