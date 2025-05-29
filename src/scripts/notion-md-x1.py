import os
import re
from notion_client import Client
from notion_client.helpers import get_full_rich_text

# --- Configuration ---
NOTION_TOKEN = "ntn_P524559548822tGPGbj7rUlnwkUZaYYo8ZBAqqbjF7r2Od"
DATABASE_ID = "202138a96f6080a898dcec3c02a3deec"
OUTPUT_DIR = "../content/blog" # Base output directory for blog posts
# --- Helper Functions ---

def slugify(text):
    """Converts text to a URL-friendly slug."""
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)  # Remove non-word chars (except spaces and hyphens)
    text = re.sub(r'[\s_-]+', '-', text)  # Replace spaces/underscores/multiple hyphens with single hyphen
    text = text.strip('-')  # Remove leading/trailing hyphens
    return text

def get_page_content_as_plain_markdown(notion_client, page_id):
    """Fetches all blocks for a page and converts them to plain Markdown (paragraphs only)."""
    markdown_content = []
    response = notion_client.blocks.children.list(block_id=page_id)
    for block in response["results"]:
        # Only process paragraph blocks for this minimal version
        if block["type"] == "paragraph" and block["paragraph"]["rich_text"]:
            plain_text = get_full_rich_text(block["paragraph"]["rich_text"])
            markdown_content.append(f"{plain_text}\n")
        # Add other simple types if absolutely necessary (e.g., h1, h2)
        elif block["type"] == "heading_1" and block["heading_1"]["rich_text"]:
            plain_text = get_full_rich_text(block["heading_1"]["rich_text"])
            markdown_content.append(f"# {plain_text}\n")
        elif block["type"] == "heading_2" and block["heading_2"]["rich_text"]:
            plain_text = get_full_rich_text(block["heading_2"]["rich_text"])
            markdown_content.append(f"## {plain_text}\n")
        elif block["type"] == "heading_3" and block["heading_3"]["rich_text"]:
            plain_text = get_full_rich_text(block["heading_3"]["rich_text"])
            markdown_content.append(f"### {plain_text}\n")
        # For simplicity, other block types are ignored in this MVP
    return "".join(markdown_content)

# --- Main Script ---
if NOTION_TOKEN is None:
    print("錯誤：NOTION_TOKEN 環境變數未設定。請設定後再執行。")
    exit()

try:
    notion = Client(auth=NOTION_TOKEN)
    print(f"嘗試讀取資料庫 ID: {DATABASE_ID}")

    # 查詢資料庫
    response = notion.databases.query(
        database_id=DATABASE_ID,
        # 這裡不加 filter，會讀取所有項目
        page_size=100 # 預設抓取數量，可依需求調整
    )

    if not response["results"]:
        print("在資料庫中找不到任何項目。")
    else:
        print(f"成功讀取 {len(response['results'])} 個資料庫項目。")
        for page in response["results"]:
            page_id = page["id"]
            
            # --- 從 Notion 屬性中提取 Frontmatter 資訊 ---
            title = "Untitled"
            status = "unknown"
            lang = "en" # 預設語言

            for prop_name, prop_data in page["properties"].items():
                if prop_name == "Name" and prop_data["type"] == "title" and prop_data["title"]:
                    # Name 欄位對應 Notion 的 'title' 類型
                    title_parts = [text_obj["plain_text"] for text_obj in prop_data["title"]]
                    title = "".join(title_parts)
                elif prop_name == "Status" and prop_data["type"] == "select" and prop_data["select"]:
                    status = prop_data["select"]["name"]
                elif prop_name == "Lang" and prop_data["type"] == "select" and prop_data["select"]:
                    lang = prop_data["select"]["name"].lower() # 轉為小寫 'en' 或 'zh-tw'
            
            # 使用 title 產生 slug
            slug = slugify(title)
            if not slug: # 避免空標題導致空 slug
                slug = page_id[:8] # 使用頁面 ID 的一部分作為備用 slug

            # --- 生成 Frontmatter ---
            escaped_title = title.replace('"', '\\"')

            frontmatter = f"""---
            title: "{escaped_title}"
            status: "{status}"
            lang: "{lang}"
            slug: "{slug}"
            ---
            """
            
            # --- 獲取頁面內容 (純文字) ---
            page_markdown_content = get_page_content_as_plain_markdown(notion, page_id)
            full_markdown_file_content = frontmatter + page_markdown_content

            # --- 判斷輸出路徑並寫入檔案 ---
            target_lang_dir = ""
            if lang == "en":
                target_lang_dir = "en"
            elif lang == "zh-tw":
                target_lang_dir = "zh-tw"
            else:
                print(f"警告: 頁面 '{title}' (ID: {page_id}) 的 Lang 欄位值為 '{lang}'，不支援的語言。預設儲存到 'en' 資料夾。")
                target_lang_dir = "en" # 預設 fallback

            output_subdir = os.path.join(OUTPUT_DIR, target_lang_dir)
            os.makedirs(output_subdir, exist_ok=True) # 確保目標資料夾存在

            filename = f"{slug}.md"
            output_filepath = os.path.join(output_subdir, filename)

            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(full_markdown_file_content)
            
            print(f"已生成檔案: {output_filepath}")

except Exception as e:
    print(f"執行時發生錯誤: {e}")
    print("請檢查：")
    print("1. NOTION_TOKEN 是否正確設定並具有存取權限。")
    print("2. DATABASE_ID 是否正確。")
    print("3. 你的 Integration 是否已被添加到該資料庫的共享設定中。")
    print("4. Notion 資料庫欄位名稱 (Name, Status, Lang) 是否與程式碼中的一致，且類型正確。")