import json 
import pronto 

chebi = pronto.Ontology(handle = '../../home/owls/chebi.owl.gz')
print('=================')

chebi_map_1_1_4 = {}
chebi_map_1_5_9 = {}
chebi_map_2 = {}
chebi_map_3 = {}
chebi_map_4 = {}
chebi_map_5 = {}
chebi_map_6 = {}
chebi_map_7 = {}
chebi_map_8 = {}
chebi_map_9 = {}

for idx, term in enumerate(chebi.terms()):
    if 'chebi:' not in term.id.lower() or not term.id or not term.name: continue 
    synonyms = []
    for syn in term.synonyms:
        synonyms.append(syn.description)
    chebi_id = term.id.replace('CHEBI:', '')
    data = {
        'recommended_name': term.name,
        'synonyms': synonyms if synonyms else []
    }
    if chebi_id[0] == '1':
        if len(chebi_id) == 1: chebi_map_1_1_4[chebi_id] = data
        elif chebi_id[1] in {'0', '1', '2', '3', '4'}: chebi_map_1_1_4[chebi_id] = data
        else: chebi_map_1_5_9[chebi_id] = data 
    elif chebi_id[0] == '2': chebi_map_2[chebi_id] = data
    elif chebi_id[0] == '3': chebi_map_3[chebi_id] = data
    elif chebi_id[0] == '4': chebi_map_4[chebi_id] = data
    elif chebi_id[0] == '5': chebi_map_5[chebi_id] = data
    elif chebi_id[0] == '6': chebi_map_6[chebi_id] = data
    elif chebi_id[0] == '7': chebi_map_7[chebi_id] = data
    elif chebi_id[0] == '8': chebi_map_8[chebi_id] = data
    elif chebi_id[0] == '9': chebi_map_9[chebi_id] = data

root_path = '../../mapping_data/chebi_map/'
maps = {
    f'{root_path}chebi_map_1_1_4.json': chebi_map_1_1_4,
    f'{root_path}chebi_map_1_5_9.json': chebi_map_1_5_9,
    f'{root_path}chebi_map_2.json': chebi_map_2,
    f'{root_path}chebi_map_3.json': chebi_map_3,
    f'{root_path}chebi_map_4.json': chebi_map_4,
    f'{root_path}chebi_map_5.json': chebi_map_5,
    f'{root_path}chebi_map_6.json': chebi_map_6,
    f'{root_path}chebi_map_7.json': chebi_map_7,
    f'{root_path}chebi_map_8.json': chebi_map_8,
    f'{root_path}chebi_map_9.json': chebi_map_9
}
for path, map in maps.items():
    with open(path, 'w') as f:
        json.dump(map, f, indent=4)