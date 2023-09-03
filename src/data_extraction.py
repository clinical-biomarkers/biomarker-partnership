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

    split_col_on_delim(df, split_column, new_col_name, delim)
        Expands indicated column on a delimiter into multiple rows.  

    populate_col(source, target_col)
        Populates the biomarker dataframe.

    format_doid(source, prefix)
        Formats the Disease Ontology Identifiers (DOIDs) and populates into main_x_ref column in biomarker dataframe.
    
    map_uniprot()
        Maps the corresponding uniprot entry for each gene. 

    map_loinc()
        Map the corresponding loinc data. 
    
    map_uberon()
        Map the corresponding uberon data. 
    
    map_doid()
        Map the corresponding doid based on the disease column and populate the condition name.

    map_mutations(mutation_map: dict, variant_map: dict)
        Map mutations and variants using the rs_id column.       
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
        self.uberon_map = self.read_in_data(input_file = self.uberon_map, input_type = 'csv')
        self.doid_map = self.read_in_data(input_file = self.doid_map, input_type = 'csv')
    
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
    
    def format_doid(self, source: str, prefix: str) -> None:
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
        self.populate_col(source = formatted_series, target_col = 'main_x_ref')

    def map_uniprot(self) -> None:
        ''' Maps the corresponding uniprot entry for each gene. 
        '''

        if self.biomarker_df['gene'].isna().all():
            raise AttributeError('Gene column must be populated first.')

        gene_to_uniprot = dict(zip(self.uniprot_df['Gene Names'].str.lower().str.strip(), self.uniprot_df['Entry']))
        gene_to_uniprot_series = self.biomarker_df['gene'].str.lower().str.strip().map(gene_to_uniprot).fillna('Null')
        self.populate_col(source = gene_to_uniprot_series, target_col = 'uniprot')

        name_to_uniprot = dict(zip(self.uniprot_df['Gene Names'].str.lower().str.strip(), self.uniprot_df['Protein names']))
        name_to_uniprot_series = self.biomarker_df['gene'].str.lower().str.strip().map(name_to_uniprot)
        self.populate_col(source = name_to_uniprot_series, target_col = 'name')
    
    def map_loinc(self) -> None:
        ''' Map the corresponding loinc data. 
        '''

        if self.biomarker_df['gene'].isna().all():
            raise AttributeError('Gene column must be populated first.')
        
        self.loinc_df['first_word'] = self.loinc_df['COMPONENT'].str.split(' ').str[0]
        loinc_dict = self.loinc_df.set_index('first_word')['LOINC_NUM'].to_dict()
        loinc_series = self.biomarker_df['gene'].map(loinc_dict)
        self.populate_col(source = loinc_series, target_col = 'loinc_code')

        system_dict = self.loinc_df.set_index('LOINC_NUM')['SYSTEM'].to_dict()
        system_series = self.biomarker_df['loinc_code'].map(system_dict)
        self.populate_col(source = system_series, target_col = 'system')

    def map_uberon(self) -> None:
        ''' Map the corresponding uberon data. 
        '''

        if self.biomarker_df['system'].isna().all():
            raise AttributeError('System column must be populated first')
        
        uberon_dict = self.uberon_map.set_index('system').apply(lambda row: row['name'] + ' (UN:' + str(row['uberon_value']) + ')', axis = 1).to_dict()
        uberon_series = self.biomarker_df['system'].map(uberon_dict)
        self.populate_col(source = uberon_series, target_col = 'specimen_type')
    
    def map_doid(self) -> None:
        ''' Map the corresponding DOID based on the disease column and populate the condition name. 
        '''

        if self.biomarker_df['disease'].isna().all():
            raise AttributeError('Disease column must be populated first')
        
        doid_dict = self.doid_map.set_index('Disease Name')['DOID'].to_dict()
        for idx, row in self.doid_map.iterrows():
            synonyms = str(row['Exact Synonyms']).split('|')
            for synonym in synonyms:
                doid_dict[synonym.lower()] = row['DOID']
        
        doid_series = self.biomarker_df['disease'].str.lower().map(doid_dict)
        self.populate_col(source = doid_series, target_col = 'doid')

        condition_name_series = self.biomarker_df['disease'].str.lower() + '(DOID:' + self.biomarker_df['doid'].astype(str) + ')'
        condition_name_series = np.where(self.biomarker_df['doid'].notna(), condition_name_series, self.biomarker_df['disease'].str.lower())
        self.populate_col(source = condition_name_series, target_col = 'condition_name') 

    def map_mutations(self, mutation_map: dict, variant_map: dict) -> None:
        ''' Map mutations and variants using the rs_id column.

        Parameters
        ----------
        mutation_map: dict
            Dictionary mapping the rs_id to the mutation names.
        variant_map: dict
            Dictionary mapping the rs_id to the variant names. 
        '''

        if self.biomarker_df['rs_id'].isna().all():
            raise AttributeError('Rs_id column must be populated first.')

        mutations_series = self.biomarker_df['rs_id'].map(mutation_map).fillna('Null')
        self.populate_col(source = mutations_series, target_col = 'mutation')

        variation_series = self.biomarker_df['rs_id'].map(variant_map).fillna('Null')
        self.populate_col(source = variation_series, target_col = 'variation')

        mask = self.biomarker_df['variation'].notna()
        self.biomarker_df['evidence_source'] = 'ClinVar'
        self.biomarker_df.loc[mask, 'evidence_source'] = "ClinVar|https://www.ncbi.nlm.nih.gov/clinvar/variation/" + self.biomarker_df['variation'] + "/?new_evidence=true"