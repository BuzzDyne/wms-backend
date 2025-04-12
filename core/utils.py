import re
from typing import Optional, Tuple
from constant import XLS
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from core.error_codes import ErrCode as E


def validate_username(username: str) -> bool:
    """
    Validates if the username is alphanumeric (including dot), starts with a letter,
    and is at least 3 characters long.
    """
    pattern = r"^[a-zA-Z][a-zA-Z0-9.]{2,}$"
    return bool(re.match(pattern, username))


def validate_password(password: str) -> bool:
    """
    Validates if the password is at least 4 characters long.
    All characters are allowed.
    """
    pattern = r"^.{4,}$"  # At least 4 characters, any characters allowed
    return bool(re.match(pattern, password))


def validate_picklist_file(workbook, ecom_code):
    """
    Validates the structure of a picklist Excel file based on the specified e-commerce code.

    This function checks that the header row of the Excel sheet matches the expected structure
    defined in the `XLS` configuration for the given e-commerce code. It ensures that the
    required headers are present and positioned at the expected column indexes.

    Args:
        workbook (openpyxl.Workbook): The workbook object loaded from the uploaded Excel file.
        ecom_code (str): The e-commerce platform code (e.g., "TIK", "TOK", "SHO").

    Returns:
        openpyxl.worksheet.worksheet.Worksheet: The active worksheet of the workbook if validation passes.

    Raises:
        HTTPException: If the `ecom_code` is invalid or if the header row does not match
            the expected structure for the specified e-commerce code.

    Error Cases:
        - If the `ecom_code` is not in `XLS`:
            Raises:
                HTTPException: status_code=400, detail="Invalid e-commerce code: {ecom_code}.
                               Supported codes are {list(XLS.keys())}."
        - If a header is missing or incorrect:
            Raises:
                HTTPException: status_code=400, detail="Invalid header for {field_name} in file for {ecom_code}.
                               Expected: '{expected_header}' at index {expected_index},
                               Got: '{actual_header}'"
    """
    sheet = workbook.active  # Use the first sheet by default

    # Fetch the expected configuration for the given ecom_code
    if ecom_code not in XLS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=E.format_error(E.PIC_UPL_E01, ecom_code, list(XLS.keys())),
        )

    config = XLS[ecom_code]

    # Get the expected header row offset
    header_row_index = config["y_offset"]["header"] + 1

    # Read the header row from the sheet
    header_row = [
        cell
        for cell in sheet.iter_rows(
            min_row=header_row_index, max_row=header_row_index, values_only=True
        ).__next__()
    ]

    # Validate each expected field's header and index
    for field_name, field_config in config["fields"].items():
        expected_header = field_config["NAME"]
        expected_index = field_config["INDEX"]

        # Check if the header exists in the correct column
        if (
            len(header_row) <= expected_index
            or header_row[expected_index] != expected_header
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=E.format_error(
                    E.PIC_UPL_E02,
                    field_name,
                    ecom_code,
                    expected_header,
                    expected_index,
                    (
                        header_row[expected_index]
                        if expected_index < len(header_row)
                        else None
                    ),
                ),
            )
    return sheet


def extract_picklist_item(sheet, ecom_code, picklist_id):
    """
    Extracts picklist items from the given Excel sheet based on the e-commerce platform configuration.

    Args:
        sheet (openpyxl.worksheet.worksheet.Worksheet): The worksheet object to extract data from.
        ecom_code (str): The e-commerce platform code (e.g., "TIK", "TOK", "SHO", "LAZ").
        picklist_id (str): The ID of the picklist which these items belongs to.

    Returns:
        list: A list of dictionaries containing the extracted order details.
    """
    config = XLS[ecom_code]
    orders = []

    if ecom_code == "TIK":

        def create_order(row):
            quantity = int(row[config["fields"]["QUANTITY"]["INDEX"]])
            product_name = row[config["fields"]["PRODUCT"]["INDEX"]]
            product_variant = row[config["fields"]["VARIANT"]["INDEX"]]

            # Clean and check the variant
            product_variant = product_variant.strip() if product_variant else None

            base_order = {
                "ecom_code": ecom_code,
                "ecom_order_id": row[config["fields"]["ORDERID"]["INDEX"]],
                "product_name": (
                    f"{product_name} - {product_variant}"
                    if product_variant
                    else product_name
                ),
                "field1": product_name,
                "field2": product_variant,
                "field3": None,
                "field4": None,
                "field5": None,
                "picklist_id": picklist_id,
                "picklistfile_id": None,
                "stock_id": None,
            }
            # Duplicate order entries for each quantity
            return [base_order.copy() for _ in range(quantity)]

    elif ecom_code == "TOK":

        def create_order(row):
            quantity = int(row[config["fields"]["QUANTITY"]["INDEX"]])
            base_order = {
                "ecom_code": ecom_code,
                "ecom_order_id": row[config["fields"]["ORDERID"]["INDEX"]],
                "product_name": row[config["fields"]["PRODUCT"]["INDEX"]],
                "field1": row[config["fields"]["PRODUCT"]["INDEX"]],
                "field2": None,
                "field3": None,
                "field4": None,
                "field5": None,
                "picklist_id": picklist_id,
                "picklistfile_id": None,
                "stock_id": None,
            }
            # Duplicate order entries for each quantity
            return [base_order.copy() for _ in range(quantity)]

    elif ecom_code == "SHO":

        def create_order(row):
            product_info = row[config["fields"]["PRODUCT"]["INDEX"]]
            ecom_order_id = row[config["fields"]["ORDERID"]["INDEX"]]

            # Split the product_info field by delimiter to separate each product
            products = product_info.split("\n")  # Assuming newlines separate products
            orders = []

            for product in products:
                # Remove any numbering prefixes like [1], [2], etc.
                product = product.lstrip("0123456789[] ").strip()

                # Parse the individual product details
                details = {
                    part.split(":", 1)[0].strip(): part.split(":", 1)[1].strip()
                    for part in product.split(";")
                    if ":" in part
                }

                product_name = details.get("Nama Produk")
                variation = details.get("Nama Variasi")

                # Clean and check the variant
                variation = variation.strip() if variation else None

                quantity = int(
                    details.get("Jumlah", "1")
                )  # Default to 1 if not specified

                base_order = {
                    "ecom_code": ecom_code,
                    "ecom_order_id": ecom_order_id,
                    "product_name": (
                        f"{product_name} - {variation}" if variation else product_name
                    ),
                    "field1": product_name,
                    "field2": variation,
                    "field3": None,
                    "field4": None,
                    "field5": None,
                    "picklist_id": picklist_id,
                    "picklistfile_id": None,
                    "stock_id": None,
                }

                # Duplicate orders based on quantity
                orders.extend([base_order.copy() for _ in range(quantity)])

            return orders

    elif ecom_code == "LAZ":

        def create_order(row):
            product_name = row[config["fields"]["PRODUCT"]["INDEX"]]
            product_variant = row[config["fields"]["VARIANT"]["INDEX"]]

            # Clean and check the variant
            product_variant = product_variant.strip() if product_variant else None

            base_order = {
                "ecom_code": ecom_code,
                "ecom_order_id": row[config["fields"]["ORDERID"]["INDEX"]],
                "product_name": (
                    f"{product_name} - {product_variant}"
                    if product_variant
                    else product_name
                ),
                "field1": product_name,
                "field2": product_variant,
                "field3": None,
                "field4": None,
                "field5": None,
                "picklist_id": picklist_id,
                "picklistfile_id": None,
                "stock_id": None,
            }
            # Duplicate order entries for each quantity
            return [base_order]

    else:

        def create_order(row):
            return []

    # Iterate rows and create orders
    for row in sheet.iter_rows(
        min_row=1 + config["y_offset"]["data"], values_only=True
    ):
        orders.extend(create_order(row))  # Extend with multiple orders if quantity > 1

    return orders


