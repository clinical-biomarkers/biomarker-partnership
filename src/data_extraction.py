import pandas as pd 
import os 
import numpy as np

class DataExtractionHelper: 
    ''' Class for the data extraction helper. 

    Class Attributes
    ----------------
    column_names : List[str]
        Column names for the final biomarker Dataframe. 
    file_types : List[str]
        File types that this helper supports. 
    uniprot_map : str
        File path to the Uniprot mapping file. 
    loinc_map : str
        File path to the loinc mapping file. 
    uberon_map : str
        File path to the uberon mapping file.   
    doid_map : str
        File path to the doid mapping file.
    disease_map : dict
        Map for exact match common disease terms.  
    disease_prefix_map : dict
        Map for disease terms tha tare identified by prefixes rather than exact matches. 

    Instance Attributes
    -------------------
    biomarker_df : pd.Dataframe
        Target dataframe.
    uniprot_df : pd.Dataframe
        Uniprot mapping data. 
    loinc_df : pd.Dataframe
        Loinc mapping data. 
    uberon_df : pd.Dataframe
        Uberon mapping data.
    doid_df : pd.Dataframe
        Doid mapping data. 

    Methods
    -------
    __init__()
        Constructor. 
    
    read_in_data(input_file, input_type, delim) 
        Reads in the data from the user inputted file path and returns it as a Pandas DataFrame. 

    split_col_on_delim(df, split_column, new_col_name, delim)
        Expands indicated column on a delimiter into multiple rows.  

    populate_col(source, target_col, dtype)
        Populates the biomarker dataframe.    
    '''

    column_names = ['biomarker_id', 'main_x_ref', 'assessed_biomarker_entity', 'biomarker_status',
                    'best_biomarker_type', 'specimen_type', 'loinc_code', 'condition_name',
                    'assessed_entity_type', 'evidence_source', 'notes', 'rs_id', 'gene', 'disease', 
                    'uniprot', 'name', 'system', 'doid', 'mutation', 'variation']
    file_types = {'csv', 'txt'}
    uniprot_map = '../mapping_data/uniprot_names.tsv' # path is set for jupyter notebook (notebooks have a different default cwd vs .py files)
    loinc_map = '../mapping_data/Loinc.csv' # path is set for jupyter notebook (notebooks have a different default cwd vs .py files)
    uberon_map = '../mapping_data/uberon_system.csv' # path is set for jupyter notebook (notebooks have a different default cwd vs .py files)
    doid_map = '../mapping_data/doid_table.csv' # path is set for jupyter notebook (notebooks have a different default cwd vs .py files)
    disease_map = {
        'hereditary cancer-predisposing syndrome': 'cancer',
        'familial cancer of breast': 'breast cancer',
        'breast adenocarcinoma': 'breast cancer',
        'carcinoma of colon': 'colon cancer',
        'gastric cancer': 'stomach cancer',
        'hepatocellular carcinoma': 'liver cancer',
        'palmoplantar keratoderma-XX sex reversal-predisposition to squamous cell carcinoma syndrome': 'squamous cell carcinoma',
        'hurthle cell carcinoma of thyroid': 'thyroid gland cancer',
        'endometrial carcinoma': 'endometrial cancer',
        'gastric cancer': 'stomach cancer',
        'familial colorectal cancer': 'colorectal cancer'
    }
    disease_prefix_map = {
        'breast cancer, susceptibility to': 'breast cancer',
        'breast cancer': 'breast cancer',
        'colorectal cancer': 'colorectal cancer',
        'pancreatic cancer, susceptibility to': 'pancreatic cancer',
        'prostate cancer, hereditary': 'prostate cancer', 
        'lung cancer, susceptibility to': 'lung cancer', 
        'lung cancer': 'lung cancer', 
        'mismatch repair cancer syndrome': 'mismatch repair cancer syndrome', 
        'papillary renal cell carcinoma type': 'kidney cancer',
        'esophageal squamous cell carcinoma': 'esophageal cancer',
        'thyroid cancer, nonmedullary': 'thyroid gland cancer'
    }

    def __init__(self) -> None:
        ''' Constructor, creates the initial empty biomarker dataframe. 
        '''

        self.biomarker_df = pd.DataFrame(columns = self.column_names)
        self.uniprot_df = self.read_in_data(input_file = self.uniprot_map, input_type = 'csv', delim = '\t')
        self.loinc_df = self.read_in_data(input_file = self.loinc_map, input_type = 'csv')
        self.loinc_df['first_word'] = self.loinc_df['COMPONENT'].str.split(' ').str[0]
        self.uberon_map = self.read_in_data(input_file = self.uberon_map, input_type = 'csv')
        self.doid_map = self.read_in_data(input_file = self.doid_map, input_type = 'csv')
        self.doid_map = self.split_col_on_delim(self.doid_map, 'Exact Synonyms', 'synonym', drop = False)
    
    def read_in_data(self, input_file: str, input_type: str, delim: str = ',') -> pd.DataFrame:
        ''' Reads in the data from the user inputted file path and returns a Pandas Dataframe. 

        Parameters
        ----------
        input_file : str
            File path to the input file.
        input_type : str 
            File type of the input file.
        delim : str
            If a non-csv file, the delimiter (default value comma). 
        
        Returns
        -------
        pd.DataFrame
            The resulting dataframe from the file load. 
        '''
        
        if input_type.strip().lower() not in self.file_types:
            raise ValueError('Input file type invalid.')
        if not os.path.isfile(f'{input_file}'):
            raise ValueError(f'Input file does not exist. Recheck inputted file path/name.')
        
        if input_type.strip().lower() == 'csv':
            return pd.read_csv(input_file, sep = delim)
        elif input_type.strip().lower() == 'txt':
            return pd.read_csv(input_file, sep = delim)
    
    def split_col_on_delim(self, df: pd.DataFrame, split_column: str, new_col_name: str, delim: str = ',', drop: bool = True) -> pd.DataFrame:
        ''' Expands indicated column on a delimiter into multiple rows.  

        Parameters
        ----------
        df : pd.Dataframe
            The dataframe to work with.
        split_column : str
            The column to split.
        new_col_name : str
            The name of the new column.
        delim : str
            The delimiter to split on (default value comma).
        drop : bool
            Whether to drop the original column or not. 

        Returns
        -------
        pd.DataFrame 
            The resulting dataframe after the column was split into multiple rows. 
        '''

        if split_column not in df.columns:
            raise ValueError('Passed split_column does not exist in the dataframe.')
        
        df = df.copy()
        df[new_col_name] = df[split_column].str.split(delim)
        df = df.explode(new_col_name)
        if drop:
                return df.drop(split_column, axis = 1)
        else:
            return df
        
    def populate_col(self, source: pd.Series, target_col: str, dtype: str = 'str') -> None:
        ''' Populates the biomarker dataframe. 

        Parameters
        ----------
        source: pd.Series
            The data to populate the dataframe column. 
        target_col: str
            The column to enter the data in. 
        dtype: str
            Data type of target column (default value string). 
        '''
        
        if target_col not in self.column_names:
            raise ValueError('Target column invalid.')
        
        self.biomarker_df[target_col] = source.astype(dtype)