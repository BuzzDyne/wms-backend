from enum import Enum


class UserTMStatus(Enum):
    ACTIVE = 1
    INACTIVE = 0


class RoleTMRoleId(Enum):
    OWNER = 1
    WAREHOUSE = 2
    ECOMMORCE = 3
    PACKER = 4
