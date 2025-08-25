from settings import *

class ResponseHandler:
    def __init__(self):
        self.session = requests.Session()

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

    def gemini(self, query, prompt=CONTENT_PROMPT, max_retries=6, delay=2):
        retries = 0
        endpoint = ENDPOINT_2
        while retries < max_retries:
            try:
                response = self.session.post(endpoint, json=self._get_payload(query, prompt))
                response.raise_for_status()
                response_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                response_text = response_text.replace("*", "")
                return response_text
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed: {e}")
                if retries >= max_retries // 2:
                    endpoint = ENDPOINT_1
                retries += 1
                time.sleep(delay * (2 ** retries))
            except Exception as e:
                raise Exception(f"[{self.__class__.__name__}] Could not fetch response from Gemini") from e
        raise Exception("Max retries exceeded")
