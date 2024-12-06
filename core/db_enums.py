from enum import IntEnum, StrEnum


class UserTMStatus(IntEnum):
    ACTIVE = 1
    INACTIVE = 0


class RoleTMRoleId(IntEnum):
    OWNER = 1
    WAREHOUSE = 2
    ECOMMORCE = 3
    PACKER = 4


class StockTMIsActive(IntEnum):
    ACTIVE = 1
    INACTIVE = 0


class PicklistTMStatus(StrEnum):
    ON_DRAFT = "ON_DRAFT"
    CANCELLED = "CANCELLED"
    CREATED = "CREATED"
    ON_PICKING = "ON_PICKING"
    COMPLETED = "COMPLETED"


class PicklistItemTRIsExcluded(IntEnum):
    INCLUDED = 0
    EXCLUDED = 1


class AuditLog:
    class Menu(StrEnum):
        PICKLIST = "PICKLIST"

    class Action(StrEnum):
        PICKLIST_CREATION = "PICKLIST_CREATION"
        PICKLIST_UPDATE = "PICKLIST_UPDATE"

    class Entity(StrEnum):
        PICKLIST_TM = "PICKLIST_TM"
