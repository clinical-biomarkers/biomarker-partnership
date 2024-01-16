#!/usr/bin/env/python3
''' Biomarker-Partnership testing script. Tests multiple parts of the repository workflow.

Currently configured to test these scripts:
    - /data_dictionary/skeleton_dictionary.py
    - /data_dictionary/process_dictionary.py
    - /schema/validate_data.py
    - /src/table_json_conversion.py 

Usage: python test.py [options]

    Optional arguments:
        -h --help       show the help message and exit 
        -v --version    show current version number and exit
'''

import json 
import argparse 
import sys 
import os 
import subprocess
import glob 
import logging
import pandas as pd

_CONF_KEY = 'testing'
_version = None
_log_path = None
_python = None
_tmp_output_path = None 
SOURCE_FILES = None 

def user_args() -> None:
    ''' Parses the command line arguments.
    '''
    # argument parser 
    parser = argparse.ArgumentParser(
        prog = 'biomarker_tester',
        usage = 'python test.py [options]'
    )
    parser.add_argument('-v', '--version', action = 'version', version = f'%(prog)s {_version}')
    options = parser.parse_args()

def get_test_files() -> dict:
    ''' Gets the test files for each testing category.

    Returns
    -------
    dict
        Returns a dictionary with each testing category's data, assertion, and script files.
    '''
    result = {}
    for test_category in list(SOURCE_FILES.keys()):
        path_root = f'./v{_version}/{test_category}'
        glob_pattern = '*'
        assertion_path = f'{path_root}/assertion_files/{glob_pattern}'
        data_path = f'{path_root}/test_data/{glob_pattern}'
        result[test_category] = {
            'assertion_files': glob.glob(assertion_path),
            'data_files': glob.glob(data_path),
            'script_path': SOURCE_FILES[test_category]
        }
        validate_filepath(SOURCE_FILES[test_category], mode = 'input')
    
    return result

def validate_test_data_pairs(files: dict) -> int:
    ''' Validates whether the matching assertion and test data file pairs exist. 

    Parameters
    ----------
    files: dict
        The file dictionary structure created from the get_test_files function.

    Returns
    -------
    int 
        0 if processing succesful, 1 if not. 
    '''
    error_count = 1
    for test_category in list(SOURCE_FILES):
        for test_data_path in files[test_category]['data_files']:
            data_file_path, _ = os.path.splitext(test_data_path)
            _, data_file_name = os.path.split(data_file_path)
            assertion_files = [os.path.split(os.path.splitext(assertion_file_name)[0])[1] for assertion_file_name in files[test_category]['assertion_files']]
            if data_file_name not in assertion_files:
                logging.error(f'Error #{error_count} - Missing matching assertion file for test case:\n\tTest case: {test_data_path}\n\tTest category: {test_category}')
                error_count += 1 
    if error_count == 1:
        logging.info(f'Passed test data pair validation.')
        return 0
    else:
        return 1

def setup_logging(log_path: str) -> None:
    ''' Configures the logger to write to a file.

    Parameters
    ----------
    log_path: str
        The path of the log file.
    '''
    logging.basicConfig(filename = log_path, level = logging.INFO,
                        format = '%(asctime)s - %(levelname)s - %(message)s')

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
            logging.error(f'validate_filepath mode: {mode}\n\tFileNotFoundError: {filepath}')
            raise FileNotFoundError(f'Error: The (input) file {filepath} does not exist.')
    elif mode == 'output':
        if not os.path.isdir(filepath):
            logging.error(f'validate_filepath mode: {mode}\n\tFileNotFoundError: {filepath}')
            raise FileNotFoundError(f'Error: The (output) directory {filepath} does not exist.')
    else:
        raise ValueError(f'Validate_filepath error: Invalid mode {mode}')

