# Formatting/Contributing Data 

Notes for formatting your data for contribution to the Biomarker Partnership. 

## Initial Curation 

You can contribute data in multiple formats. The recommended path is to initially curate your data in the TSV table format. For reference on the correct formatting/structure for the TSV, you can reference [this](https://hivelab.biochemistry.gwu.edu/biomarker-partnership/data/BCO_000435) dataset. The column headers should match. The `biomarker_id` value can be any string value that uniquely identifies which rows are a part of the same biomarker entry. For questions on what any of the different fields represent, refer to the latest [data dictionary](../../data_dictionary/).

Once the initial data is curated, you can convert back and forth between the flat TSV format and the JSON data model format by following the [data conversion documentation](../../src/data_conversion/README.md).

## Biomarker Assessed Entity ID Mapping

In order to standardize data for unique `biomarker_id` assignment, these resouces/databases were chosen as the resources for each `assessed_entity_type` (by order of preference/availability): 

| Assessed Entity Type | Resource (in order of preference/availability) |
|----------------------|------------------------------------------------|
| Carbohydrate         | Chemical Entities of Biological Interest (ChEBI) |
| Cell                 | Cell Ontology (CO) -> National Cancer Institute Thesaurus (NCIt) |
| Chemical Element     | PubChem (PCCID) -> National Cancer Institute Thesaurus (NCIt) |
| DNA                  | National Cancer Institute Thesaurus (NCIt) |
| Gene                 | NCBI |
| Gene (mutation)      | NCBI dbSNP |
| Glycan               | GlyTouCan Accession (GTC) -> PubChem (PCCID) |
| Lipoprotein          | Chemical Entities of Biological Interest (ChEBI) |
| Metabolite           | Chemical Entities of Biological Interest (ChEBI) |
| Peptide              | Protein Ontology (PRO) |
| Protein              | Uniprot (UPKB) -> Protein Data Bank (PDB) -> Protein Ontology (PRO) -> National Cancer Institute Thesaurus (NCIt)|
| Protein Complex      | Protein Ontology (PRO) -> Gene Ontology (GO) |
| RNA                  | RNA Central (RNAC) |
| miRNA                | miRBase (MRB) |

For `condition` data, our primary database is the Disease Ontology (DOID). 

If your data has new entity types that are not listed above, reach out to the repository maintainers. 

