# -*- coding: utf-8 -*-
"""
    Simple API
"""
import logging
import os
import json
from time import time

import uvicorn
import requests

from mangum import Mangum
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def send_message(version, to_phone, wa_id, user_token, template_name, params):
    url = f"https://graph.facebook.com/{version}/{to_phone}/messages"
    logger.info(version)
    logger.info(to_phone)
    logger.info(wa_id)
    ori_tpl_params = []
    for idx, item in enumerate(params):
        ori_tpl_params.append({"type": "text", "text": item})

    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "to": f"{wa_id}",
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "pt_BR"},
                "components": [{"type": "header", "parameters": ori_tpl_params}],
            },
        }
    )
    logger.info(payload)
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


app = FastAPI(title="API Model")
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def remove_file_before_leave(request: Request, call_next):
    start_time = time()
    response = await call_next(request)
    process_time = time()
    response.headers["X-Process-Time"] = str(process_time - start_time)
    return response


@app.get("/", tags=["Version 1"])
async def get_main():
    pass
    return None


@app.get("/webhook", tags=["Version 1"])
async def get_webhook(request: Request):
    try:
        raw = await request.json()
    except:
        raw = None

    try:
        params = request.query_params
    except:
        params = None

    if params and "hub.mode" in params and params["hub.mode"] == "subscribe":
        return int(params["hub.challenge"])
    return {"status": "OK", "headers": request.headers, "body": raw, "parameters": params}


@app.post("/webhook", tags=["Version 1"])
async def post_webhook(request: Request):
    try:
        raw = await request.json()
    except:
        raw = None

    logger.info(raw)

    message = "Nada..."
    if raw and "messages" in raw["entry"][0]["changes"][0]["value"]:
        message = f'Você disse: {raw["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]}'

    if raw and raw["entry"][0]["changes"][0]["field"] == "messages":
        send_message(
            os.environ["aws_version"],
            os.environ["aws_appid"],
            raw["entry"][0]["changes"][0]["value"]["metadata"]["display_phone_number"],
            os.environ["aws_token"],
            "mensagem",
            [message],
        )
        return {"status": "message sent"}
    return None


handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)
