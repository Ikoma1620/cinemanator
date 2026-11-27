"""スクリーン情報_*.json と manual_theaters.json から akinator 用の data.js を生成する。
使い方: python3 akinator/build_data.py

manual_theaters.json には手入力の追加データが入っている。
  theaters : クローラーの対象外だった館（独立系・取りこぼしたチェーン館）
  fixes    : クローラーのデータの修正（館名の取り違え、抜けていたフォーマット、館の分割など）
"""
import glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
manual = json.load(open(os.path.join(HERE, "manual_theaters.json"), encoding="utf-8"))
fixes = manual["fixes"]


def entry(name, chain, pref, url, screens, formats, special=None):
    """screens: [{"seats", "wheelchair", "width", "formats"}]"""
    seats = [s["seats"] for s in screens if isinstance(s.get("seats"), (int, float)) and s["seats"] > 0]
    widths = [s["width"] for s in screens if s.get("width")]
    wcs = [s.get("wheelchair") for s in screens]
    return {
        "n": name, "c": chain, "p": pref, "u": url,
        "sc": len(screens) or None,
        "st": sum(seats) if seats else None,
        # 車いす席が未記載のスクリーンがあれば「不明」
        "wc": None if not wcs or any(w is None for w in wcs) else sum(wcs),
        "sp": special if special is not None else sum(1 for s in screens if s.get("formats")),
        "f": formats,
        "mx": max(seats) if seats else None,
        "mn": min(seats) if seats else None,
        "w": max(widths) if widths else None,
    }


def from_crawled(t, chain, name=None, scr=None):
    s = t.get("summary") or {}
    scr = scr if scr is not None else (t.get("screens") or [])
    screens = [{
        "seats": x.get("seats"),
        "wheelchair": x.get("wheelchair"),
        "width": (x.get("size") or {}).get("width"),
        "formats": x.get("formats") or [],
    } for x in scr if isinstance(x.get("seats"), (int, float)) and x["seats"] > 0]
    if scr is t.get("screens"):
        formats = list(s.get("formats") or [])
        special = s.get("specialScreens")
    else:  # 分割した館はスクリーンから集計し直す
        formats = sorted({f for x in screens for f in x["formats"]})
        special = None
    e = entry(name or t["theaterName"], chain, t["prefecture"], t["url"], screens, formats, special)
    if scr is t.get("screens") and s.get("screens"):
        e["sc"] = s["screens"]
    return e


out = []
for path in sorted(glob.glob(os.path.join(SRC, "スクリーン情報_*.json"))):
    d = json.load(open(path, encoding="utf-8"))
    chain = fixes["chainRename"].get(d["chain"]["name"], d["chain"]["name"])
    for t in d["theaters"]:
        name = fixes["rename"].get(t["url"], t["theaterName"])
        if name in fixes["split"]:
            for part in fixes["split"][name]:
                scr = [t["screens"][i] for i in part["screens"]]
                out.append(from_crawled(t, chain, part["theaterName"], scr))
            continue
        e = from_crawled(t, chain, name)
        for f in fixes["addFormats"].get(name, []):
            if f not in e["f"]:
                e["f"].append(f)
        out.append(e)

for t in manual["theaters"]:
    formats = []
    for f in [f for s in t["screens"] for f in s["formats"]] + t.get("extraFormats", []):
        if f not in formats:
            formats.append(f)
    out.append(entry(t["theaterName"], t["chain"], t["prefecture"], t["url"], t["screens"], formats))

names = [t["n"] for t in out]
dup = {n for n in names if names.count(n) > 1}
assert not dup, f"館名が重複しています: {dup}"

with open(os.path.join(HERE, "data.js"), "w", encoding="utf-8") as f:
    f.write("window.THEATERS=")
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print(len(out), "theaters")
