''' Miscellaneous configuration functions for data conversion process. 
'''

import logging
import json
import os 
import re

def setup_logging(log_path: str) -> None:
    ''' Set up logging for the data conversion process.

    Parameters
    ----------
    log_path : str
        Path to the log file. 
    '''
    logging.basicConfig(filename=log_path, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

def validate_filepath(filepath: str, mode: str) -> None:
    ''' Validates the filepaths for the user inputted source path and
    the destination path. 

    Parameters
    ----------
    filepath: str
        Filepath to the source data dictionary file or the output path.
    mode: str
        Whether checking the output directory path or the input file. ('input' or 'output')
    '''
    
    if mode == 'input':
        if not os.path.isfile(filepath):
            logging.error(f'Error: The (input) file {filepath} does not exist.')
            raise ValueError(f'Error: The (input) file {filepath} does not exist.')
    elif mode == 'output':
        if not os.path.isdir(filepath):
            logging.error(f'Error: The (output) directory {filepath} does not exist.')
            raise ValueError(f'Error: The (output) directory {filepath} does not exist.')
    else:
        logging.error(f'Validate_filepath error: Invalid mode {mode}')
        raise ValueError(f'Validate_filepath error: Invalid mode {mode}')

def load_json(filepath: str) -> dict:
    ''' Loads and returns a JSON file.

    Parameters
    ----------
    filepath: str
        Filepath to the JSON file.

    Returns
    -------
    dict
        The loaded JSON to return.
    '''
    with open(filepath, 'r') as f:
        return json.load(f)

def write_json(filepath: str, data: dict) -> None:
    ''' Writes the data to a JSON file.

    Parameters
    ----------
    filepath: str
        Filepath to the JSON file.
    data: dict
        Data to write to the JSON file.
    '''
    with open(filepath, 'w') as f:
        json.dump(data, f, indent = 4)

def clean_string(string: str) -> str:
    ''' Cleans a string by removing all non-alphanumeric characters and
    converting to lowercase.

    Parameters
    ----------
    string: str
        String to clean.

    Returns
    -------
    str
        The cleaned string.
    '''
    return re.sub(r'[^A-Za-z0-9]+', '', string).lower()

def print_and_log(string: str, level: str) -> None:
    ''' Logs and prints if level is warning (for error level the calling 
    code is expected to raise the error so no print required). 

    Parameters
    ----------
    string: str
        String to print and log.
    level: str
        Level of logging to use.
    '''
    if level.lower() == 'debug':
        logging.debug(string)
    elif level.lower() == 'info':
        logging.info(string)
    elif level.lower() == 'warning':
        logging.warning(string)
        print(string)
    elif level.lower() == 'error':
        logging.error(string)
    else:
        logging.error(f'print_and_log error: Invalid level {level}')
        raise ValueError(f'print_and_log error: Invalid level {level}')