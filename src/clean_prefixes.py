''' This script can be used to clean prefix mismatches in table formatted data. For example, 'UN' in the specimen_id column will be remapped to 'UBERON' and 'PMID'
in the evidence_source column will be remapped to 'PUBMED'.

Usage: clean_prefixes.py [options]

    Positional arguments:
        source_filepath     filepath of the source file 
        target_filepath     filepath of the target file 
    
    Optional arguments: 
        -h --help           show the help message and exit 
'''

import argparse
import pandas as pd
import os
import sys
import json

# prefix map 
PREFIX_MAP_PATH = '../mapping_data/prefix_map.json'

def main():

    # argument parser
    parser = argparse.ArgumentParser(
        prog = 'biomarker-partnership prefix cleaner',
        usage = 'python clean_prefixes.py [options] source_filepath target_filepath'
    )

    # add arguments
    parser.add_argument('source_filepath', help = 'filepath of the source table to clean')
    parser.add_argument('target_filepath', help = 'filepath of the target table to write to')

    # print out help if script is called without enough arguments
    if len(os.sys.argv) <= 2:
        sys.argv.append('-h')
    
    options = parser.parse_args()
    
    # read prefix map
    with open(PREFIX_MAP_PATH) as f:
        prefix_map = json.load(f)
    
    # read in the source table
    source_table = pd.read_csv(options.source_filepath, sep = '\t')

    ### clean specimen_id column 
    source_table['specimen_id'] = source_table['specimen_id'].apply(lambda x: x.replace(x.split(':')[0], prefix_map[x.split(':')[0].lower()]) if pd.notnull(x) and x.split(':')[0].lower() in prefix_map else x)

    ### clean evidence_source column
    source_table['evidence_source'] = source_table['evidence_source'].apply(lambda x: x.replace(x.split(':')[0], prefix_map[x.split(':')[0].lower()]) if pd.notnull(x) and x.split(':')[0].lower() in prefix_map else x)

    # write the cleaned table to the target filepath
    source_table.to_csv(options.target_filepath, sep = '\t', index = False)

if __name__ == '__main__': 
    main() 