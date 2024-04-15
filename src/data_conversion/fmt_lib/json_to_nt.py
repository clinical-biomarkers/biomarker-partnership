""" Handles the conversion from the JSON data model format to the N-Triples (nt) format.
"""

from fmt_lib import misc_functions as misc_fns
from typing import Union

# triple category keys
SUBJECT_OBJECTS = "subject_objects"
PREDICATES = "predicates"

# replace value
REPLACE_VALUE = "{replace}"


def json_to_nt(
    source_filepath: str, target_filepath: str, triples_map: dict, namespace_map
) -> None:
    """Converts the JSON data model format to the N-Triples (nt) format.

    Parameters
    ----------
    source_filepath : str
        The path to the source JSON file to convert.
    target_filepath : str
        The path to the target nt file to generate.
    triples_map : dict
        The triples map to use for the conversion.
    namespace_map : dict
        The namespace map to use for the conversion.
    """

    # get the JSON source data
    json_data = misc_fns.load_json(source_filepath)

    final_triples = []

    # iterate through top level entries
    for idx, entry in enumerate(json_data):

        entry_triples = []
        biomarker_subject_uri = create_biomarker_subect_uri(
            entry["biomarker_id"], triples_map[SUBJECT_OBJECTS]["biomarker_id"]
        )

        # iterate through biomarker component entries
        for biomarker_component in entry["biomarker_component"]:

            ### handle change in entity triple
            biomarker = biomarker_component["biomarker"]
            assessed_biomarker_entity_id = biomarker_component[
                "assessed_biomarker_entity_id"
            ]
            assessed_entity_type = biomarker_component["assessed_entity_type"].strip().lower()
            change_triple = build_biomarker_change_triple(
                biomarker_subject_uri,
                biomarker,
                assessed_biomarker_entity_id,
                assessed_entity_type,
                triples_map,
                namespace_map,
            )
            if change_triple is not None:
                entry_triples.append(change_triple)

            ### handle specimen triple
            specimens = biomarker_component.get("specimen", [])
            specimen_triples = build_specimen_triples(
                biomarker_subject_uri, specimens, triples_map, namespace_map
            )
            if specimen_triples is not None:
                entry_triples.extend(specimen_triples)

        ### handle best biomarker role triple
        roles = entry["best_biomarker_role"]
        role_triples = build_biomarker_role_triples(
            biomarker_subject_uri, roles, triples_map
        )
        if role_triples:
            entry_triples.extend(role_triples)

        ### handle the condition triple
        if entry.get("condition", None):
            condition = entry["condition"]["id"]
            condition_triple = build_condition_triple(
                biomarker_subject_uri, condition, roles, triples_map, namespace_map
            )
            if condition_triple:
                entry_triples.extend(condition_triple)

        # add the entry triples to the final triples
        final_triples.extend(entry_triples)

    # write the final triples to the target nt file
    triples = "\n".join(final_triples)
    with open(target_filepath, "w") as f:
        f.write(triples)


def build_condition_triple(
    biomarker_subject_uri: str,
    condition: str,
    roles: list,
    triples_map: dict,
    namespace_map: dict,
) -> list:
    """Builds the condition triple.

    Parameters
    ----------
    biomarker_subject_uri : str
        The biomarker subject URI.
    condition : str
        The condition name space and ID.
    roles : list
        The best_biomarker roles list.
    triples_map : dict
        The triples map to use for the conversion.
    namespace_map : dict
        The namespace map to use for the conversion.

    Returns
    -------
    list
        The condition triples.
    """
    condition_triples = []
    condition_name_space = condition.split(":")[0].lower()
    if condition_name_space in namespace_map:
        if namespace_map[condition_name_space] == "disease ontology":
            doid_id = condition.split(":")[1]
            condition_object_uri = triples_map[SUBJECT_OBJECTS]["doid"].replace(
                REPLACE_VALUE, doid_id
            )
            for role_entry in roles:
                role = role_entry["role"].lower()
                condition_predicate_map = triples_map[PREDICATES][
                    "condition_role_indicator"
                ]
                if role == "diagnostic":
                    predicate_uri = condition_predicate_map["diagnostic"]
                elif role == "risk":
                    predicate_uri = condition_predicate_map["risk"]
                elif role == "monitoring":
                    predicate_uri = condition_predicate_map["monitoring"]
                elif role == "prognostic":
                    predicate_uri = condition_predicate_map["prognostic"]
                else:
                    continue
                condition_triples.append(
                    f"{biomarker_subject_uri} {predicate_uri} {condition_object_uri} ."
                )
    else:
        misc_fns.log_once(
            f"build_condition_triple: No namespace URI map found for condition name space: '{condition_name_space}'",
            "info",
        )

    return condition_triples


