""" Maps the ID assigned Clinvar data to the various PubMed papers listed as evidence sources.
"""

import json
from xml.etree.ElementTree import ParseError
import ijson  # type: ignore
import os
import sys
from pymed import PubMed  # type: ignore
from pymed.api import PubMedBookArticle  # type: ignore
from dotenv import load_dotenv
import time

citation_map_path = (
    "../../home/data/processed_data/GlyGen/clinvar/clinvar_citations_disease.json"
)
clinvar_json = "../../home/data/finalized_data/clinvar.json"
output_json = "../../home/data/finalized_data/clinvar_2.json"
pubmed_link = "https://pubmed.ncbi.nlm.nih.gov/{}"
pubmed_map_path = "../../mapping_data/pubmed_map.json"
component_tags = [
    "biomarker",
    "assessed_biomarker_entity",
    "assessed_biomarker_entity_id",
]
top_level_tags = ["condition"]

with open(citation_map_path, "r") as f:
    citation_map = json.load(f)


def main():
    chunk_size = 5_000
    buffer = []

    with open(clinvar_json, "r") as f:
        array_entries = ijson.items(f, "item")

        out_file = open(output_json, "w")
        out_file.write("[\n")
        first_record = True
        api_call_counter = 0
        for idx, item in enumerate(array_entries):
            print(f"On item: {idx}")
            assessed_biomarker_entity_id = item["biomarker_component"][0][
                "assessed_biomarker_entity_id"
            ]
            condition_id = item["condition"]["id"]
            clinvar_evidence_sources = [evidence for evidence in item["evidence_source"] if evidence["database"] == "Clinvar"]
            if in_citation_map(assessed_biomarker_entity_id, condition_id):
                for pmid in citation_map[assessed_biomarker_entity_id][condition_id]:
                    item["biomarker_component"][0]["evidence_source"].append(
                        generate_evidence_source(component_tags, pmid)
                    )
                    item["evidence_source"].append(
                        generate_evidence_source(top_level_tags, pmid)
                    )
                    citation_tuple = generate_citation_entry(
                        pmid, clinvar_evidence_sources
                    )
                    if citation_tuple is not None:
                        api_call_counter += citation_tuple[0]
                        item["citation"].append(citation_tuple[1])
                    if api_call_counter == 10:
                        print("sleeping...")
                        time.sleep(2)
                        api_call_counter = 0
            buffer.append(item)
            if len(buffer) >= chunk_size:
                if not first_record:
                    out_file.write(",\n")
                json.dump(buffer, out_file, indent=2)
                buffer = []
                first_record = False
                # TODO
                sys.exit(0)
        if buffer:
            if not first_record:
                out_file.write(",\n")
            json.dump(buffer, out_file, indent=2)
        out_file.write("\n]")

    out_file.close()


def generate_evidence_source(tags: list[str], pmid: str) -> dict:
    evidence_source = {
        "id": pmid,
        "database": "Pubmed",
        "url": pubmed_link.format(pmid),
        "evidence_list": [],
        "tags": [{"tag": tag} for tag in tags],
    }
    return evidence_source


def in_citation_map(assessed_biomarker_entity_id: str, condition_id: str) -> bool:
    return (
        assessed_biomarker_entity_id in citation_map
        and condition_id in citation_map.get(assessed_biomarker_entity_id, {})
    )


def generate_citation_entry(
    pmid: str, evidence_source: list | None = None
) -> tuple | None:

    citation_tuple = get_pubmed_data(pmid)
    if citation_tuple is None:
        return None
    api_call = citation_tuple[0]
    citation_data = citation_tuple[1]
    return_data = {
        "citation_title": citation_data["title"],
        "journal": citation_data["journal"],
        "authors": citation_data["authors"],
        "date": citation_data["publication_date"],
        "evidence_source": [],
        "reference": [{"id": pmid, "type": "Pubmed", "url": pubmed_link.format(pmid)}],
    }
    if evidence_source is not None:
        evidence_source_list = []
        for source in evidence_source:
            evidence_source_list.append(
                {
                    "id": source["id"],
                    "database": source["database"],
                    "url": source["url"],
                }
            )
        return_data["evidence_source"] = evidence_source_list

    return api_call, return_data


def get_pubmed_data(pmid: str) -> tuple | None:
    pmid = pmid.strip()
    with open(pubmed_map_path, "r") as f:
        pubmed_map = json.load(f)
    if pmid in pubmed_map:
        return 0, pubmed_map[pmid]

    load_dotenv()
    email = os.getenv("EMAIL")
    api_key = os.getenv("API_KEY")
    pubmed = PubMed(tool="CFDE Biomarker-Partnership Citation Retriever", email=email)  # type: ignore
    pubmed.parameters.update({"api_key": api_key})  # type: ignore
    query = f"PMID: {pmid}"
    articles = pubmed.query(query)
    try:
        article = next(articles)
    except StopIteration as e:
        print(f"StopIteration for PMID: {pmid}.\n{e}")
        return 1, None
    except ParseError as e:
        print(f"ParseError for PMID: {pmid}.\n{e}")
        return 1, None
    except Exception as e:
        print(f"Exception for PMID: {pmid}.\n{e}")
        return 1, None

    try:
        title = article.title
        if isinstance(article, PubMedBookArticle):
            journal = f"Book: {article.title}"
        else:
            journal = article.journal
        authors = ", ".join(
            [f"{author['lastname']} {author['initials']}" for author in article.authors]
        )
        publication_date = str(article.publication_date)
    except Exception as e:
        print(f"Exception parsing artcile for PMID: {pmid}.\n{e}")
        return 1, None

    return_data = {
        "title": title,
        "journal": journal,
        "authors": authors,
        "publication_date": publication_date,
    }
    pubmed_map[pmid] = return_data
    with open(pubmed_map_path, "w") as out:
        json.dump(pubmed_map, out, indent=4)
    return 1, return_data


if __name__ == "__main__":
    main()
