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
    PIC_FIN_E01 = "Picklist not found (PIC_FIN_E01)"
    PIC_FIN_E02 = "Picklist status is '{}'. Expected: '{}' (PIC_FIN_E02)"
    PIC_FIN_E03 = "Picklist doesn't have any items (PIC_FIN_E03)"
    PIC_FIN_E04 = "Picklist still has item(s) unmapped StockID (PIC_FIN_E04)"
    PIC_OPI_E01 = "Picklist not found (PIC_OPI_E01)"
    PIC_OPI_E02 = "Picklist status is '{}'. Expected: '{}' (PIC_OPI_E02)"

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
