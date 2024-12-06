XLS_FILE_FORMAT = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

XLS = {
    "TIK": {
        "y_offset": {
            "header": 0,
            "data": 2,
        },
        "fields": {
            "ORDERID": {"INDEX": 0, "NAME": "Order ID"},
            "PRODUCT": {"INDEX": 7, "NAME": "Product Name"},
            "VARIANT": {"INDEX": 8, "NAME": "Variation"},
            "QUANTITY": {"INDEX": 9, "NAME": "Quantity"},
        },
    },
    "TOK": {
        "y_offset": {
            "header": 3,
            "data": 4,
        },
        "fields": {
            "ORDERID": {"INDEX": 3, "NAME": "No. Invoice"},
            "PRODUCT": {"INDEX": 2, "NAME": "Nama Produk"},
            "QUANTITY": {"INDEX": 4, "NAME": "Jumlah Produk"},
        },
    },
    "SHO": {
        "y_offset": {
            "header": 0,
            "data": 1,
        },
        "fields": {
            "ORDERID": {"INDEX": 1, "NAME": "order_sn"},
            "PRODUCT": {"INDEX": 7, "NAME": "product_info"},
        },
    },
    "LAZ": {
        "y_offset": {
            "header": 0,
            "data": 1,
        },
        "fields": {
            "ORDERID": {"INDEX": 3, "NAME": "OrderNumber"},
            "PRODUCT": {"INDEX": 2, "NAME": "Product"},
            "QUANTITY": {"INDEX": 4, "NAME": "Quantity"},
        },
    },
}
