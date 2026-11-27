"""スクリーン情報_*.json から akinator 用の data.js を生成する。
使い方: python3 akinator/build_data.py
"""
import glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)

# 対象の8チェーン（フォルダにある他のチェーンのデータは使わない）
CHAINS = ["109シネマズ", "TOHOシネマズ", "T・ジョイ", "イオンシネマ", "コロナシネマワールド",
          "シネマサンシャイン", "ユナイテッド・シネマ", "松竹MOVIX（SMT）"]

out = []
for path in [os.path.join(SRC, f"スクリーン情報_{c}.json") for c in CHAINS]:
    d = json.load(open(path, encoding="utf-8"))
    chain = d["chain"]["name"]
    for t in d["theaters"]:
        s = t.get("summary") or {}
        scr = t.get("screens") or []
        seats = [x["seats"] for x in scr if isinstance(x.get("seats"), (int, float)) and x["seats"] > 0]
        widths = [x["size"]["width"] for x in scr if x.get("size") and x["size"].get("width")]
        out.append({
            "n": t["theaterName"],
            "c": chain,
            "p": t["prefecture"],
            "u": t["url"],
            "sc": s.get("screens") or len(scr) or None,
            "st": s.get("seats") or (sum(seats) if seats else None),
            # 車いす席が未記載のスクリーンがあると summary は 0 になるので「不明」にする
            "wc": None if any(x.get("wheelchair") is None for x in scr) else s.get("wheelchair"),
            "sp": s.get("specialScreens"),
            "f": s.get("formats") or [],
            "mx": max(seats) if seats else None,
            "mn": min(seats) if seats else None,
            "w": max(widths) if widths else None,
        })

with open(os.path.join(HERE, "data.js"), "w", encoding="utf-8") as f:
    f.write("window.THEATERS=")
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print(len(out), "theaters")
