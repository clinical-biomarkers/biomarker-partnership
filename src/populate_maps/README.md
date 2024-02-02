# Ontology Parsing 

For various fields as defined in the biomarker data model, supplemental data such as term synonyms, descriptions, citation data, and other metadata is utilized to support a comprehensive view of a specific biomarker entry. However, the unrolled and simplified TSV view format of the data does not include this supplementary metadata. To relieve the burden on researchers converting their table formatted data into our data model, data conversion code (documentation can be found [here](../data_conversion/)) supports API calls to various resources to automate the retrieval of various these various metadata fields. 

However, given the vast amount of disparate resources and databases that contain biological data of interest, not all resources can be supported. In addition, even for the resources that are supported, we want to reduce the amount of potentially duplicate and unneeded API calls to reduce code overhead and burden on client servers. The way the API calls work in the data conversion code follows a general structure: 
- For the specific resource, the local map (similar to a caching mechanism) is first checked for the ID value being called on. 
    - If a local copy of the data is available, an API call is not needed and the data will be pulled from the local map.
    - This will also reduce the possibility of hitting API rate limits. 
- If there is not a local copy of the data, an API call will be made to the request the data for the specific resource ID. 
    - The retrieved data will be formatted and stored in the local map file to eliminate the need for another API call the next time this value is searched on. 

The files in this directory can parse various OBO ontologies to pre-populate the resource maps to prevent a potential cold start problem on data conversions containing many previously unseen values. 

The code in this repository uses the [pronto]() library for the ontology file parsing. 