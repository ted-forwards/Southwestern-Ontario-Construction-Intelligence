import csv, io, json, re, pathlib, urllib.request
from datetime import datetime, timezone

URL = "https://canadabuys.canada.ca/opendata/pub/openTenderNotice-ouvertAvisAppelOffres.csv"
with urllib.request.urlopen(URL, timeout=90) as response:
    raw = response.read()
reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
fields = {"title":"title-titre-eng","id":"referenceNumber-numeroReference","buyer":"contractingEntityName-nomEntitContractante-eng","region":"regionsOfDelivery-regionsLivraison-eng","closes":"tenderClosingDate-appelOffresDateCloture","url":"noticeURL-URLavis-eng"}
category = "procurementCategory-categorieApprovisionnement"
missing = set(fields.values()) | {category}
missing -= set(reader.fieldnames or [])
if missing:
    raise ValueError(f"Source schema changed: {missing}")
records = {}
total = 0
for row in reader:
    total += 1
    r = {k:(row.get(v) or "").strip() for k,v in fields.items()}
    if not re.search(r'\bOntario\b', r["region"], re.I) or not r["id"] or not r["title"]:
        continue
    r["construction"] = "CNST" in (row.get(category) or "") or bool(re.search(r'\b(construction|roofing|paving|excavation|renovation|watermain|rehabilitation|engineering|demolition|electrical|mechanical)\b',r["title"],re.I))
    records[r["id"]] = r
if not total or not records:
    raise ValueError("Empty source or Ontario result; preserving previous snapshot")
path = pathlib.Path("data/live-tenders.json")
path.parent.mkdir(exist_ok=True)
tmp = path.with_suffix(".tmp")
tmp.write_text(json.dumps({"updated":datetime.now(timezone.utc).isoformat(timespec="seconds"),"source":"CanadaBuys","records":sorted(records.values(),key=lambda r:r["closes"] or "9999")},ensure_ascii=False,indent=2),encoding="utf-8")
tmp.replace(path)
print(f"Read {total}; published {len(records)} Ontario notices")
