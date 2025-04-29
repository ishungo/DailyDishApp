from typing import List, Union, Generator, Iterator
from schemas import OpenAIChatMessage
from pydantic import BaseModel
import os
import requests

from pathlib import Path
import sys
DAILY_DISH_APP_DIR = Path("/home/ubuntu/app/DailyDishApp/src")
sys.path.append(str(DAILY_DISH_APP_DIR))
from SuggestDishAgent import process_request
from traceback import print_exc

class Pipeline:
    class Valves(BaseModel):
        OPENAI_API_KEY: str = ""

    def __init__(self):
        # Optionally, you can set the id and name of the pipeline.
        # Best practice is to not specify the id so that it can be automatically inferred from the filename, so that users can install multiple versions of the same pipeline.
        # The identifier must be unique across all pipelines.
        # The identifier must be an alphanumeric string that can include underscores or hyphens. It cannot contain spaces, special characters, slashes, or backslashes.
        # self.id = "openai_pipeline"
        self.name = "DailyDishApp:レシピ提案"
        self.valves = self.Valves(
            **{
                "OPENAI_API_KEY": os.getenv(
                    "OPENAI_API_KEY", "your-openai-api-key-here"
                )
            }
        )

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        # This is where you can add your custom pipelines like RAG.
        print(f"pipe:{__name__}")

        # print(messages)
        print(user_message)

        OPENAI_API_KEY = self.valves.OPENAI_API_KEY
        MODEL = "dummy"

        headers = {}
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
        headers["Content-Type"] = "application/json"

        payload = {**body, "model": MODEL}

        if "user" in payload:
            del payload["user"]
        if "chat_id" in payload:
            del payload["chat_id"]
        if "title" in payload:
            del payload["title"]

        # print(payload)

        try:
            r = process_request(messages)
            print(payload['stream'])
            if payload['stream']:
                return r
            else:
                ret = ""
                for d in r:
                    ret += d
                return ret
        except Exception as e:
            print_exc()
            return f"Error: {e}"