def transform_size_names(
    size_start: str, size_end: Optional[str] = None
) -> Optional[Tuple[str, str]]:
    """Transforms and validates size names.

    Args:
        size_start (str): The starting size name.
        size_end (Optional[str]): The ending size name, if applicable.

    Returns:
        Optional[Tuple[str, str]]: A tuple containing the valid size name and value,
                                   or None if validation fails.
    """
    # Transform start name
    size_start = size_start.upper().strip()
    if not re.match(r"^[A-Z0-9 ]+$", size_start):
        return None

    size_name_start = size_start
    size_value_start = size_start.replace(" ", "_")

    # Initialize and transform size_end
    if size_end:
        size_end = size_end.upper().strip()
        if not re.match(r"^[A-Z0-9 ]+$", size_end):
            return None
        size_name_end = size_end
        size_value_end = size_end.replace(" ", "_")

    # Combine the two names if size_end is provided
    if size_end:
        valid_size_value = f"{size_value_start}_TO_{size_value_end}"
        valid_size_name = f"{size_name_start} - {size_name_end}"
    else:
        valid_size_value = size_value_start
        valid_size_name = size_name_start

    return valid_size_name, valid_size_value


def transform_type_name(type_name: str) -> Optional[Tuple[str, str]]:
    """Transforms and validates a type name.

    This function converts a type name to uppercase, replaces spaces with underscores,
    and ensures the name contains only valid characters.

    Args:
        type_name (str): The type name to be transformed.

    Returns:
        Optional[Tuple[str, str]]: A tuple containing the original and transformed type name,
                                   or None if validation fails.
    """
    # Transform type name
    type_name = type_name.upper().strip()
    if not re.match(r"^[A-Z0-9 ]+$", type_name):
        return None

    type_value = type_name.replace(" ", "_")

    return type_name, type_value


def transform_color_name(color_name: str, color_hex: str) -> Optional[Tuple[str, str]]:
    """Transforms and validates a color name and hex code.

    This function converts a color name to uppercase, trims leading and trailing spaces,
    and ensures the color name contains only valid characters. It also validates that
    the hex code is exactly 6 uppercase hexadecimal characters.

    Args:
        color_name (str): The name of the color to be transformed and validated.
        color_hex (str): The hexadecimal color code to be validated.

    Returns:
        Optional[Tuple[str, str]]: A tuple containing the validated color name and hex code,
                                   or None if validation fails.
    """
    # Transform and validate color name
    color_name = color_name.upper().strip()
    if not re.match(r"^[A-Z0-9 ]+$", color_name):
        return None

    # Validate color hex code
    if not re.match(r"^[A-Fa-f0-9]{6}$", color_hex):
        return None

    return color_name, color_hex


def map_picklistfile_ids(picklist_files):
    file_ids = {
        "tik_file_id": None,
        "tok_file_id": None,
        "sho_file_id": None,
        "laz_file_id": None,
    }
    for file in picklist_files:
        if file.ecom_code == "TIK":
            file_ids["tik_file_id"] = file.id
        elif file.ecom_code == "TOK":
            file_ids["tok_file_id"] = file.id
        elif file.ecom_code == "SHO":
            file_ids["sho_file_id"] = file.id
        elif file.ecom_code == "LAZ":
            file_ids["laz_file_id"] = file.id
    return file_ids
