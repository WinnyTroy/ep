'''
Initialization for the EP python application
'''
import ast
import json
import logging
import sentry_sdk
from mangum import Mangum
from fastapi import Request
from json import JSONDecodeError
from fastapi import FastAPI, HTTPException
from .database import create_db_and_tables
from credit_notes.app.settings import settings
from starlette.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from .utils.credit_notes_tools import (create_credit_note,
                                       get_single_unleashed_customer_details,
                                       fetch_client_existing_interest_invoices,
                                       aggregate_existing_credit)
from .utils.db_connections_utils import create_unleashed_credit_note_record

# ELK for access logging
logging.basicConfig(filename="logFile.txt",
                    filemode='a',
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s-%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

app = FastAPI(title=settings.app_name,
              version=settings.app_version,
              root_path=settings.app_root_path)

###### Include monitoring stack #######
# Sentry for Error Logging
if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, release=settings.app_version)
    app.add_middleware(SentryAsgiMiddleware)

# Include middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins='*',
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["x-apigateway-header",
                   "Content-Type",
                   "X-Amz-Date",
                   "Access-Control-Allow-Origin"])

# Initialize application by connecting with Database
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Include Routes
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
    logging.debug(f'Request data received for current request- {client_data}')
    print(f'Received request data >>>>>>>>>>> {client_data}')

    client_id = int(client_data.get('client_id', ''))
    credit_amount = float(client_data.get('amount', ''))

    # Unpack AMT comment data
    credit_reason = client_data.get('comments', '')
    if isinstance(credit_reason, dict):
        credit_reason = client_data["comments"]["payplanData"]["note"]

    # Capture existing interest invoices
    existing_client_interest_invoices = fetch_client_existing_interest_invoices(client_id)
    if isinstance(existing_client_interest_invoices, HTTPException):
        return existing_client_interest_invoices
    # Counter check existing client credit amount
    aggregated_credit_value = aggregate_existing_credit(
        existing_client_interest_invoices,
        credit_amount)
    if aggregated_credit_value < 0:
            return HTTPException(
                status_code=422 ,
                detail=f"Bad Request - Client {client_id}'s existing"\
                    f" credit value is {aggregated_credit_value}")

    # Fetching client by client id
    # if client_credit_value is greater than 0
    unleashed_client = get_single_unleashed_customer_details(
                        name=client_id)

    # Handle Non existent Unleashed clients
    if unleashed_client['Pagination']['NumberOfItems'] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Client id `{client_id}` does not exist in Unleashed.")
    else:
        # Get unleashed client guid
        client_code = unleashed_client["Items"][0]["Guid"]
        print(f'Client fetched from Unleashed >>>>>>>>>>> {unleashed_client}')
        logging.debug(f'Retrieved Unleashed client - {unleashed_client}')
        # apm.capture_message(f'Retrieved Unleashed client - {unleashed_client}')

    # Default the product to the fincancing component
    product_code = 'f5f20ff7-ebf8-4196-b413-650f50582f8d'

    # Default the warehouse to Wells Fargo Warehouse
    warehouse_code = 'f8027663-364d-4325-a0f9-518e095aa0da'

    # Persist Credit Note details in SUnculture Main DB
    create_unleashed_credit_note_record()

    response_object = create_credit_note(client_code, product_code,
                                         warehouse_code, credit_amount,
                                         credit_reason)

    return response_object

# AWS Lambda FastApi Adapter
handler = Mangum(app=app, spec_version=2)
