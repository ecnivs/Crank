from settings import *
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, ResumableUploadError

class YoutubeHandler:
    def __init__(self, token_file):
        self.secrets_file = SECRETS_JSON
        self.token_file = f"json/{token_file}.json"
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.credentials = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        try:
            self._try_authenticate()
        except RefreshError as e:
            logging.error(f"[{self.__class__.__name__}] Refresh failed. Deleting token and retrying.")
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
            self.credentials = None
            try:
                self._try_authenticate()
            except Exception as retry_error:
                raise RuntimeError(f"[{self.__class__.__name__}] Retry after token deletion failed.") from retry_error
        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] Authentication Failed.") from e

    def _try_authenticate(self):
        if os.path.exists(self.token_file) and not self.credentials:
            self.credentials = Credentials.from_authorized_user_file(self.token_file, self.scopes)

        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.secrets_file, self.scopes)
                self.credentials = flow.run_local_server(port=0, open_browser=True)

            with open(self.token_file, 'w') as token:
                token.write(self.credentials.to_json())

        self.service = build('youtube', 'v3', credentials=self.credentials)

    def upload(self, channel_name, video_path, title, description, tags: list, categoryId, preset):
        try:
            body = {
                'snippet': {
                    'title': str(title),
                    'description': str(description),
                    'tags': tags,
                    'categoryId': str(categoryId)
                },
                'status': {
                    'privacyStatus': 'public'
                }
            }

            media = MediaFileUpload(video_path, mimetype='video/*', resumable=True)
            request = self.service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )
            response = request.execute()
            logging.info(f"✅ Uploaded to '{channel_name}' successfully. Video ID: {response['id']}")
            return response['id']
        except ResumableUploadError as e:
            preset.set_limit_time()
            logging.error(f"Failed to upload to '{channel_name}': {e}")
        except Exception as e:
            logging.error(f"Failed to upload to '{channel_name}': {e}")
