BRAND = {
    "name": "PrevSuite",
    "logo_path": "img/prevsuite-logo.svg",  # relativo a /static
    "accent_hex": "#ff6a3d",
    "accent2_hex": "#3b82f6",
}

# Códigos de vertical
VERTICALS = {
    "general":  {"label": "General Store",  "modules": ["inventory","sales","reports","forecast"]},
    "market":   {"label": "Market/Grocery", "modules": ["inventory","expiry","sales","reports","forecast"]},
    "apparel":  {"label": "Apparel",        "modules": ["inventory","sizes","promotions","sales","reports","forecast"]},
    "restaurant":{"label": "Restaurant (PrevFood)", "modules": ["menu","inventory","sales","reports","forecast"]},
    "electronics":{"label": "Electronics",  "modules": ["inventory","brands","warranty","sales","reports","forecast"]},
}

# Mapeia vertical -> rótulo do microapp (para header/título)
MICROAPPS = {
    "restaurant": {"name": "PrevFood", "logo_path": "img/Logo.jpg"},
}
