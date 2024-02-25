import requests
import logging
from transformers import AutoTokenizer
from config import MAX_TOKENS, GPT_URL, SYSTEM_CONTENT, HEADERS, MODEL_TRANSFORMER


logger = logging.getLogger(__name__)
logging.basicConfig(filename='gpt_errors.log', level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class GPT:
    def __init__(self):
        self.system_content = SYSTEM_CONTENT
        self.URL = GPT_URL
        self.HEADERS = HEADERS
        self.MAX_TOKENS = MAX_TOKENS
        self.assistant_content = "Ответ:"

    @staticmethod
    def count_tokens(prompt):
        tokenizer = AutoTokenizer.from_pretrained(MODEL_TRANSFORMER)
        return len(tokenizer.encode(prompt))

    def process_resp(self, response):
        if response.status_code < 200 or response.status_code >= 300:
            logger.error(f"Ошибка при отправке запроса к GPT API: {response.status_code}")
            self.clear_history()
            return False, f"Ошибка: {response.status_code}"

        try:
            full_response = response.json()
        except Exception as e:
            logger.error(f"Ошибка при получении JSON от GPT API: {e}")
            self.clear_history()
            return False, "Ошибка получения JSON"

        if "error" in full_response or 'choices' not in full_response:
            logger.error(f"Ошибка в ответе от GPT API: {full_response}")
            self.clear_history()
            return False, f"Ошибка: {full_response}"

        result = full_response['choices'][0]['message']['content']

        if result == "":
            self.clear_history()
            return True, "Конец объяснения"
        return True, self.assistant_content + result

    def make_promt(self, user_request):
        if user_request == "":
            user_request = "продолжи"
        json = {
            "messages": [
                {"role": "system", "content": self.system_content},
                {"role": "user", "content": user_request},
                {"role": "assistant", "content": self.assistant_content}
            ],
            "temperature": 1.2,
            "max_tokens": self.MAX_TOKENS,
        }
        return json

    def send_request(self, json):
        try:
            resp = requests.post(url=self.URL, headers=self.HEADERS, json=json)
            logging.debug(f"Request sent to GPT API: {self, json}")
            logging.debug(f"Response from GPT API: {resp.text}")
            return resp
        except Exception as e:
            logging.error(f"Error sending request to GPT API: {e}")
            return None

    def save_history(self, content_response):
        self.assistant_content += content_response

    def clear_history(self):
        self.assistant_content = ""
