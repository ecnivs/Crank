from settings import *

class ResponseHandler:
    def __init__(self, client):
        self.client = client
        self.models = {
            "2.5": "gemini-2.5-flash",
            "2.0": "gemini-2.0-flash",
            "1.5": "gemini-1.5-flash",
        }

    def gemini(self, query, model):
        current_model = self.models.get(str(model))
        response = self.client.models.generate_content(
            model = current_model,
            contents = query
        )
        logging.info(f"[{self.__class__.__name__}] Gemini returned: {response.text}")
        return response.text
