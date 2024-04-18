""" Converts the CSV file of the Clinvar RS ID/Condition to Pubmed evidence into a JSON file 
for more efficient comparisons.
"""

import json
import csv

csv_file_path = (
    "../../home/data/processed_data/GlyGen/clinvar/clinvar_citations_disease.csv"
)
json_output_path = (
    "../../home/data/processed_data/GlyGen/clinvar/clinvar_citations_disease.json"
)

output_dict: dict = {}
rs_id_set: set[str] = set()
csv_file = csv.DictReader(open(csv_file_path))

for idx, row in enumerate(csv_file):
    assessed_biomarker_entity_id = row["assessed_biomarker_entity_id"]
    condition_id = row["condition_id"]
    evidence_id = row["evidence_source"].split(":")[1]
    if assessed_biomarker_entity_id not in rs_id_set:
        rs_id_set.add(assessed_biomarker_entity_id)
        output_dict[assessed_biomarker_entity_id] = {
            condition_id: [evidence_id]
        }
    else:
        if condition_id in output_dict[assessed_biomarker_entity_id]:
            if evidence_id not in output_dict[assessed_biomarker_entity_id][condition_id]:
                output_dict[assessed_biomarker_entity_id][condition_id].append(evidence_id)
        else:
            output_dict[assessed_biomarker_entity_id][condition_id] = [evidence_id]

with open(json_output_path, "w") as f:
    json.dump(output_dict, f)
