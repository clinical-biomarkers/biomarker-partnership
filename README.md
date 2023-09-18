# BiomarkerKB 

The goal of this project is to develop a community-based biomarker-centric data model to harvest and organize biomarker knowledge for diverse biological data types. 

- [Intro](#intro)
    - [Background](#background)
    - [Scope and Goal of the Project](#scope-and-goal-of-the-project)
    - [Initial Biomarker Database Curation](#initial-biomarker-database-curation)
- [Biomarker Defition](#biomarker-definition)
- [Getting Started](#getting-started)
- [Repository Structure](#repository-structure)
- [References](#references)

## Intro
### Background 
The FDA-NIH Biomarker Working Group (FNBWG) BEST resource<sup>1</sup> defines a biomarker as a "characteristic that is measured as an indicator of normal biological processes, pathogenic processes, or responses to an exposure or intervention, including therapeutic interventions". Biomarkers, measured in body fluids or tissues, are useful instrements for clinical inquiry and a growing focus of research. Biomarkers comprise important tools in the transition toward Predictive, Preventive, Personalized, Participatory medicine<sup>2</sup> and serve as valuable indicators in drug development, as well as surrogate endpoints in clinical trials.

### Scope and Goal of the Project
Biomarker research has led to distributed sets of data and the overall collection of relevant biomarker data in many different resources. The goal of this project is to provide systematic harmonization and organization of biomarker data by mapping biomarker data from public sources to Common Fund data elements. Importantly, biomarker discovery <ins>is not</ins> the goal of this project. 

### Initial Biomarker Database Curation
This project focuses on creating a biomarker database from different, relevant resources. So far we have extracted biomarkers from 5 different resources: OpenTargets, ClinVar, GWAS Catalog, MarkerDB (automated curation), and OncoMX (manual curation). The information and data extracted from the resources was done based on an agreed upon defintion of biomarkers and what the core elements were for a biomarker (indicated in Figure 1).

## Biomarker Definition

![DataModel](https://user-images.githubusercontent.com/116293652/226414788-89e71a90-de6d-47d0-b3a7-f3baa4e667e7.png)  
Figure 1

The elements highlighted in green are data types that would need to be extracted from the resources in order for a basic biomarker definition to be formed (assessed_biomarker_entity, condition_name, biomarker_status, evidence_source/type). Other data types such as loinc_code, specimen_type, and best_biomarker_type were not deemed as core elements but still provide context to the defintion of a particular biomarker (clinical lab measurements, where to measure the biomarker from, and what type of biomarker it is). These data types were mapped to the biomarker from outside resources such as LOINC and Uberon Ontology.

There is also a notes section present in this databse and that includes extra/miscellaneous deatils of the biomarker. This can include the exact mutation/amino acid change/expression data, Uniprot identifier, panel information, and the genome build. This data could be mapped from an outside resource or could be extracted directly from the reource the biomarker is being extracted from.

Based on the resource that was being studied there can be some variation in how the data was extracted, manipulted, and harmonized to fit the structre of the above figure. This repository will provide examples of this alonsgide the table generated and other resources needed to gain information/data for the biomarker.

## Getting Started

### Clone the Repository

Clone this repository to your local machine:
```bash
git clone https://github.com/biomarker-ontology/BiomarkerKB.git
```

### Conda Setup 

Create a `conda` environment using the `conda_environment.yml` file and activate the environment.

```bash
conda env create -f <PATH/TO/conda_environment.yml>
conda activate biomarkerkb
```

## Repository Structure 

| Directory             | Description                                                                           |
|-----------------------|---------------------------------------------------------------------------------------|
| `mapping_data`        | Contains the supporting data that is used to map contextual data to the biomarkers.   |
| `results`             | Contains the processed and formatted output csv files.                                |
| `src`                 | Contains the initial scripts.                                                         |

## References

- **<sup>1</sup>**: FDA-NIH_Biomarker_Working_Group. in BEST (Biomarkers, EndpointS, and other Tools) Resource [https://www.ncbi.nlm.nih.gov/books/NBK326791].     (2016). 
- **<sup>2</sup>**: Hood, L., Balling, R. & Auffray, C. Revolutionizing medicine in the 21st century through systems approaches. Biotechnol J 7, 992-1001 (2012). https://doi.org:10.1002/biot.201100306 