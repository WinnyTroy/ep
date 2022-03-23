from fastapi import HTTPException
from ..models import (Accounts,
                      Installations,
                      Account_Installations_Connect)
from ..database import engine
from sqlmodel import Session, select, or_

# Intialize database session per single thread
session = Session(engine)

def create_unleashed_credit_note_record():
    client_record = Installations()
    pass

def get_saved_user(client_id):
    try:
        db_accounts = session.exec(
            select(Accounts).where(
                Accounts.account_ref==client_id)).first().account_id
    except AttributeError:
        return HTTPException(
                status_code=404 ,
                detail=f"Bad Request - Client {client_id}'s "\
                "Does not have a record on the `sc_accounts` table")
    return db_accounts

def query_user_existing_installations(db_user_installations):
    # Filter out the financing_component installations
    client_installations = session.exec(select(Installations).where(
        Installations.installation_id==db_user_installations.installation_id,
        or_(Installations.item_code=="InterestPiece",
            Installations.item_code=="financing_component"))).all()
    if not client_installations:
        return HTTPException(
                status_code=404 ,
                detail=f"Bad Request - Client {db_user_installations}'s "\
                "Does not have a record on the `sc_installation_unleashed_contents` table")
    return client_installations


def query_user_installation_records(db_user_account_id):
    # Use `sc_installations` connector table
    # to fetch all installations for specific user
    user_installations = session.exec(
        select(Account_Installations_Connect).where(
            Account_Installations_Connect.account_id==db_user_account_id)).first()
    if not user_installations:
        return HTTPException(
                status_code=404 ,
                detail=f"Bad Request - Client {db_user_account_id}'s "\
                "Does not have a record on the `sc_installations` table")
    return user_installations
