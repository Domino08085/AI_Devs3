import uvicorn
import os
import sys
import navigate

from fastapi import FastAPI
from pydantic import BaseModel

root_folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(root_folder, 'lib'))

app = FastAPI()


class RouteRequest(BaseModel):
    instruction: str


@app.post("/route/")
def trace_route(route_request: RouteRequest):
    answer = navigate.navigate(route_request.instruction)
    return {"description": answer}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=4040)