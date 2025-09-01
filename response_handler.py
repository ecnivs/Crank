import logging

# -------------------------------
# Logging Configuration
# -------------------------------
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s - %(message)s',
                    force=True)

class ResponseHandler:
    def __init__(self, client):
        self.logger = logging.getLogger(self.__class__.__name__)
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
        self.logger.info(f"Gemini returned: {response.text}")
        return response.text
