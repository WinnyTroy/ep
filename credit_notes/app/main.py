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
from credit_notes.app.settings.settings import settings
from starlette.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from .utils.credit_notes_tools import confirm_existing_user_credit

# ELK for access logging
logging.basicConfig(filename="logFile.txt",
                    filemode='a',
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s-%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

app = FastAPI(title=settings.app_name,
              version=settings.app_version,
              root_path=settings.app_root_path)

#  ******* monitoring stack **********
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
    # Unpack request data
    try:
        client_data = await request.json() or json.loads(request['body'])
        # handle aws lambda docker container requests
        # client_data = request.scope['aws.event']
    except (JSONDecodeError, KeyError):
        client_data = await request.body()

    if isinstance(client_data, bytes):
        user_data = client_data.decode("UTF-8")
        client_data = ast.literal_eval(user_data)
        print(f'Received request data >>>>>>>>>>> {user_data}')
    logging.debug(f'Request data received for current request- {client_data}')
    print(f'Received request data >>>>>>>>>>> {client_data}')

    client_id = str(client_data.get('client_id', ''))
    credit_amount = float(client_data.get('amount', ''))
    client_name = str(client_data.get('customer_name', ''))
    client_contact = int(client_data.get(
                        'Customer Phone number',
                        '0712354876'))
    # Unpack AMT comment data
    credit_reason = client_data.get('comments', '')
    if isinstance(credit_reason, dict):
        credit_reason = client_data["comments"]["payplanData"]["note"]

    # Determine action to be performed
    # Based on the amount sent in request
    if credit_amount < 0:
        performing_action = 'Credit'
    else:
        performing_action = 'Debit'

    response_object = confirm_existing_user_credit(
            client_id,
            credit_amount,
            credit_reason,
            client_name,
            client_contact,
            performing_action=performing_action,)

    if isinstance(response_object, HTTPException):
        raise response_object

    return response_object


# AWS Lambda FastApi Adapter
handler = Mangum(app=app)