def validate_assertion(source_filepath: str, assertion_filepath: str, filetype: str) -> bool:
    ''' Validates a generated file against the corresponding assertion file. 

    Parameters
    ----------
    source_filepath: str
        File path to the generated file to check. 
    assertion_filepath: str 
        File path to the assertion file to check against.
    filetype: str
        The file type of the files. 
    
    Returns
    -------
    bool
        True if the assertion check passed, False otherwise. 
    '''
    # checks the assertion if both source and assertion file types are json
    if filetype.lower().strip() == 'json':
        with open(source_filepath, 'r') as f:
            source_data = json.load(f)
        with open(assertion_filepath, 'r') as f:
            assertion_data = json.load(f)

        if source_data == assertion_data:
            return True
        else: 
            return False
    
    # checks the assertion if the target conversion format is tsv
    elif filetype.lower().strip() == 'tsv':
        with open(source_filepath, 'r') as f:
            source_data = pd.read_csv(f, sep = '\t')
        with open(assertion_filepath, 'r') as f:
            assertion_data = pd.read_csv(f, sep = '\t')
        source_data = source_data.fillna('')
        assertion_data = assertion_data.fillna('')
        # sort the dataframes by the first and second column so ordering does not matter
        source_data = source_data.sort_values(by = [source_data.columns[0], source_data.columns[1]]).reset_index(drop = True)
        assertion_data = assertion_data.sort_values(by = [assertion_data.columns[0], source_data.columns[1]]).reset_index(drop = True)
        if source_data.equals(assertion_data):
            return True
        else:
            return False

# def validate_conversion_assertion(source_filepath: str, assertion_filepath: str, source_filetype: str) -> bool:
#     ''' Validates a generated file against the corresponding assertion file.

#     Parameters
#     ----------
#     source_filepath: str
#         File path to the generated file to check.
#     assertion_filepath: str
#         File path to the assertion file to check against.
#     target_filetype: str
#         The file type of the target file.
    
#     Returns
#     -------
#     bool
#         True if the assertion check passed, False otherwise.
#     '''
#     # checks the assertion if the target conversion format is tsv
#     if source_filetype.lower().strip() == 'tsv':
#         with open(source_filepath, 'r') as f:
#             source_data = pd.read_csv(f, sep = '\t')
#         with open(assertion_filepath, 'r') as f:
#             assertion_data = pd.read_csv(f, sep = '\t')
#         source_data = source_data.fillna('')
#         assertion_data = assertion_data.fillna('')
#         # sort the dataframes by the first and second column so ordering does not matter
#         source_data = source_data.sort_values(by = [source_data.columns[0], source_data.columns[1]]).reset_index(drop = True)
#         assertion_data = assertion_data.sort_values(by = assertion_data.columns[0]).reset_index(drop = True)
#         if source_data.equals(assertion_data):
#             return True
#         else:
#             return False
    

def skeleton_dict_tests(test_data: dict) -> str:
    ''' Runs the tests for the skeleton_dictionary.py script.

    Parameters
    ----------
    test_data: dict
        The data for the skeleton dictionary testing.

    Returns
    -------
    str
        The output string for the test case results.
    '''
    script = os.path.split(test_data['script_path'])[1]
    assertion_files = test_data['assertion_files']
    test_files = [f"{test_tmp.replace('./', '../supplementary_files/tests/')}" for test_tmp in test_data["data_files"]]
    cwd = '../../data_dictionary'
    result = 'SKELETON DICT TEST RESULTS:'
    fail_count = 0

    # run each test
    for test_num, test in enumerate(test_files):
        test_name = os.path.split(os.path.splitext(test)[0])[1]
        args = [test]
        # run the script
        _ = subprocess.run([_python, script] + args, cwd = cwd, capture_output = True, text = True)
        generated_file = f'../../data_dictionary/v{_version}/skeleton_data_dictionary.json'
        # check the result
        corresponding_assertion = assertion_files[assertion_files.index(f"{test.replace('test_data', 'assertion_files').replace('../supplementary_files/tests/', './')}")]
        test_result = validate_assertion(generated_file, corresponding_assertion, filetype = 'json')
        # remove the generated file 
        os.remove(generated_file)
        if not test_result: fail_count += 1 
        result += f"\n\tTEST #{test_num + 1}: {test_name}...RESULT: {'passed' if test_result else 'FAILED'}"
    
    result += f'\n\tOVERVIEW: Total skeleton_dictionary tests failed --> {fail_count}'
    return result 

