import pandas as pd 
import os 

class DataExtractionHelper: 
    ''' Class for the data extraction helper. 

    Class Attributes
    ----------------
    column_names : List[str]
        Column names for the final biomarker Dataframe. 
    file_types : List[str]
        File types that this helper supports. 

    Methods
    -------
    __init__()
        Constructor. 
    
    read_in_data(input_file, input_type, delim) 
        Reads in the data from the user inputted file path and returns it as a Pandas DataFrame. 

    split_col_on_delim(df, split_column, new_col_name, delim)
        Expands indicated column on a delimiter into multiple rows.  

    populate_col(source, target_col)
        Populates the biomarker dataframe.

    format_doid(source, prefix)
        Formats the Disease Ontology Identifiers (DOIDs) and populates into main_x_ref column in biomarker dataframe.
    '''

    column_names = ['biomarker_id', 'main_x_ref', 'assessed_biomarker_entity', 'biomarker_status',
                    'best_biomarker_type', 'specimen_type', 'loinc_code', 'condition_name',
                    'assessed_entity_type', 'evidence_source', 'notes', 'rs_id']
    file_types = {'csv', 'txt'}

    def __init__(self) -> None:
        ''' Constructor, creates the initial empty biomarker dataframe. 
        '''

        self.biomarker_df = pd.DataFrame(columns = self.column_names)
    
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
            return pd.read_csv(input_file)
        elif input_type.strip().lower() == 'txt':
            return pd.read_csv(input_file, sep = delim)
    
    def split_col_on_delim(self, df: pd.DataFrame, split_column: str, new_col_name: str, delim: str = ',') -> pd.DataFrame:
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
        return df.drop(split_column, axis = 1)
        
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
    
    def format_doid(self, source: str, prefix: str):
        ''' Formats the Disease Ontology Identifiers (DOIDs) and populates into main_x_ref column in biomarker dataframe.

        Parameters
        ----------
        source: str
            The source column in the biomarker_df. 
        prefix: str
            Prefix for the DOID. 
        '''

        mask = self.biomarker_df[source].isna()
        formatted_series = prefix + self.biomarker_df[source].astype('str')
        formatted_series[mask] = prefix + '<NA>'
        self.biomarker_dfk['main_x_ref'] = formatted_series
