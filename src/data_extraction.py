import pandas as pd 

class DataExtractionEngine: 
    ''' Class for the main data extraction engine. 

    Class Attributes
    ----------------
    column_names : List[str]
        Column names for the output Dataframe. 

    Instance Attributes
    -------------------

    Methods
    -------
    __init__(input_file, input_type)
        Constructor. 
    '''

    column_names = ['biomarker_id', 'main_x_ref', 'assessed_biomarker_entity', 'biomarker_status',
                    'best_biomarker_type', 'specimen_type', 'loinc_code', 'condition_name',
                    'assessed_entity_type', 'evidence_source', 'notes']

    def __init__(self, input_file: str, input_type: str = 'csv') -> None:
        ''' Constructor. 

        Parameters
        ----------
        input_file : str
            File path to the input file. 
        input_type : str
            File type of the input file (default value is csv). 
        '''

        
