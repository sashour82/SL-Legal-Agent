import pandas as pd
import json
import os

def convert_excel_to_json(excel_path, json_path=None, lang="ar"):
    # Arabic and English column name mappings
    columns_map = {
        "ar": {
            "law_name": "اسم المستند القانوني",
            "section": "الباب",
            "chapter": "الفصل",
            "chapter_title": "عنوان الفصل",
            "article_number": "رقم المادة",
            "article_text": "نص المادة",
            "active": "سارية",
            "notes": "ملاحظات",
        },
        "en": {
            "law_name": "law_name",
            "section": "section",
            "chapter": "chapter",
            "chapter_title": "chapter_title",
            "article_number": "article_number",
            "article_text": "article_text",
            "active": "active",
            "notes": "notes"
        }
    }

    if lang not in columns_map:
        raise ValueError("Language must be 'ar' or 'en'")

    columns = columns_map[lang]

    df = pd.read_excel(excel_path)

    # Validate required columns
    for key, col_name in columns.items():
        if col_name not in df.columns:
            raise ValueError(f"Missing required column: {col_name}")

    # Clean and filter data
    df[columns["article_text"]] = df[columns["article_text"]].astype(str)
    df = df[df[columns["article_text"]].str.strip() != ""]
    df = df[df[columns["article_number"]].notna()]

    # Build JSON
    articles = []
    for _, row in df.iterrows():
        article = {
            "law_name": row[columns["law_name"]],
            "section": row[columns["section"]],
            "chapter": row[columns["chapter"]],
            "chapter_title": row[columns["chapter_title"]],
            "article_number": int(row[columns["article_number"]]),
            "article_text": row[columns["article_text"]].strip(),
            "active": row[columns["active"]],
            "notes": "" if pd.isna(row[columns["notes"]]) else row[columns["notes"]]
        }
        articles.append(article)

    # Set default JSON output path
    if not json_path:
        json_path = os.path.splitext(excel_path)[0] + ".json"

    # Save to JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"✅ File saved: {json_path}")

# Example usage:
convert_excel_to_json("law.xlsx", "law.json", lang="ar")