def build_specimen_triples(
    biomarker_subject_uri: str, specimens: list, triples_map: dict, namespace_map: dict
) -> list:
    """Builds the specimen triples.

    Parameters
    ----------
    biomarker_subject_uri : str
        The biomarker subject URI.
    specimens : list
        The specimens list.
    triples_map : dict
        The triples map to use for the conversion.
    namespace_map : dict
        The namespace map to use for the conversion.

    Returns
    -------
    list
        The specimen triples.
    """
    specimen_triples = []
    specimen_predicate_uri = triples_map[PREDICATES]["specimen_sampled_from"]

    for specimen in specimens:
        if specimen.get("name_space", "") != "":
            if specimen["name_space"].lower() in namespace_map:
                if namespace_map[specimen["name_space"].lower()] == "uberon":
                    specimen_id = specimen.get("id", None)
                    if specimen_id:
                        uberon_sample_uri = triples_map[SUBJECT_OBJECTS][
                            "uberon"
                        ].replace(REPLACE_VALUE, specimen_id.split(":")[1])
                        specimen_triples.append(
                            f"{biomarker_subject_uri} {specimen_predicate_uri} {uberon_sample_uri} ."
                        )
            else:
                misc_fns.log_once(
                    f"build_specimen_triples: No namespace URI found for specimen: '{specimen}'",
                    "info",
                )

    return specimen_triples


def build_biomarker_role_triples(
    biomarker_subject_uri: str, roles: dict, triples_map: dict
) -> list:
    """Builds the best biomarker role triples.

    Parameters
    ----------
    biomarker_subject_uri : str
        The biomarker subject URI.
    roles : dict
        The roles dictionary.
    triples_map : dict
        The triples map to use for the conversion.

    Returns
    -------
    list
        The best biomarker role triples.
    """
    role_triples = []
    role_predicate_uri = triples_map[PREDICATES]["best_biomarker_role"]
    role_object_map = triples_map[SUBJECT_OBJECTS]["best_biomarker_role"]
    for role_dict in roles:
        role = role_dict["role"]
        if role.lower() == "risk":
            role_object_uri = role_object_map["risk"]
        elif role.lower() == "diagnostic":
            role_object_uri = role_object_map["diagnostic"]
        elif role.lower() == "prognostic":
            role_object_uri = role_object_map["prognostic"]
        elif role.lower() == "monitoring":
            role_object_uri = role_object_map["monitoring"]
        elif role.lower() == "predictive":
            role_object_uri = role_object_map["predictive"]
        elif role.lower() == "response":
            role_object_uri = role_object_map["response"]
        elif role.lower() == "safety":
            role_object_uri = role_object_map["safety"]
        else:
            misc_fns.log_once(
                f"build_biomarker_role_triples: No role URI found for role: '{role}'",
                "info",
            )
            continue
        role_triples.append(
            f"{biomarker_subject_uri} {role_predicate_uri} {role_object_uri} ."
        )

    return role_triples


