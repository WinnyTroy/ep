'''
Initialization for the EP python application
'''
import ast
from http.client import HTTPException
import json
from mangum import Mangum
from fastapi import FastAPI
from fastapi import Request
from json import JSONDecodeError
from starlette.middleware.cors import CORSMiddleware
from .utils.credit_notes_tools import (create_credit_note,
                                       get_single_unleashed_customer_details)

app = FastAPI(title="EP",
              version=1,
              root_path="/dev/")

app.add_middleware(
    CORSMiddleware,
    allow_origins='*',
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["x-apigateway-header",
                   "Content-Type",
                   "X-Amz-Date",
                   "Access-Control-Allow-Origin"],
)

# Routes
@app.post("/api/create-credit", status_code=201)
async def home(request: Request):
    # Unpack JSON request data
    try:
        client_data = await request.json() or json.loads(request['body'])
    except (JSONDecodeError, KeyError):
        client_data = await request.body()

    if isinstance(client_data, bytes):
        user_data = client_data.decode("UTF-8")
        client_data = ast.literal_eval(user_data)

    client_id = client_data['client_id']
    credit_amount = client_data['amount']

    # Fetching client by client name for now
    unleashed_client = get_single_unleashed_customer_details(
                        name=client_id)

    # Get unleashed client guid
    try:
        client_code = unleashed_client["Items"][0]["Guid"]
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Client id {client_id} does not exist in Unleashed.")

    # Default the product to the fincancing component
    product_code = 'f5f20ff7-ebf8-4196-b413-650f50582f8d'

    # Default the warehouse to Wells Fargo Warehouse
    warehouse_code = 'f8027663-364d-4325-a0f9-518e095aa0da'

    response_object = create_credit_note(client_code,
                                         product_code,
                                         warehouse_code,
                                         credit_amount)

    return response_object

# AWS Lambda FastApi Adapter
handler = Mangum(app=app, spec_version=2)
