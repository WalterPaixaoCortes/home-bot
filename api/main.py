# -*- coding: utf-8 -*-
"""
    Simple API
"""
import base64
import json
from time import time
from mangum import Mangum

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware


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


handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)
