# v0.3 Release Notes

## Data Changes
- Data dictionary has been overhauled to capture the data model changes acccording to the [RFC](../../supplementary_files/documents/Master_Biomarker_Partnership_Data_Model_RFC.pdf). 

## Data Dictionary Structure Changes
- Data dictionary file type changed to json to reflect more complex structure. 
- Data dictionary includes standardized metadata for each field: 
    - For nested fields (arrays and objects), metadata includes description of, data type, and requirement conditions.
    - For primitive fields (string, integers, etc), metadata includes description, data type, requirement condition, domain (what values the field accepts), examples, and validation patterns.