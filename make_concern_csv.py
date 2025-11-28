import pandas as pd

# ▼ 기존 CSV 불러오기
df = pd.read_csv("acne_ingredients.csv", encoding="utf-8")

# ▼ Concern을 추가할 빈 칼럼
df["Concern"] = ""

# ▼ Concern 룰셋
silicone_keywords = [
    "dimethicone", "siloxane", "methicone",
    "cyclopentasiloxane", "cyclohexasiloxane",
    "amodimethicone", "trimethicone"
]

petroleum_keywords = [
    "petrolatum", "mineral oil", "paraffinum", "ceresin",
    "ozokerite", "microcrystalline wax"
]

drying_alcohol_keywords = [
    "alcohol denat", "sd alcohol", "ethanol", "isopropyl alcohol"
]

irritant_keywords = [
    "fragrance", "parfum", "essential oil",
    "menthol", "peppermint", "eucalyptus",
    "limonene", "linalool", "benzyl alcohol"
]

fungal_acne_keywords = [
    "polysorbate", "peg-", "sorbitan", "oleate",
    "isopropyl palmitate", "isopropyl myristate"
]

def detect_concern(ingredient, row):
    name = ingredient.lower()
    concerns = []

    # 1) Pore-clogging (코메도제닉 점수 기반)
    try:
        score = float(row.get("ComedogenicScore", 0))
        if score >= 3:
            concerns.append("Pore-clogging")
    except:
        pass

    # 2) Silicone
    if any(k in name for k in silicone_keywords):
        concerns.append("Silicone")

    # 3) Petroleum-based
    if any(k in name for k in petroleum_keywords):
        concerns.append("Petroleum-based")

    # 4) Drying Alcohol
    if any(name.startswith(k) or k in name for k in drying_alcohol_keywords):
        concerns.append("Drying Alcohol")

    # 5) Fungal Acne Trigger
    if any(k in name for k in fungal_acne_keywords):
        concerns.append("Fungal Acne Trigger")

    # 6) Irritant / Sensitizer
    if any(k in name for k in irritant_keywords):
        concerns.append("Irritant")

    # 7) None
    if not concerns:
        return "None"

    return ", ".join(sorted(set(concerns)))


# ▼ 모든 성분에 대해 Concern 자동 생성
new_concerns = []
for idx, row in df.iterrows():
    ingredient = row["Ingredient"]
    concern = detect_concern(ingredient, row)
    new_concerns.append(concern)

df["Concern"] = new_concerns

# ▼ 새로운 CSV로 저장
df.to_csv("acne_ingredients_with_concern.csv", index=False, encoding="utf-8")

print("완료! acne_ingredients_with_concern.csv 파일이 생성되었습니다.")
