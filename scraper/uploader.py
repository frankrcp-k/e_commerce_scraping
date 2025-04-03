import sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

def upload_file(service, file_path, mime_type):
    file_metadata = {
        "name": file_path.split("/")[-1], 
        "parents": ["18BJmtTmwfRCiarh-IzM-5dELuE03z2Vk"]}
    media = MediaFileUpload(file_path, mimetype=mime_type)

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    print(f"File uploaded successfully")


service_account_file = "scraper/ecommerce_scraping_service_account_credentials.json"
scopes = ["https://www.googleapis.com/auth/drive.file"]

credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
service = build("drive", "v3", credentials=credentials)


file_path = sys.argv[1]
mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

upload_file(service, file_path, mime_type)