import requests, xml.etree.ElementTree as ET
from typing import Iterator, Dict

OAI = "https://gallica.bnf.fr/services/OAIRecord?ark={ark}"  # metadata by ark
SRU = "https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2&maximumRecords=50&startRecord={start}&query={query}"

def search_subject(subject_contains:list[str], date_before:str, max_items:int=100) -> Iterator[Dict]:
    start = 1
    fetched = 0
    # SRU CQL query for subject and date
    subj = " OR ".join([f'"{s}"' for s in subject_contains])
    query = f'(dc.subject any {subj}) and (dc.date < "{date_before}")'
    while fetched < max_items:
        r = requests.get(SRU.format(start=start, query=query), timeout=30)
        if r.status_code != 200:
            break
        root = ET.fromstring(r.content)
        ns = {"srw": "http://www.loc.gov/zing/srw/"}
        records = root.findall(".//srw:record", ns)
        if not records: break
        for rec in records:
            md = rec.find(".//srw:recordData", ns)
            if md is None: continue
            xml = ET.tostring(md, encoding="unicode")
            # naive ARK extraction
            if "ark:/" in xml:
                start_idx = xml.find("ark:/")
                ark = xml[start_idx: xml.find('"', start_idx)]
                yield {"ark": ark, "record_xml": xml, "source": f"https://gallica.bnf.fr/{ark}"}
                fetched += 1
                if fetched >= max_items: break
        start += 50
