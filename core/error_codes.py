from enum import Enum


class ErrCode(Enum):
    AUT_SUP_001 = "Username '{}' already exists."
    AUT_SUP_002 = "Role '{}' does not exist."
    AUT_SUP_003 = "Username must start with a letter, be at least 3 characters long, and may only contain alphanumeric characters and dots."
    AUT_SUP_004 = "Password must be at least 4 characters long."

    AUT_SIN_001 = "Username does not exist."
    AUT_SIN_002 = "Incorrect password."

    AUT_REF_001 = "Username does not exist."
    AUT_REF_002 = "User has been disabled."

    @classmethod
    def get(cls, code, *args) -> dict:
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
            "errorCode": code.name,  # Get the enum member name (e.g., 'AUT_SUP_001')
            "errorMsg": code.value.format(*args),  # Get the formatted message
        }
