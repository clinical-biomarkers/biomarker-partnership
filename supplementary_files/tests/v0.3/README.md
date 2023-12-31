# Sample Data for Testing

- [skeleton_dictionary tests](#skeleton-dictionary)
- [data_dictionary tests](#data-dictionary)
- [data_conversion tests](#data-conversion)

## Skeleton Dictionary

These files test the `skeleton_dictionary.py` script for generating skeleton data dictionaries. 

| File                          | Testing For                                                       |
|-------------------------------|-------------------------------------------------------------------|
| `simple_structure.json`       | Testing for a simple top level single element.          |
| `two_element_simple_structure.json` | Testing for multiple, simple top level elements.  |
| `single_object_field.json`        | Testing for a single top level object element.                              |
| `single_list_field.json`      | Testing for a single top level list element.    |
| `single_object_single_child.json` | Testing for a single top level object field with a simple nested child field.  | 
| `single_list_single_child.json`  | Testing for a single top level list field with a simple nested child field.    |
| `list_and_object_fields.json` | Testing for both a top level list and object fields with simple nested child fields. |
| `parent_list_nested_list.json`            | Testing for a list element with a nested list element child.  |
| `parent_object_nested_object.json` | Testing for an object element with a nested object element child. |
| `parent_list_nested_objects.json` | Testing for a top level list element with multiple nested object children elements. | 
| `parent_object_nested_list_of_objects.json` | Testing for a top level object element with a list child element containing primitive fields. |
| `complex_structure.json`      | Testing for a complex structure example, encompassing all of the cases in the previous test cases. | 

## Data Dictionary 

These files test the `process_dictionary.py` script for generating the corresponding JSON schema's using the data dictionary. 

| File                          | Testing For                                                   |
|-------------------------------|---------------------------------------------------------------|
| `simple_dict.json`            | Testing for the simplest possible data dictionary, a single top level element.    |
| `two_element_simple_structure.json` | Testing for multiple, simple, top level elements.   | 
| `object_field_primitive_child_elements.json` | Testing for a single object field that contains multiple primitive child elements where one is required and the other is not. |
| `object_field_array_child_elements.json`     | Testing for a single object field that contains an array field, which containing multiple child elements with various requirement levels. |

## Data Conversion

| File                                              | Total Entries | Component<br>Entries | Specimen<br>Entries | Component Evidence<br>Source Entries | Top Level Evidence<br>Source Entries | Condition or<br>Exposure Agent |
|---------------------------------------------------|---------------|----------------------|---------------------|--------------------------------------|--------------------------------------|--------------------------------|
| `single_entry`                                    | 1             | 1                    | 1                   | 1                                    | 1                                    | Condition                      |
| `single_entry_multiple_components`                | 1             | 2                    | 1                   | 1                                    | 1                                    | Condition                      |
| `single_entry_no_specimen`                        | 1             | 1                    | 0                   | 1                                    | 1                                    | Condition                      |                  
| `single_entry_no_specimen_mult_comp_evidence`     | 1             | 1                    | 0                   | 2                                    | 1                                    | Condition                      |
| `single_entry_multiple_specimen`                  | 1             | 1                    | 2                   | 1                                    | 1                                    | Condition                      |
| `single_entry_multiple_comp_evidence`             | 1             | 1                    | 1                   | 2                                    | 1                                    | Condition                      | 