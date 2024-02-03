import json 
import pronto 

cell_ontology = pronto.Ontology(handle = '../../home/owls/cl.owl')
print('=================')

cell_ontology_map = {}

for idx, term in enumerate(cell_ontology.terms()):
    if 'cl:' not in term.id.lower(): continue 
    synonyms = []
    for syn in term.synonyms:
        synonyms.append(syn.description)
    cell_ontology_map[term.id.replace(':', '_')] = {
        'recommended_name': term.name,
        'synonyms': synonyms if synonyms else []
    }

with open('../../mapping_data/co_map.json', 'w') as f:
    json.dump(cell_ontology_map, f, indent=4)  