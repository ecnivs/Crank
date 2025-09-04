from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, ResumableUploadError
from pathlib import Path
import datetime
import logging

# -------------------------------
# Logging Configuration
# -------------------------------
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s - %(message)s',
                    force=True)

class Uploader:
    def __init__(self, name = "crank"):
        self.name = name.replace(" ", "").lower()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.secrets_file = Path("secrets.json")
        self.token_folder = Path("tokens")
        self.token_folder.mkdir(exist_ok = True)
        self.token_file = self.token_folder / f"{self.name}_token.json"
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.credentials = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        try:
            self._try_authenticate()
        except RefreshError:
            self.logger.error("Refresh failed. Deleting token and retrying.")
            if self.token_file.exists():
                self.token_file.unlink()
            self.credentials = None
            try:
                self._try_authenticate()
            except Exception as retry_error:
                raise RuntimeError(f"[{self.__class__.__name__}] Retry after token deletion failed.") from retry_error
        except Exception:
            raise RuntimeError(f"[{self.__class__.__name__}] Authentication Failed.")

    def _try_authenticate(self):
        if self.token_file.exists() and not self.credentials:
            self.credentials = Credentials.from_authorized_user_file(str(self.token_file), self.scopes)

        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(self.secrets_file), self.scopes)
                self.credentials = flow.run_local_server(port=0, open_browser=True)

            self.token_file.write_text(self.credentials.to_json(), encoding="utf-8")

        self.service = build('youtube', 'v3', credentials=self.credentials)

    def upload(self, video_path, title, description, tags, categoryId, delay, last_upload):
        try:
            body = {
                'snippet': {
                    'title': str(f"{title} #shorts"),
                    'description': str(description),
                    'tags': tags,
                    'categoryId': str(categoryId)
                },
                'status': {
                    'privacyStatus': 'public'
                }
            }

            scheduled_publish_time = last_upload + datetime.timedelta(hours=delay)
            now = datetime.datetime.now(datetime.UTC)

            if delay and scheduled_publish_time > now:
                body['status']['publishAt'] = scheduled_publish_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                body['status']['privacyStatus'] = 'private'
            else:
                body['status']['privacyStatus'] = 'public'
                scheduled_publish_time = now

            media = MediaFileUpload(str(video_path), mimetype='video/*', resumable=True)
            request = self.service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )
            response = request.execute()
            self.logger.info(f"Uploaded successfully. Video ID: {response['id']}")
            return scheduled_publish_time or datetime.datetime.now(datetime.UTC)
        except ResumableUploadError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to upload: {e}")
            return None
