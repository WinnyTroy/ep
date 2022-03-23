
import json
import datetime
from pickle import FALSE
from typing import List, Optional

from sqlalchemy.orm.relationships import foreign
from sqlalchemy.sql.expression import false
from sqlalchemy.sql.functions import user
from sqlmodel import SQLModel, Field


class Accounts(SQLModel, table=True):
   __tablename__ = 'sc_accounts'
   account_id: Optional[str] = Field(primary_key=True, nullable=False)
   account_type_id:str = Field(nullable=False)
   customer_id:str = Field(nullable=False)
   # Freshsales contains Unleashed Credit Notes Guid
   freshsales_id:str = Field(nullable=True)
   payg_contract_number:str = Field(nullable=True)
   # Client National ID number
   account_ref:str = Field(nullable=False)
   product_id:str = Field(nullable=False)
   product_units:str = Field(nullable=True)
   acreage:float = Field(nullable=True)
   payplan_id:str = Field(nullable=True)
   account_bypass:int = Field(nullable=True)
   account_notes:str = Field(nullable=True)
   created_at:datetime.datetime = Field(nullable=False)
   created_by:str = Field(nullable=False)
   updated_at:datetime.datetime= Field(nullable=True)
   updated_by:str = Field(nullable=True)


class Installations(SQLModel, table=True):
   __tablename__ = 'sc_installation_unleashed_contents'
   invoice_cn_id: Optional[int] = Field(primary_key=True, nullable=False)
   installation_id:str = Field(nullable=False)
   type:str = Field(nullable=False)
   unleashed_number:str = Field(nullable=False)
   item_code:str = Field(nullable=False)
   quantity:int = Field(nullable=False)
   item_price:float = Field(nullable=False)


class Account_Installations_Connect(SQLModel, table=True):
   __tablename__ = 'sc_installations'
   installation_id: Optional[str] = Field(primary_key=True, nullable=False)
   premise_id:str = Field(nullable=False)
   account_id:str = Field(nullable=False)
   irrigation_design_sketch:str = Field(nullable=False)
   created_by:int = Field(nullable=False)
   created_at:datetime.datetime = Field(nullable=False)
   picture_water_source:str = Field(nullable=True)
   water_source_depth_meters:int = Field(nullable=True)
   water_column_height_meters:int = Field(nullable=True)
   pump_usage:str = Field(nullable=True)
   water_requirement_lpd:int = Field(nullable=True)
   tank_height_meters:int = Field(nullable=True)
   elevation_difference_meters:int = Field(nullable=True)
   distance_to_water_source_meters:int = Field(nullable=True)
   irrigation_price:float = Field(nullable=False)
   rainmaker_price:float = Field(nullable=False)
   household_price:float = Field(nullable=True)
   total_price:float = Field(nullable=True)
   note:str = Field(nullable=True)
   system_weight_kg:float = Field(nullable=True)
   system_size_cbm:float = Field(nullable=True)
   transportation_costs:float = Field(nullable=True)
   volumetric_weight:float = Field(nullable=True)
