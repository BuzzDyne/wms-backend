from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from _cred import Credentials

SQLALCHEMY_DB_URL = f'mysql+pymysql://{Credentials["user"]}:{Credentials["password"]}@{Credentials["host"]}/{Credentials["database"]}?charset=utf8mb4'

engine = create_engine(SQLALCHEMY_DB_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = automap_base()

Base.prepare(engine, reflect=True)

User_TM = Base.classes.user_tm
Role_TM = Base.classes.role_tm
Picklist_TM = Base.classes.picklist_tm
PicklistFile_TR = Base.classes.picklistfile_tr
PicklistItem_TR = Base.classes.picklistitem_tr
ProductMapping_TR = Base.classes.productmapping_tr
Stock_TM = Base.classes.stock_tm
StockType_TR = Base.classes.stocktype_tr
StockSize_TR = Base.classes.stocksize_tr
StockColor_TR = Base.classes.stockcolor_tr
MasterParameter_TM = Base.classes.master_parameter_tm
InboundSchedule_TM = Base.classes.inboundschedule_tm
Inbound_TM = Base.classes.inbound_tm
InboundItems_TR = Base.classes.inbounditems_tr


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
