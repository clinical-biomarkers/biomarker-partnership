# Data Dictionary

The data dictionary is used to aid in the integration of biomarker partnership data from many disparate sources. The data dictionary sets the format and standard for all data incororated into the project.

- [Generating a Schema](#generating-a-schema)
- [Data Dictionary Usage](#data-dictionary-structure)
    - [Basic Top Level Element](#basic-top-level-element)
    - [Nested Elements](#nested-elements)

## Generating a Schema

If applicable, in the project root directory, update the `conf.json` file with the updated version number. 

Make sure the corresponding schema directory exist prior to running `process_dictionary.py`. While inside the project root directory:

```bash
mkdir schema/<VERSION>
```

The `process_dictionary.py` can take these arguments:

```
Positional arguments:
    file_path           filepath of the data dictionary JSON to convert

Optional arguments 
    -h --help           show the help message and exit
    -v --version        show current version number and exit
```

Move your current working directory to this directory and run the `process_dictonary.py` script passing in the filepath to the data dictionary JSON you want to process. 

```bash
cd data_dictionary
python process_dictionary.py <FILEPATH/TO/DICTIONARY>
```

## Data Dictionary Structure 

The data dictionary represents a simplified structure of the eventual JSON schema. The `process_dictionary.py` script is agnostic to the actual fields and nested structure of the data dictionary. This provides a simplified way to make changes to the data model rather than directly and manually updating, maintaining, and testing a complex JSON schema. 

#### Basic Top Level Element

The structure of a basic top level element in the data dictionary looks like this:

```json
"biomarker_id": {
    "description": "Biomarker identifier. This will be automatically assigned when the data is incorporated.",
    "type": "string",
    "required": {
        "requirement": false,
        "conditionals": [],
        "exclusions": []
    }, 
    "example": ["A0034"],
    "pattern": "^.*$",
    "pattern_notes": "Matches on an entire line, regardless of content, including an empty line."
}
```

**Elements:**
- *Field name* - The name of the field (Ex. `"biomarker_id"`).
    - *Description* - A description of the field. 
    - *Type* - Type for the field. 
    - *Required* - Metadata for the field requirement conditions.
        - *Requirement* - Whether the field is required or not. This value can accept `true`, `false`, or `conditional`. 
        - *Conditionals* - If `requirement` is set to `conditional`, then conditional requirements can be added. If a field's requirement is conditional on another field (or fields) being present, you can add those field names here. 
        - *Exclusions* - If `requirement` is set to `conditional`, then exclusion requirements can be added. If a field's presence is mutually exclusive based on another field (or fields) being present, you can add those field names here. 
    - *Example* - An example for the field (supports multiple examples).
    - *Pattern* - A regex pattern to validate the data against.
    - *Pattern notes* - This field is optional (and is not used by the `process_dictionary.py` script), a description of the regex pattern. 

#### Nested Elements 

The data dictionary also supports nested elements. Nested elements can be either contained as objects or arrays. 

The structure of a nested element in an array looks like this:

```json
"biomarker_component": {
    "description": "List of biomarker components.",
    "type": "array",
    "required": {
        "requirement": true,
        "conditionals": [],
        "exclusions": []
    },
    "items": [
        {
            "biomarker": {
                "description": "Change observed in an entity that differs from normal processes.",
                "type": "string",
                "required":{
                    "requirement": true,
                    "conditionals": [],
                    "exclusions":[]
                },
                "example": ["presence of rs1800562 mutation"],
                "pattern": "^.+$",
                "pattern_notes": "Matches on an entire line, regardless of content, not including an empty line."
            }
        },
        {
            "assessed_biomarker_entity": {
                "description": "Biomarker entity and common name/gene symbol/short name.",
                "type": "string",
                "required": {
                    "requirement": true,
                    "conditionals": [],
                    "exclusions": []
                },
                "example": ["rs1800562 mutation in hereditary haemochromatosis protein (hereditary hemochromatosis protein) (HFE)"],
                "pattern": "^.+$",
                "pattern_notes": "Matches on an entire line, regardless of content, not including an empty line."
            }
        },
        ... // more elements here
    ]
}
```

**Elements:**  
The basic structure is essentially the same as the single top level element with the only difference being the parent element metadata. The parent element still requires the `description`, `type`, and `required` data. The parent element also requires the `items` keyword that contains the nested elements. The `items` value must be an array, even if the parent `type` is an object. This is required because the `process_dictionary.py` script must be agnostic to the actual fields itself, allowing it to loop through nested objects and dynamically generate the JSON schema. 