def data_dictionary_tests(test_data: dict) -> str: 
    ''' Runs the tests for the process_dictionary.py script.

    Parameters
    ----------
    test_data: dict 
        The data for the data dictionary testing.
    
    Returrns 
    --------
    str
        The output string for the test case results.
    '''
    script = os.path.split(test_data['script_path'])[1]
    assertion_files = test_data['assertion_files']
    test_files = [f"{test_tmp.replace('./', '../supplementary_files/tests/')}" for test_tmp in test_data['data_files']]
    cwd = '../../data_dictionary'
    result = 'DATA DICT TEST RESULTS:'
    fail_count = 0 

    # run each test
    for test_num, test in enumerate(test_files):
        test_name = os.path.split(os.path.splitext(test)[0])[1]
        args = [test, '-o', f'{_tmp_output_path}/data_dict_test.json']
        # run the script
        _ = subprocess.run([_python, script] + args, cwd = cwd, capture_output = True, text = True)
        generated_file = f'../../data_dictionary/data_dict_test.json'
        # check the result
        correspdonding_assertion = assertion_files[assertion_files.index(f"{test.replace('test_data', 'assertion_files').replace('../supplementary_files/tests/', './')}")]
        test_result = validate_assertion(generated_file, correspdonding_assertion, filetype = 'json')
        # remove the generated file
        os.remove(generated_file)
        if not test_result: fail_count += 1
        result += f"\n\tTEST #{test_num + 1}: {test_name}...RESULT: {'passed' if test_result else 'FAILED'}"
    
    result += f'\n\tOVERVIEW: Total data_dictionary tests failed --> {fail_count}'
    return result 

def validate_data_tests(test_data: dict) -> str:
    ''' Runs the tests for the validate_data.py script.

    Parameters
    ----------
    test_data: dict 
        The data for the data validation testing.

    Returns
    -------
    str
        The output string for the test case results.
    '''
    script = os.path.split(test_data['script_path'])[1]
    assertion_files = test_data['assertion_files']
    test_files = [f"{test_tmp.replace('./', '../supplementary_files/tests/')}" for test_tmp in test_data['data_files']]
    cwd = '../../schema'
    result = 'DATA VALIDATION (SCHEMA) RESULTS:'
    fail_count = 0

    # run each test
    for test_num, test in enumerate(test_files):
        test_name = os.path.split(os.path.splitext(test)[0])[1]
        args = [test, f'v{_version}/biomarker_schema.json']
        # run the script
        output = subprocess.run([_python, script] + args, cwd = cwd, capture_output = True, text = True)
        # check the stdout for the result
        validation_result = True if 'Validation successful.' in output.stdout else False
        # read in the assertion txt file 
        correspdonding_assertion = assertion_files[assertion_files.index(f"{test.replace('test_data', 'assertion_files').replace('../supplementary_files/tests/', './').replace('.json', '.txt')}")]
        with open(correspdonding_assertion, 'r') as f:
            assertion = f.read()
        # check if the result matches the assertion
        if validation_result and 'Validation successful.' in assertion:
            test_result = True
        elif not validation_result and 'Validation successful.' not in assertion: 
            test_result = True
        else:
            test_result = False
        if not test_result: fail_count += 1
        result += f"\n\tTEST #{test_num + 1}: {test_name}...RESULT: {'passed' if test_result else 'FAILED'}"
    
    result += f'\n\tOVERVIEW: Total validate_data tests failed --> {fail_count}'
    return result

