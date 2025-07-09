from settings import *
import gspread
from google.oauth2.service_account import Credentials

class ResponseHandler:
    def __init__(self):
        self.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        self.creds = Credentials.from_service_account_file(KEY_JSON, scopes=self.scopes)
        self.client = gspread.authorize(self.creds)
        self.session = requests.Session()

    def get_sheet_response(self, sheet_id):
        try:
            sheet = self.client.open_by_key(sheet_id)
            values_list = sheet.sheet1.row_values(2)
            if values_list:
                sheet.sheet1.delete_rows(2)
                return re.sub(r'\s+', ' ', values_list[1]).strip()
            return None
        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] Could not fetch sheet data") from e

    def _get_payload(self, query, prompt):
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": query},
                        {"text": prompt}
                    ]
                }
            ]
        }
        return payload

    def gemini(self, query, prompt=CONTENT_PROMPT, data_type=str, max_retries=5, delay=2):
        retries = 0
        endpoint = ENDPOINT_2
        while retries < max_retries:
            try:
                response = self.session.post(endpoint, json=self._get_payload(query, prompt))
                response.raise_for_status()
                response_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                response_text = response_text.replace("*", "")
                return data_type(response_text)
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed: {e}")
                if retries >= max_retries // 2:
                    endpoint = ENDPOINT_1
                retries += 1
                time.sleep(delay * (2 ** retries))
            except Exception as e:
                raise Exception(f"[{self.__class__.__name__}] Could not fetch response from Gemini") from e
        raise Exception("Max retries exceeded")
