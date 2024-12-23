from enum import Enum


class ErrCode(Enum):
    AUT_SUP_E01 = "Username '{}' already exists (AUT_SUP_E01)"
    AUT_SUP_E02 = "Role '{}' does not exist (AUT_SUP_E02)"
    AUT_SUP_E03 = "Username must start with a letter, be at least 3 characters long, and may only contain alphanumeric characters and dots (AUT_SUP_E03)"
    AUT_SUP_E04 = "Password must be at least 4 characters long (AUT_SUP_E04)"
    AUT_SIN_E01 = "Username does not exist (AUT_SIN_E01)"
    AUT_SIN_E02 = "Incorrect password (AUT_SIN_E02)"
    AUT_REF_E01 = "Username does not exist (AUT_REF_E01)"
    AUT_REF_E02 = "User has been disabled (AUT_REF_E02)"

    PIC_NEW_E01 = "A draft picklist already exists (PIC_NEW_E01)"
    PIC_UPL_E01 = "Invalid e-commerce code: {}. Supported codes are {} (PIC_UPL_E01)"
    PIC_UPL_E02 = "Invalid header for '{}' in file for '{}'. Expected: '{}' at index {}, Got: '{}' (PIC_UPL_E02)"
    PIC_CCL_E01 = "Picklist not found (PIC_CCL_E01)"
    PIC_CCL_E02 = "Picklist status is '{}'. Expected: '{}' (PIC_CCL_E02)"
    PIC_REM_E01 = "Picklist not found (PIC_REM_E01)"
    PIC_REM_E02 = "Given PicklistItem (ID:{}) belongs to Picklist (ID:{}). Expected Picklist (ID:{}) (PIC_REM_E02)"
    PIC_FIN_E01 = "Picklist not found (PIC_FIN_E01)"
    PIC_FIN_E02 = "Picklist status is '{}'. Expected: '{}' (PIC_FIN_E02)"
    PIC_FIN_E03 = "Picklist doesn't have any items (PIC_FIN_E03)"
    PIC_FIN_E04 = "Picklist still has item(s) unmapped StockID (PIC_FIN_E04)"
    PIC_OPI_E01 = "Picklist not found (PIC_OPI_E01)"
    PIC_OPI_E02 = "Picklist status is '{}'. Expected: '{}' (PIC_OPI_E02)"
    PIC_SEM_E01 = "PicklistItem not found (PIC_SEM_E01)"
    PIC_SEM_E02 = "Given size/type/color doesnt exists (PIC_SEM_E02)"
    PIC_DFI_E01 = "Picklist not found (PIC_DFI_E01)"
    PIC_DFI_E02 = "Picklist file not found (PIC_DFI_E02)"
    PIC_DFI_E03 = "Picklist File doesn't belong to given picklist id (PIC_DFI_E03)"
    PIC_DFI_E04 = "No File found for given ecom code and picklist id (PIC_DFI_E04)"

    PIC_DIT_E01 = "Picklist not found (PIC_DIT_E01)"
    PIC_DIT_E02 = "Picklist item not found (PIC_DIT_E02)"
    PIC_DIT_E03 = "Picklist Item doesn't belong to given picklist id (PIC_DIT_E03)"

    STO_NSZ_E01 = "Invalid size name format (STO_NSZ_E01)"
    STO_NSZ_E02 = "Size '{}' already exists (STO_NSZ_E02)"
    STO_NTY_E01 = "Invalid type name format (STO_NTY_E01)"
    STO_NTY_E02 = "Type '{}' already exists (STO_NTY_E02)"
    STO_NCO_E01 = "Invalid color format (STO_NCO_E01)"
    STO_NCO_E02 = "Color '{}' already exists (STO_NCO_E02)"

    @classmethod
    def format_error(cls, code, *args) -> dict:
        """
        Fetches the error message by code and formats it if needed.

        Args:
            code (Enum): The error code to fetch.
            *args: Arguments to format the error message.

        Returns:
            dict: A dictionary containing the error code and formatted message.

        Raises:
            ValueError: If the error code does not exist in the class.
        """
        # Ensure the code is a member of the Enum
        if not isinstance(code, cls):
            raise ValueError(f"Invalid error code: {code}")

        return {
            "errorCode": code.name,
            "errorMsg": code.value.format(*args),
        }
