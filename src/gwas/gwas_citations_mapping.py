""" Grabs the GWAS PMID evidence citation details. 
"""

import json
from xml.etree.ElementTree import ParseError
import os
from pymed import PubMed  # type: ignore
from pymed.api import PubMedBookArticle  # type: ignore
from dotenv import load_dotenv
import time

gwas_json_path = "../../home/data/finalized_data/gwas/gwas.json"
gwas_json = json.load(open(gwas_json_path, "r"))

output_json = "../../home/data/finalized_data/gwas/gwas_w_citations.json"
pubmed_map_path = "../../mapping_data/pubmed_map.json"
pubmed_link = "https://pubmed.ncbi.nlm.nih.gov/{}"
pubmed_map = json.load(open(pubmed_map_path, "r"))


def main():
    api_call_counter = 0
    for idx, entry in enumerate(gwas_json):
        print(f'On item: {idx}') 
        curr_pmids = []
        curr_gwas = []
        for evidence_source in entry["evidence_source"]:
            if evidence_source["database"] == "Gwas":
                curr_gwas.append(evidence_source)
            elif evidence_source["database"] == "PubMed":
                curr_pmids.append(evidence_source["id"])
        for pmid in curr_pmids:
            citation_tuple = generate_citation_entry(pmid, curr_gwas)
            if citation_tuple is not None:
                api_call_counter += citation_tuple[0]
                entry["citation"].append(citation_tuple[1])
            if api_call_counter == 10:
                print("sleeping...")
                time.sleep(2)
                api_call_counter = 0
    with open(output_json, "w") as out_file:
        json.dump(gwas_json, out_file, indent=2)
    with open(pubmed_map_path, "w") as out_file:
        json.dump(pubmed_map, out_file, indent=4)


def generate_citation_entry(
    pmid: str, evidence_source: list | None = None
) -> tuple | None:
    citation_tuple = get_pubmed_data(pmid)
    if citation_tuple is None:
        return None
    api_call = citation_tuple[0]
    citation_data = citation_tuple[1]
    return_data = {
        "title": citation_data["title"],
        "journal": citation_data["journal"],
        "authors": citation_data["authors"],
        "date": citation_data["publication_date"],
        "evidence": [],
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
        return_data["evidence"] = evidence_source_list

    return api_call, return_data


def get_pubmed_data(pmid: str, max_retries: int = 3, retry_delay=5) -> tuple | None:

    global pubmed_map

    pmid = pmid.strip()
    if pmid in pubmed_map:
        return 0, pubmed_map[pmid]

    load_dotenv()
    email = os.getenv("EMAIL")
    api_key = os.getenv("API_KEY")
    pubmed = PubMed(tool="CFDE Biomarker-Partnership Citation Retriever", email=email)  # type: ignore

    for attempt in range(max_retries):
        try:
            pubmed.parameters.update({"api_key": api_key})  # type: ignore
            query = f"PMID: {pmid}"
            articles = pubmed.query(query)
            article = next(articles)

            title = article.title
            if isinstance(article, PubMedBookArticle):
                journal = f"Book: {article.title}"
            else:
                journal = article.journal
            authors = ", ".join(
                [
                    f"{author['lastname']} {author['initials']}"
                    for author in article.authors
                ]
            )
            publication_date = str(article.publication_date)

            return_data = {
                "title": title,
                "journal": journal,
                "authors": authors,
                "publication_date": publication_date,
            }
            pubmed_map[pmid] = return_data
            return 1, return_data

        except (StopIteration, ParseError, Exception) as e:
            print(f"Error for PMID: {pmid} on attempt {attempt + 1}.\n{e}")
            time.sleep(retry_delay)

    print(f"Failed to retrieve data after {max_retries} attempts.")
    return 1, None


if __name__ == "__main__":
    main()
