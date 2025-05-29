import os
from notion_client import Client


NOTION_TOKEN = "ntn_P524559548822tGPGbj7rUlnwkUZaYYo8ZBAqqbjF7r2Od"
DATABASE_ID = "202138a96f6080a898dcec3c02a3deec"


# --- Code Starts Here ---
if NOTION_TOKEN is None:
    print("Error: NOTION_TOKEN environment variable is not set. Please set it and try again.")
    print("Example (Linux/macOS): export NOTION_TOKEN='secret_YOURNOTIONSECRET'")
    print("Example (Windows CMD): set NOTION_TOKEN=secret_YOURNOTIONSECRET")
    exit()

try:
    # Initialize the Notion client
    notion = Client(auth=NOTION_TOKEN)

    print(f"Attempting to read database with ID: {DATABASE_ID}")

    # Query the database
    # Here, we only fetch a few results. You can add filters or sorts for more specific queries.
    response = notion.databases.query(
        database_id=DATABASE_ID,
        # You can add query conditions, e.g.:
        # filter={
        #     "property": "Status", # Assuming you have a property named "Status"
        #     "select": {
        #         "equals": "Published"
        #     }
        # },
        page_size=5 # Fetch only the first 5 items as an example
    )

    # Check if any results were found
    if not response["results"]:
        print("No items found in the database.")
    else:
        print("Successfully retrieved database items:")
        for page in response["results"]:
            page_id = page["id"]
            # Get the page title (usually the first "title" type property in the database)
            title_property = None
            for prop_name, prop_data in page["properties"].items():
                if prop_data["type"] == "title" and prop_data["title"]:
                    # Title content is a list; iterate to get its plain text
                    title_parts = [text_obj["plain_text"] for text_obj in prop_data["title"]]
                    title_property = "".join(title_parts)
                    break # Stop after finding the title property

            if title_property:
                print(f"- Page ID: {page_id}, Title: {title_property}")
            else:
                print(f"- Page ID: {page_id}, (No title or incorrect title property type)")

except Exception as e:
    print(f"An error occurred while reading the Notion database: {e}")
    print("Please check:")
    print("1. If your NOTION_TOKEN is correct and has access permissions.")
    print("2. If your DATABASE_ID is correct.")
    print("3. If your Integration has been added to the database's share settings in Notion.")