def data_conversion_tests(test_data: dict) -> str:
    ''' Runs the tests for the data_conversion.py script.
    
    Parameters
    ----------
    test_data: dict 
        The data for the data conversion testing.
    
    Returns
    -------
    str
        The output string for the test case results.
    '''
    script = os.path.split(test_data['script_path'])[1]
    assertion_files = test_data['assertion_files']
    test_files = [f"{test_tmp.replace('./', '../../supplementary_files/tests/')}" for test_tmp in test_data['data_files']]
    cwd = '../../src/data_conversion'
    result = 'DATA CONVERSION RESULTS:'
    fail_count = 0
    venv_python = f'../{_python}'
    overall_count = 0

    # aggreagate loop tests for later processing
    loop_tests = []

    # run each test
    for test_num, test in enumerate(test_files):
        test_name = os.path.split(os.path.splitext(test)[0])[1]
        target_file_format = os.path.splitext(test)[0].split('_')[-1]
        if target_file_format == 'loop':
            loop_tests.append(test)
            continue
        test_file_format = os.path.splitext(test)[1]
        generated_file = f'{_tmp_output_path}data_conversion_test.{target_file_format}'
        args = [test, generated_file]
        # run the script 
        _ = subprocess.run([venv_python, script] + args, cwd = cwd, capture_output = True, text = True)
        # check the result
        correspdonding_assertion = assertion_files[assertion_files.index(f"{test.replace('test_data', 'assertion_files').replace('../../supplementary_files/tests/', './').replace(f'{test_file_format}', f'.{target_file_format}')}")]
        test_result = validate_assertion(f"{generated_file.replace('./', '../../src/data_conversion/')}", correspdonding_assertion, target_file_format)
        # remove the generated file
        os.remove(generated_file.replace('./', '../../src/data_conversion/'))
        if not test_result: fail_count += 1
        result += f"\n\tTEST #{test_num + 1}: {test_name}...RESULT: {'passed' if test_result else 'FAILED'}"
        overall_count += 1
    
    # run loop tests
    for test in loop_tests:
        test_name = os.path.split(os.path.splitext(test)[0])[1]
        source_file_format = os.path.splitext(test)[1].replace('.', '')
        if source_file_format.lower() == 'json':
            target_file_formats = ['tsv', 'json', 'tsv']
        elif source_file_format.lower() == 'tsv':
            target_file_formats = ['json', 'tsv', 'json']
        generated_files = [f'{_tmp_output_path}data_conversion_test_{idx + 1}.{target_file_format}' for idx, target_file_format in enumerate(target_file_formats)]
        args = [[test, generated_files[0]]] + [[generated_files[i-1], generated_files[i]] for i in range(1, len(generated_files))]
        for arg in args:
            _ = subprocess.run([venv_python, script] + arg, cwd = cwd, capture_output = True, text = True)
        # check the results 
        test_result_1 = validate_assertion(f"{generated_files[0].replace('./', '../../src/data_conversion/')}", f"{generated_files[2].replace('./', '../../src/data_conversion/')}", target_file_formats[0])
        test_result_2 = validate_assertion(f"{test.replace('../../supplementary_files/tests/v{_version}/data_conversion/', './')}", f"{generated_files[1].replace('./', '../../src/data_conversion/')}", target_file_formats[1])
        test_result = True if test_result_1 and test_result_2 else False
        # remove the generated files
        for generated_file in generated_files:
            os.remove(generated_file.replace('./', '../../src/data_conversion/'))
        if not test_result: fail_count += 1
        overall_count += 1
        result += f"\n\tTEST #{overall_count + 1}: {test_name}...RESULT: {'passed' if test_result else 'FAILED'}"

    result += f'\n\tOVERVIEW: Total data_conversion tests failed --> {fail_count}'
    return result

def main() -> None:

    global _version 
    global _log_path
    global _python
    global _tmp_output_path
    global SOURCE_FILES

    # grab configuration variables from config file 
    with open('../../conf.json', 'r') as f:
        config = json.load(f)
        _version = config['version']
        _log_path = config[_CONF_KEY]['log_path']
        _python = config[_CONF_KEY]['python_env']
        _tmp_output_path = config[_CONF_KEY]['tmp_output_path']
        SOURCE_FILES = config[_CONF_KEY]['source_files']
    
    setup_logging(_log_path)
    logging.info('################################## Start ##################################')
    user_args()

    # grab filepaths for test and assertion files
    test_data = get_test_files()
    # validate the structure of the test pairs 
    pairs_result = validate_test_data_pairs(test_data)
    if pairs_result == 1:
        print(f'Error matching test and assertion files, check logs for more information.')
        logging.info('---------------------------------- End ------------------------------------')
        sys.exit(1)
    
    # aggregated result log string
    results = '\n'

    # run skeleton_dictionary.py tests
    skeleton_dict_results = skeleton_dict_tests(test_data['skeleton_dictionary'])
    results += skeleton_dict_results
    print(skeleton_dict_results)

    # run the process_dictionary.py tests 
    data_dictionary_results = data_dictionary_tests(test_data['data_dictionary'])
    results += '\n' + data_dictionary_results
    print(data_dictionary_results)

    # run the validate_data.py tests 
    validate_data_results = validate_data_tests(test_data['schema'])
    results += '\n' + validate_data_results
    print(validate_data_results)

    # run the data_conversion.py tests
    data_conversion_results = data_conversion_tests(test_data['data_conversion'])
    results += '\n' + data_conversion_results
    print(data_conversion_results)

    # log aggregated results
    logging.info(results)

    logging.info('---------------------------------- End ------------------------------------')

if __name__ == '__main__':
    main() 