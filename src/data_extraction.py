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

    split_col_on_delim(df, split_column, new_col_name, delim, drop)
        Expands indicated column on a delimiter into multiple rows.  

    populate_col(source, target_col, dtype)
        Populates the biomarker dataframe.    

    _map_loinc()
        Map the corresponding loinc data based on the gene column (gene column must be populated first).

    _map_specimen()
        Map the specimen type based on the system column (system column must be populated first).
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

    def __init__(self) -> None:
        ''' Constructor, creates the initial empty biomarker dataframe. 
        '''

        self.biomarker_df = pd.DataFrame(columns = self.column_names)
        self.uniprot_df = self.read_in_data(input_file = self.uniprot_map, input_type = 'csv', delim = '\t')
        self.loinc_df = self.read_in_data(input_file = self.loinc_map, input_type = 'csv')
        _target_rows = self.loinc_df['COMPONENT'].str.contains('gene targeted mutation analysis', case = False, na = False)
        self.loinc_df = self.loinc_df[_target_rows]
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
        df[new_col_name] = df[new_col_name].str.strip()
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

        if target_col == 'gene': 
            self._map_loinc()
            self._map_uniprot()
            self._map_specimen()
        elif target_col == 'disease': 
            self._map_disease()
            self._map_doid()
    
    def _map_loinc(self) -> None: 
        ''' Map the corresponding loinc data based on the gene column (gene column must be populated first).
        '''

        if self.biomarker_df['gene'].isna().all():
            raise AttributeError('Gene column must be populated first.')

        loinc_dict = self.loinc_df.set_index('first_word')['LOINC_NUM'].to_dict() 
        loinc_series = self.biomarker_df['gene'].map(loinc_dict)
        self.populate_col(source = loinc_series, target_col = 'loinc_code')

        system_dict = self.loinc_df.set_index('LOINC_NUM')['SYSTEM'].to_dict()
        system_series = self.biomarker_df['loinc_code'].map(system_dict)
        self.populate_col(source = system_series, target_col = 'system')
    
    def _map_uniprot(self) -> None:
        '''
        '''

        if self.biomarker_df['gene'].isna().all():
            raise AttributeError('Gene column must be populated first.')

        gene_to_uniprot_dict = dict(zip(self.uniprot_df['Gene Names'].str.lower().str.strip(), self.uniprot_df['Entry']))
        gene_to_uniprot_series = self.biomarker_df['gene'].str.lower().str.strip().map(gene_to_uniprot_dict).fillna('Null')
        self.populate_col(source = gene_to_uniprot_series, target_col = 'uniprot')

        name_to_uniprot_dict = dict(zip(self.uniprot_df['Gene Names'].str.lower().str.strip(), self.uniprot_df['Protein names']))
        name_to_uniprot_series = self.biomarker_df['gene'].str.lower().str.strip().map(name_to_uniprot_dict)
        self.populate_col(source = name_to_uniprot_series, target_col = 'name')
    
    def _map_specimen(self) -> None: 
        ''' Map the specimen type based on the system column (system column must be populated first).
        '''

        if self.biomarker_df['system'].isna().all():
            raise AttributeError('System column must be populated first.')
        
        uberon_dict = self.uberon_map.set_index('system').apply(lambda row: f"{row['name']} (UN:{row['uberon_value']})", axis = 1).to_dict()
        uberon_series = self.biomarker_df['system'].map(uberon_dict)
        self.populate_col(source = uberon_series, target_col = 'specimen_type')

    def _map_disease(self) -> None:
        '''
        '''
    
    def _map_doid(self) -> None:
        '''
        '''

        if self.biomarker_df['disease'].isna().all():
            raise AttributeError('Disease column must be populated first.')

        doid_dict = self.doid_map.set_index('Disease Name')['DOID'].to_dict()
        doid_series = self.biomarker_df['disease'].str.lower().map(doid_dict)

        doid_synonym_dict = self.doid_map.set_index('synonym')['DOID'].to_dict()
        doid_synonym_series = self.biomarker_df['disease'].str.lower().map(doid_synonym_dict)
        
        combined_doid_series = doid_series.combine_first(doid_synonym_series)
        self.populate_col(source = combined_doid_series, target_col = 'doid')
    
