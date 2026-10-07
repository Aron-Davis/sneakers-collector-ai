# Casi di valutazione per l'estrazione strutturata delle sneaker.
EXTRACTION_CASES = [
    # Casi standard in italiano.
    {
        "name": "jordan_chicago",
        "input": (
            "Ho comprato delle Nike Air Jordan 1 Chicago "
            "taglia 43 EU, usate, con scatola, pagate 180 euro."
        ),
        "expected": {
            "brand": "Nike",
            "size": 43,
            "size_system": "EU",
            "condition": "used",
            "purchase_price": 180,
            "currency": "EUR",
            "has_box": True,
        },
    },
    {
        "name": "new_balance_without_box",
        "input": (
            "Ho delle New Balance 990v6 grigie taglia 43 EU, "
            "le ho usate parecchio e non ho più la scatola."
        ),
        "expected": {
            "brand": "New Balance",
            "model": "990v6",
            "size": 43,
            "size_system": "EU",
            "condition": "used",
            "has_box": False,
        },
    },
    {
        "name": "air_max_anniversary",
        "input": "Nike Air Max 1 Anniversary Red, US 10.5, comprate per 160 dollari.",
        "expected": {
            "brand": "Nike",
            "model": "Air Max 1",
            "colorway": "Anniversary Red",
            "size": 10.5,
            "size_system": "US",
            "purchase_price": 160,
            "currency": "USD",
        },
    },
    {
        "name": "gel_kayano_like_new",
        "input": (
            "Asics Gel-Kayano 14 Silver, praticamente nuove, "
            "taglia 42 EU, prese a 150 euro."
        ),
        "expected": {
            "brand": "Asics",
            "model": "Gel-Kayano 14",
            "colorway": "Silver",
            "size": 42,
            "size_system": "EU",
            "condition": "like_new",
            "purchase_price": 150,
            "currency": "EUR",
        },
    },
    {
        "name": "adidas_new_with_box",
        "input": (
            "Adidas Samba OG White Black, taglia 42 EU, nuove mai indossate, "
            "con scatola originale, pagate 120 euro."
        ),
        "expected": {
            "brand": "Adidas",
            "model": "Samba OG",
            "colorway": "White Black",
            "size": 42,
            "size_system": "EU",
            "condition": "new",
            "purchase_price": 120,
            "currency": "EUR",
            "has_box": True,
        },
    },
    {
        "name": "nike_worn_without_box",
        "input": (
            "Nike Dunk Low Grey Fog taglia 44 EU, molto consumate "
            "e senza scatola, pagate 90 euro."
        ),
        "expected": {
            "brand": "Nike",
            "model": "Dunk Low",
            "colorway": "Grey Fog",
            "size": 44,
            "size_system": "EU",
            "condition": "worn",
            "purchase_price": 90,
            "currency": "EUR",
            "has_box": False,
        },
    },
    # Casi con formati, identificatori e date esplicite.
    {
        "name": "uk_size_gbp",
        "input": (
            "New Balance 2002R Protection Pack Rain Cloud, UK 9, used, "
            "paid 140 GBP."
        ),
        "expected": {
            "brand": "New Balance",
            "model": "2002R",
            "colorway": "Protection Pack Rain Cloud",
            "size": 9,
            "size_system": "UK",
            "condition": "used",
            "purchase_price": 140,
            "currency": "GBP",
        },
    },
    {
        "name": "explicit_style_code",
        "input": "Nike Air Force 1 White, style code CW2288-111, taglia 43 EU.",
        "expected": {
            "brand": "Nike",
            "model": "Air Force 1",
            "colorway": "White",
            "style_code": "CW2288-111",
            "size": 43,
            "size_system": "EU",
        },
    },
    {
        "name": "explicit_purchase_date",
        "input": (
            "Asics GT-2160 White Silver taglia 41 EU, "
            "comprate il 15 gennaio 2026 per 130 euro."
        ),
        "expected": {
            "brand": "Asics",
            "model": "GT-2160",
            "colorway": "White Silver",
            "size": 41,
            "size_system": "EU",
            "purchase_price": 130,
            "currency": "EUR",
            "purchase_date": "2026-01-15",
        },
    },
    # Casi con informazioni parziali o mancanti.
    {
        "name": "missing_brand",
        "input": "Gel-Kayano 14 Silver, taglia 42 EU, usate.",
        "expected": {
            "brand": None,
            "model": "Gel-Kayano 14",
            "colorway": "Silver",
            "size": 42,
            "size_system": "EU",
            "condition": "used",
        },
    },
    {
        "name": "minimal_information",
        "input": "Ho delle Adidas Campus 00s.",
        "expected": {
            "brand": "Adidas",
            "model": "Campus 00s",
            "size": None,
            "purchase_price": None,
            "has_box": None,
        },
    },
    # Caso in inglese per verificare l'estrazione multilingua.
    {
        "name": "english_like_new",
        "input": (
            "Nike Air Max 90 Infrared, US size 10, almost new, "
            "original box included, paid 170 dollars."
        ),
        "expected": {
            "brand": "Nike",
            "model": "Air Max 90",
            "colorway": "Infrared",
            "size": 10,
            "size_system": "US",
            "condition": "like_new",
            "purchase_price": 170,
            "currency": "USD",
            "has_box": True,
        },
    },
]
