from settings import *

class ResponseHandler:
    def __init__(self):
        self.session = requests.Session()
        self.current_endpoint = ENDPOINT_2

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

    def gemini(self, query, prompt=None, max_retries=5, base_delay=2):
        retries = 0
        prompt = prompt or CONTENT_PROMPT
        endpoint = self.current_endpoint

        while retries < max_retries:
            try:
                response = self.session.post(endpoint, json=self._get_payload(query, prompt))
                if response.status_code == 429:
                    raise requests.exceptions.HTTPError("429 Too Many Requests")

                response.raise_for_status()
                response_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                return response_text.replace("*", "")

            except requests.exceptions.HTTPError as e:
                if "429" in str(e):
                    logging.warning(f"Rate limited on {endpoint}")
                    endpoint = ENDPOINT_1 if endpoint == ENDPOINT_2 else ENDPOINT_2
                    logging.info(f"Toggling to {endpoint}")
                else:
                    logging.error(f"HTTP error: {e}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed: {e}")
            except Exception as e:
                raise Exception(f"[{self.__class__.__name__}] Could not fetch response") from e

            retries += 1
            wait = base_delay * (2 ** retries) + random.uniform(0, 1)
            logging.debug(f"Retry {retries}/{max_retries}, waiting {wait:.2f}s...")
            time.sleep(wait)

        raise Exception("Max retries exceeded")
