import json


pmc_biomarker_set_path = "../../home/data/raw_data/LINCS/PMC_biomarker_sets.json"
output_path = "../../home/data/processed_data/LINCS/PMC_biomarker_sets.json"

def main():

    data = json.load(open(pmc_biomarker_set_path, "r"))
    processed_data = []

    for idx, entry in enumerate(data):
        
        processed_entry = entry
        processed_entry["biomarker_id"] = str(idx + 1)

        for component in processed_entry["biomarker_component"]:
            component["assessed_entity_type"] = "gene"
            
        processed_data.append(processed_entry)

    with open(output_path, "w") as f:
        json.dump(processed_data, f, indent=4)

if __name__ == "__main__":
    main()
