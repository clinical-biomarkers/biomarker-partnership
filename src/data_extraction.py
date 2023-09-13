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
        delim : str, optional
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
        delim : str, optional
            The delimiter to split on (default value comma).
        drop : bool, optional
            Whether to drop the original column or not (default value True). 

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
        ''' Populates a biomarker dataframe column. 

        Parameters
        ----------
        source: pd.Series
            The data to populate the dataframe column. 
        target_col: str
            The column to enter the data in. 
        dtype: str, optional
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
            self._format_condition_name()

        if target_col in {'rs_id', 'name', 'gene'} and self.biomarker_df['assessed_biomarker_entity'].isna().any():
            if not (self.biomarker_df['rs_id'].isna().all() | self.biomarker_df['name'].isna().all() | self.biomarker_df['gene'].isna().all()):
                self._create_assessed_biomarker_entity()

    def map_x_ref(self, prefix: str = 'dbSNP:rs') -> None:
        ''' Maps the main_x_ref column with the prefix and rs_id number. 

        Parameters
        ----------
        prefix: str, optional
            Prefix to add before the rs_id. 
        '''

        if self.biomarker_df['rs_id'].isna().all():
            raise AttributeError('Rs_id column must be populated first.')

        rsid_nan_mask = self.biomarker_df['rs_id'].isna()
        x_ref_series = prefix + self.biomarker_df['rs_id'].astype('str')
        x_ref_series[rsid_nan_mask] = prefix + '<NA>'
        self.populate_col(source = x_ref_series, target_col = 'main_x_ref')
    
    def set_biomarker_status(self, val: str = 'presence of') -> None:
        ''' Sets the biomarker status column with a static string value. 

        Parameters
        ----------
        val: str, optional
            Value to populate the biomarker_status column with (default value 'presence of').
        '''
        
        bio_status_series = pd.Series(val, index = self.biomarker_df.index)
        self.populate_col(source = bio_status_series, target_col = 'biomarker_status')
    
    def set_best_biomarker_type(self, val: str = 'risk_biomarker') -> None:
        ''' Sets the best_biomarker_type column with a static string value.

        Parameters
        ----------
        val: str, optional 
            Value to populate the best_biomarker_type column with (default value 'risk_biomarker).
        '''

        biomarker_type_series = pd.Series(val, index = self.biomarker_df.index)
        self.populate_col(source = biomarker_type_series, target_col = 'best_biomarker_type')

    def set_assessed_entity_type(self, val: str = 'gene') -> None:
        ''' Sets the assessed_entity_type column with a static string value. 

        Parameters
        ----------
        val: str, optional 
            Value to populate the assessed_entity_type column with (default value 'gene').
        '''

        assessed_entity_series = pd.Series('gene', index = self.biomarker_df.index)
        self.populate_col(source = assessed_entity_series, target_col = 'assessed_entity_type')
    
    def finalize_dataframe(self) -> None:
        ''' Drop the extra mapping rows not needed for the finalized dataframe. 
        '''

        self.biomarker_df.drop(['rs_id', 'gene', 'disease', 'uniprot', 'name', 'system', 'doid', 'mutation', 'variation'], inplace = True)

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
        ''' Map the corresponding uniprot data based on the gene column (gene column must be populated first).
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
        ''' TODO 
        '''

        if self.biomarker_df['disease'].isna().all():
                raise AttributeError('Disease column must be populated first.')
        
    def _map_doid(self) -> None:
        ''' Map the corresponding doid data based on the disease column (disease column must be populated first).
        '''

        if self.biomarker_df['disease'].isna().all():
                raise AttributeError('Disease column must be populated first.')

        doid_dict = self.doid_map.set_index('Disease Name')['DOID'].to_dict()
        doid_series = self.biomarker_df['disease'].str.lower().map(doid_dict)

        doid_synonym_dict = self.doid_map.set_index('synonym')['DOID'].to_dict()
        doid_synonym_series = self.biomarker_df['disease'].str.lower().map(doid_synonym_dict)
        
        combined_doid_series = doid_series.combine_first(doid_synonym_series)
        self.populate_col(source = combined_doid_series, target_col = 'doid')
        
    def _format_condition_name(self) -> None:
        ''' Formats the condition name with the corresponding doid value (disease and doid columns must be populated first).
        '''

        if self.biomarker_df['disease'].isna().all():
            raise AttributeError('Disease column must be populated first.')
        if self.biomarker_df['doid'].isna().all():
            raise AttributeError('Doid column must be populated first.')
        
        condition_name_series = self.biomarker_df['disease'].str.lower() + ' (DOID:' + self.biomarker_df['doid'].astype(str) + ')'
        condition_name_series = np.where(self.biomarker_df['doid'].notna(), condition_name_series, self.biomarker_df['disease'].str.lower())
        self.populate_col(source = condition_name_series, target_col = 'condition_name')
        
    def _create_assessed_biomarker_entity(self) -> None:
        ''' Creates the assessed_biomarker_entity value and populates the column (rs_id, name, and gene columns must be populated first).
        '''

        if self.biomarker_df['rs_id'].isna().all():
            raise AttributeError('Rs_id column must be populated first.')
        if self.biomarker_df['name'].isna().all():
            raise AttributeError('Name column must be populated first.')
        if self.biomarker_df['gene'].isna().all():
            raise AttributeError('Gene column must be populated first.')

        bio_entity_series = 'mutation in ' + self.biomarker_df['name'] + '(' + self.biomarker_df['gene'] + ')'
        entity_mask = self.biomarker_df['rs_id'].notna()
        bio_entity_series[entity_mask] = 'rs' + self.biomarker_df['rs_id'][entity_mask].astype(int).astype(str) + \
                                        ' mutation in ' + self.biomarker_df['name'][entity_mask].str.lower() + \
                                        ' (' + self.biomarker_df['gene'][entity_mask] + ')'
        self.populate_col(source = bio_entity_series, target_col = 'assessed_biomarker_entity')