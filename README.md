# Biomarker-Database-Curation
This project focuses on making a biomarker database from different, relevant resources. So far we have extracted biomarkers from 4 different resources: OpenTargets, ClinVar, GWAS Catalog, MarkerDB. We also added previously curated data from OncoMX The information and data extracted from the resources was done based on an agreed upon defintion of biomarkers and what tge core elements need were for a biomarker.

<img width="604" alt="image" src="https://user-images.githubusercontent.com/116293652/226414788-89e71a90-de6d-47d0-b3a7-f3baa4e667e7.png">

The elements highlighted in green are data types that would need to be extracted from the resources in order for a basic biomarker definition to be formed (assessed_biomarker_entity, condition_name, biomarker_status, evidence_source/type). Other data types, such as loinc_code, specimen_type, and best_biomarker_type, were not deemed as core elements but still provide contect to the defintion of a particular biomarker (clinical lab measurements, where to measure the biomarker from, and what type of biomarker it is). These data types were mapped to the biomarker from outside resources such as LOINC and Uberon Ontology.

There is also a notes section present in this databse and that includes extra/miscellaneous deatils of the biomarker. This can include the exact mutation/amino acid change/expression data, Uniprot identifier, panel information, and the genome build. This data could be mapped from an outside resource or could be extracted directly from the reource the biomarker is being extracted from.

Based on the resource that was being studied there can be some variation in how the data was extracted, manipulted, and harmonized to fit the structre of the above figure. This repository will provide examples of this alonsgide the table generated and other resources needed to gain information/data for the biomarker.
