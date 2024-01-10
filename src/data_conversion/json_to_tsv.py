''' Handles the conversion from the JSON data model format to the TSV table format.
'''

import json  
import logging 

def json_to_tsv(source_filepath: str, target_filepath: str, url_map: dict, name_space_map: dict) -> None:
    ''' Entry point for the JSON -> TSV conversion. 

    Parameters
    ----------
    source_filepath : str
        Filepath to the source JSON file.
    target_filepath : str
        Filepath to the target TSV file to generate. 
    url_map : dict
        Dictionary that provides mappings for name space's to base URL's. This assists with URL construction.
    name_space_map : dict
        Dictionary that provides mappings for name space acronym's to full name space names.
    '''