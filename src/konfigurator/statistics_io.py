"""IO pro statistics file — atomicky zapis, nacitani, merge."""
from __future__ import annotations

import csv
import json
import os
import pathlib
import tempfile
from typing import Optional

from .models import StatisticsFile, StatisticsFolder, StatisticsRecord, StatisticsSet, normalize_name, generate_stats_id
from .statistics_validator import validate_statistics, ValidationResult

def load_raw(path) -> dict:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Root musí být objekt.")
    return data

def load_statistics(path) -> tuple[StatisticsFile, ValidationResult]:
    raw = load_raw(path)
    vr = validate_statistics(raw)
    if not vr.ok:
        raise ValueError(f"Validace selhala: {[e.message for e in vr.errors]}")
    sf = StatisticsFile.from_dict(raw)
    return sf, vr

def save_statistics(sf: StatisticsFile, path) -> None:
    raw = sf.to_dict(include_metadata=True)
    vr = validate_statistics(raw)
    if not vr.ok:
        raise ValueError(f"Nevalidní: {[e.message for e in vr.errors]}")
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".tmp_stats_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, p)
    finally:
        try:
            if os.path.exists(tmp): os.remove(tmp)
        except Exception: pass

def merge_statistics(existing: StatisticsFile, incoming: StatisticsFile, on_conflict: str = "skip") -> tuple[StatisticsFile, list[str]]:
    """
    Merge incoming do existing. on_conflict: skip|rename|overwrite
    Vraci (merged, log)
    - folders: merge by id, pokud incoming folder id kolize ale jina name → rename incoming folder id (generate new)
    - sets: pokud normalize_name kolize → dle on_conflict
    """
    log=[]
    # folders: build id remap
    existing_folder_ids = {f.id for f in existing.folders}
    id_remap = {}
    for f in incoming.folders:
        if f.id in existing_folder_ids:
            # check if same normalized name? If same id but different content, treat as separate: rename incoming
            existing_f = next((x for x in existing.folders if x.id==f.id), None)
            if existing_f and normalize_name(existing_f.name) != normalize_name(f.name):
                new_id = generate_stats_id()
                id_remap[f.id]=new_id
                f.id=new_id
                log.append(f"Slozka '{f.name}' id kolize → nove id {new_id}")
            else:
                log.append(f"Složka '{f.name}' již existuje — přeskočena")
                continue
        existing.folders.append(f)
        existing_folder_ids.add(f.id)
    # sets
    existing_norm = {normalize_name(s.name): s for s in existing.sets}
    existing_ids = {s.id for s in existing.sets}
    for s in incoming.sets:
        # remap folderId if needed
        if s.folderId and s.folderId in id_remap:
            s.folderId=id_remap[s.folderId]
        norm = normalize_name(s.name)
        if norm in existing_norm:
            if on_conflict=="skip":
                log.append(f"Sada '{s.name}' duplicitní — přeskočena")
                continue
            elif on_conflict=="rename":
                base=s.name; i=1
                while normalize_name(base) in existing_norm:
                    base=f"{s.name} ({i})"; i+=1
                s.name=base
                # ensure id unique
                if s.id in existing_ids:
                    s.id=generate_stats_id()
                existing.sets.append(s); existing_norm[normalize_name(s.name)]=s; existing_ids.add(s.id)
                log.append(f"Sada '{s.name}' přejmenována na '{base}'")
            elif on_conflict=="overwrite":
                target = existing_norm[norm]
                # replace in place
                idx = existing.sets.index(target)
                if s.id in existing_ids and s.id != target.id:
                    s.id=generate_stats_id()
                existing.sets[idx]=s
                existing_norm[norm]=s
                log.append(f"Sada '{s.name}' přepsána")
        else:
            if s.id in existing_ids:
                s.id=generate_stats_id()
            existing.sets.append(s); existing_norm[norm]=s; existing_ids.add(s.id)
            log.append(f"Sada '{s.name}' přidána")
    # currentIndex clamp
    if existing.sets:
        existing.currentIndex = max(0, min(existing.currentIndex, len(existing.sets)-1))
    else:
        existing.currentIndex=0
    return existing, log

def parse_csv(path_or_text: str, field_count: int, delimiter: str=";") -> list[StatisticsRecord]:
    """Parse CSV text or file path to records. Decimal ',' allowed."""
    # if path exists, read file else treat as text
    p = pathlib.Path(path_or_text)
    if p.exists() and p.is_file():
        text = p.read_text(encoding="utf-8")
    else:
        text = path_or_text
    records=[]
    reader = csv.reader(text.splitlines(), delimiter=delimiter)
    for row in reader:
        if not row or all(not c.strip() for c in row):
            continue
        # skip header if first row contains non-numeric? heuristic: if any cell not parseable as number, skip if we already have fieldNames?
        vals=[]
        for cell in row[:field_count]:
            c = cell.strip().replace(",", ".")
            if c=="": c="0"
            try:
                vals.append(float(c))
            except ValueError:
                raise ValueError(f"Neplatné číslo '{cell}' v řádku {reader.line_num}")
        # if row longer than field_count, error?
        if len(row) != field_count:
            # allow missing -> pad? but we require exact
            if len(row) < field_count:
                raise ValueError(f"Řádek {reader.line_num}: očekáváno {field_count} hodnot, nalezeno {len(row)}")
        records.append(StatisticsRecord(values=vals))
    return records
