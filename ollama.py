import requests
import json
import threading

# OLLAMA_HOST = "127.0.0.1:11434"
OLLAMA_HOST = "ollama.doleckijakub.pl"

class Ollama:
    def __init__(self, model):
        self.host = f"http://{OLLAMA_HOST}"
        self.model = model
        self._response = None
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()
        if self._response is not None:
            self._response.close()

    def generate(self, prompt: str):
        # print(self, "generate() called with prompt length", len(prompt))

        self._stop_event.clear()

        url = f"{self.host}/api/generate"
        json_data = {"model": self.model, "prompt": prompt}
        try:
            response = requests.post(url, json=json_data, stream=True)
            response.raise_for_status()
            self._response = response
        except Exception as e:
            raise Exception(f"[Ollama] request failed: {e}")

        line_buffer = ""
        for chunk in response.iter_lines():
            if self._stop_event.is_set():
                break
            if not chunk:
                continue
            try:
                chunk_data = json.loads(chunk.decode("utf-8"))
            except Exception as e:
                raise Exception(f"[Ollama] failed to parse chunk: {e}")
            text = chunk_data.get("response", "")
            line_buffer += text
            while "\n" in line_buffer:
                line, line_buffer = line_buffer.split("\n", 1)
                line = line.strip()
                if line:
                    yield line

        if not self._stop_event.is_set() and line_buffer.strip():
            yield line_buffer.strip()

def simple_ollama_query(model: str, prompt: str):
    return "".join(Ollama(model).generate(prompt))