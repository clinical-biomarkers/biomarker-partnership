import json 
import pronto 

doid = pronto.Ontology(handle = '../../home/owls/doid.owl')
print('=================')

doid_map = {}

for idx, term in enumerate(doid.terms()):
    if 'doid:' not in term.id.lower():
        continue
    synonyms = []
    for syn in term.synonyms:
        if syn.scope == 'EXACT':
            synonyms.append(syn.description)
    doid_map[term.id.replace('DOID:', '')] = {
        'recommended_name': term.name,
        'description': term.definition,
        'synonyms': synonyms if synonyms else []
    }

with open('../../mapping_data/doid_map.json', 'w') as f:
    json.dump(doid_map, f, indent=4)
