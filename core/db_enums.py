from enum import IntEnum


class UserTMStatus(IntEnum):
    ACTIVE = 1
    INACTIVE = 0


class RoleTMRoleId(IntEnum):
    OWNER = 1
    WAREHOUSE = 2
    ECOMMORCE = 3
    PACKER = 4
