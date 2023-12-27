# Testing

Each portion of the project workflow can be thoroughly tested using the `test.py` script. Within each version subdirectory, there should be these subdirectories: 

| Directory                     | Test For                                          |
|-------------------------------|---------------------------------------------------| 
| `skeleton_dictionary/`        | Tests for the `skeleton_dictionary.py` script.    |
| `data_dictionary/`            | Tests for the `process_dictionary.py` script.     |
| `schema/`                     | Tests for the `validate_data.py` script.          |
| `data_conversion/`            | Tests for the `table_json_conversion.py` script.  |

Within each of these directories, there should be two subdirectories: 

1. `test_data/`: This directory contains the testing source data. 
2. `assertion_files/`: This should contain the expected output for each corresponding test data file. These are the files the output will be compared against to determine if the test was passed or not. The filename should match the corresponding test file name. 

To run the tests, change your current working directory to the `tests/` directory and run the `test.py` script: 

```
cd /supplementary_files/tests
python test.py 
```