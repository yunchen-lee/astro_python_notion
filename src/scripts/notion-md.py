import os
from notion_client import Client

# ✏️ 請確認這兩個值是你自己的 API key 與資料庫 ID
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
OUTPUT_DIR = "../content/blog"  # 請視你執行位置調整，這裡是從 scripts/ 向上跳一層到 content/blog/

def get_full_rich_text(rich_text_array):
    return "".join([rt.get("plain_text", "") for rt in rich_text_array])

# --- Main ---
notion = Client(auth=NOTION_TOKEN)
print(f"📥 正在讀取資料庫 ID: {DATABASE_ID}")
print("📂 當前工作目錄：", os.getcwd())

try:
    response = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "property": "Status",
            "select": {
                "equals": "published"
            }
        }
    )

    if not response["results"]:
        print("⚠️ 查無任何 'published' 狀態的頁面。")
    else:
        for page in response["results"]:
            page_id = page["id"]
            properties = page["properties"]

            # 擷取標題
            title = "Untitled"
            if properties.get("Name") and properties["Name"]["title"]:
                title = get_full_rich_text(properties["Name"]["title"])

            # 擷取語言（決定子資料夾）
            lang = "en"  # 預設
            if properties.get("Lang") and properties["Lang"]["select"]:
                lang = properties["Lang"]["select"]["name"].lower()

            # 擷取純段落內容（忽略 heading / list 等）
            blocks = notion.blocks.children.list(block_id=page_id)["results"]
            content_lines = []
            for block in blocks:
                if block["type"] == "paragraph" and block["paragraph"]["rich_text"]:
                    content_lines.append(get_full_rich_text(block["paragraph"]["rich_text"]))
            body = "\n\n".join(content_lines)

            # Frontmatter + Markdown 組合
            frontmatter = f"""---
title: "{title}"
lang: "{lang}"
---
"""
            markdown = frontmatter + "\n" + body

            # 儲存到對應路徑
            subdir = os.path.join(OUTPUT_DIR, lang)
            os.makedirs(subdir, exist_ok=True)
            filename = f"{title.lower().replace(' ', '-').replace('.', '')}.md"
            filepath = os.path.join(subdir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown)

            print(f"✅ 已儲存: {filepath}")

except Exception as e:
    print(f"❌ 執行時發生錯誤: {e}")