def build_biomarker_change_triple(
    biomarker_subject_uri: str,
    biomarker_change: str,
    assessed_biomarker_entity_id: str,
    assessed_entity_type: str,
    triples_map: dict,
    namespace_map: dict,
) -> Union[str, None]:
    """Builds the biomarker change triple.

    Parameters
    ----------
    biomarker_subject_uri : str
        The biomarker subject URI.
    biomarker_change : str
        The biomarker change.
    assessed_biomarker_entity_id : str
        The assessed biomarker entity ID.
    assessed_entity_type : str
        The assessed entity type.
    triples_map : dict
        The triples map to use for the conversion.
    namespace_map : dict
        The namespace map to use for the conversion.

    Returns
    -------
    str
        The biomarker change triple.
    """
    # get predicate URI
    change_key = "biomarker_change"
    if "increase" in biomarker_change.lower():
        predicate_uri = triples_map[PREDICATES][change_key]["increase"]
    elif "decrease" in biomarker_change.lower():
        predicate_uri = triples_map[PREDICATES][change_key]["decrease"]
    elif "absence" in biomarker_change.lower():
        predicate_uri = triples_map[PREDICATES][change_key]["absence"]
    elif "presence" in biomarker_change.lower():
        predicate_uri = triples_map[PREDICATES][change_key]["presence"]
    else:
        misc_fns.log_once(
            f"build_biomarker_change_triple: No change predicate found for biomarker change: '{biomarker_change}'",
            "info",
        )
        return None

    # get object URI
    entity_namespace = assessed_biomarker_entity_id.split(":")[0].lower()
    if entity_namespace in namespace_map:
        entity_id = assessed_biomarker_entity_id.split(":")[1].strip().upper()
        namespace_value = namespace_map[entity_namespace]
        if namespace_value == "uniprot":
            object_uri = triples_map[SUBJECT_OBJECTS]["uniprot"].replace(
                REPLACE_VALUE, entity_id
            )
        elif namespace_value == "cell ontology":
            object_uri = triples_map[SUBJECT_OBJECTS]["cell_ontology"].replace(
                REPLACE_VALUE, entity_id
            )
        elif namespace_value == "protein ontology":
            object_uri = triples_map[SUBJECT_OBJECTS]["protein_ontology"].replace(
                REPLACE_VALUE, entity_id
            )
        elif namespace_value == "chebi":
            object_uri = triples_map[SUBJECT_OBJECTS]["chebi"].replace(
                REPLACE_VALUE, entity_id
            )
        elif namespace_value == "ncit":
            object_uri = triples_map[SUBJECT_OBJECTS]["ncit"].replace(
                REPLACE_VALUE, entity_id
            )
        elif namespace_value == "ncbi":
            if assessed_entity_type == "gene":
                object_uri = triples_map[SUBJECT_OBJECTS]["ncbi"]["gene"].replace(
                    REPLACE_VALUE, entity_id
                )
            elif assessed_entity_type == "chemical element":
                object_uri = triples_map[SUBJECT_OBJECTS]["ncbi"]["compound"].replace(
                    REPLACE_VALUE, entity_id
                )
            else:
                misc_fns.log_once(
                    f"build_biomarker_change_triple: No object URI found for 'ncbi' entity type: '{assessed_entity_type}'",
                    "info",
                )
                return None
        else:
            misc_fns.log_once(
                f"build_biomarker_change_triple: No namespace object URI mapping found for entity namespace: '{entity_namespace}'",
                "info",
            )
            return None
    else:
        misc_fns.log_once(
            f"build_biomarker_change_triple: No namespace object URI mapping found for entity namespace: '{entity_namespace}'",
            "info",
        )
        return None

    return f"{biomarker_subject_uri} {predicate_uri} {object_uri} ."


def create_biomarker_subect_uri(biomarker_id: str, base_url: str) -> str:
    """Creates the URI for the biomarker subject.

    Parameters
    ----------
    biomarker_id : str
        The biomarker ID.
    base_url : str
        The base URL to use for the URI.

    Returns
    -------
    str
        The biomarker subject URI.
    """
    return base_url.replace(REPLACE_VALUE, biomarker_id)
