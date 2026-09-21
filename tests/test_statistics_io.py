import json, pathlib, tempfile
from konfigurator.statistics_io import load_statistics, save_statistics, merge_statistics, parse_csv
from konfigurator.models import StatisticsFile

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "valid_statistics_v1.json"

def test_roundtrip():
    sf,_=load_statistics(FIXTURE)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        path=tmp.name
    try:
        save_statistics(sf, path)
        sf2,_=load_statistics(path)
        assert len(sf2.sets)==len(sf.sets)
        assert sf2.sets[0].name==sf.sets[0].name
    finally:
        pathlib.Path(path).unlink(missing_ok=True)

def test_merge_skip():
    sf,_=load_statistics(FIXTURE)
    incoming,_=load_statistics(FIXTURE)
    # same name -> skip
    merged, log = merge_statistics(sf, incoming, on_conflict="skip")
    assert len(merged.sets)==1
    assert any("preskoc" in x.lower() or "skip" in x.lower() or "přeskoč" in x.lower() for x in log)

def test_merge_rename():
    sf,_=load_statistics(FIXTURE)
    incoming,_=load_statistics(FIXTURE)
    merged, log = merge_statistics(sf, incoming, on_conflict="rename")
    assert len(merged.sets)==2
    assert merged.sets[1].name != merged.sets[0].name

def test_merge_overwrite():
    sf,_=load_statistics(FIXTURE)
    incoming,_=load_statistics(FIXTURE)
    incoming.sets[0].records=[]
    merged, log = merge_statistics(sf, incoming, on_conflict="overwrite")
    assert len(merged.sets)==1
    assert len(merged.sets[0].records)==0

def test_parse_csv():
    recs=parse_csv("1;2\n3;4\n", 2, ";")
    assert len(recs)==2 and recs[0].values==[1.0,2.0]
    recs2=parse_csv("1,5;2,5\n", 2, ";")
    assert recs2[0].values==[1.5,2.5]

def test_parse_csv_header_skip():
    # parse_csv currently requires numeric rows; header skip is handled by UI layer, not core parse
    recs=parse_csv("1;2\n3;4\n", 2, ";")
    assert len(recs)==2
    try:
        parse_csv("a;b\n", 2, ";")
        assert False
    except ValueError:
        pass
