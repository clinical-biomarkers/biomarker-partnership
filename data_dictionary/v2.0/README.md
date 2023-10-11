# v2.0 Release Notes 

- The `main_x_ref` column has been renamed to `assessed_biomarker_entity_ID`.
- The `biomarker_status` column has been renamed to `biomarker`.
- The `specimen_type` column has been split into `specimen_ID` and `specimen` columns to increase parsability.
- The `condition_name` column has been split into `condition_ID` and `condition` columns to increase parsability.
- The following columns have been added[^1]:
    - `exposure_agent_ID`
    - `exposure_agent` 
- The `evidence_source` column has been split into `evidence_source`[^2] and `evidence`[^3] columns to increase parsability.


[^1]: A given record will have either condition information or expsure_agent information.  
[^2]: The evidence_source column will optimally be formatted as Resource:Identifier (e.x. PMID:12345).  
[^3]: The evidence column would be "some text sentence" and would be populated by manual curation or natural langauge processing (NLP).