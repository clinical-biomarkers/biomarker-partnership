import pandas as pd 
import os 

class DataExtractionEngine: 
    ''' Class for the main data extraction engine. 

    Class Attributes
    ----------------
    column_names : List[str]
        Column names for the output Dataframe. 
    file_types : Set{str}
        Set of valid file input types. 

    Instance Attributes
    -------------------
    raw_data : pd.DataFrame
        DataFrame containing raw data loaded in from input file. 

    Methods
    -------
    __init__(input_file, input_type)
        Constructor. 
    
    read_in_data(input_file, input_type) 
        Reads in the data from the user inputted file path and returns it as a Pandas DataFrame. 
    '''

    column_names = ['biomarker_id', 'main_x_ref', 'assessed_biomarker_entity', 'biomarker_status',
                    'best_biomarker_type', 'specimen_type', 'loinc_code', 'condition_name',
                    'assessed_entity_type', 'evidence_source', 'notes']
    file_types = {'csv'}

    def __init__(self, input_file: str, input_type: str = 'csv') -> None:
        ''' Constructor. 

        Parameters
        ----------
        input_file : str
            File path to the input file. 
        input_type : str
            File type of the input file (default value is csv). 
        '''

        # make sure inputs are valid 
        if input_type not in self.file_types:
            raise ValueError('Input file type invalid.')
        if not os.path.isfile(f'./{input_file}'):
            raise ValueError(f'Input file does not exist. Recheck inputted file path/name.')
        
        # load in data 
        self.raw_data = self.read_in_data(input_file, input_type)
    
    def read_in_data(self, input_file: str, input_type: str) -> pd.DataFrame:
        ''' Reads in the data from the user inputted file path and returns a Pandas Dataframe. 

        Parameters
        ----------
        input_file : str
            File path to the input file (pre-validated in contructor).
        input_type : str 
            File type of the input fiel (pre-validated in constructor).
        '''

        return pd.read_csv(input_file)
    


