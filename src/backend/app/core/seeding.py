import os
import re
import uuid
import secrets
import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.modules.Tenancy.domain.models import RestaurantProfile, TenantSettings
from app.modules.Stations.domain.models import Station
from app.modules.Tables.domain.models import Table
from app.modules.MenuCatalog.domain.models import MenuCategory, MenuItem

def parse_moda_data():
    """
    Parses categories and items from moda_src/moda-cafe/js/data.js using robust regex.
    Returns a tuple of (categories_list, items_dict).
    """
    # Locate data.js file path
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    data_path = os.path.join(base_dir, "moda_src/moda-cafe/js/data.js")
    
    if not os.path.exists(data_path):
        print(f"Warning: data.js not found at {data_path}, fallback to default seeding.")
        return [], {}
        
    with open(data_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Extract CATEGORIES array
    # Search for const CATEGORIES = [ ... ];
    categories = []
    cat_match = re.search(r"const\s+CATEGORIES\s*=\s*\[(.*?)\]\s*;", content, re.DOTALL)
    if cat_match:
        cat_block = cat_match.group(1)
        # Parse single category objects: { id: "...", name: "...", image: "..." }
        cat_objects = re.findall(r"\{\s*id:\s*[\"'](.*?)[\"']\s*,\s*name:\s*[\"'](.*?)[\"']\s*,\s*image:\s*[\"'](.*?)[\"']\s*\}", cat_block)
        for idx, (cid, cname, cimage) in enumerate(cat_objects):
            categories.append({
                "slug": cid,
                "name": cname,
                "display_order": idx + 1
            })
            
    # Extract MENU_ITEMS object
    # Search for const MENU_ITEMS = { ... };
    items_dict = {}
    items_match = re.search(r"const\s+MENU_ITEMS\s*=\s*\{(.*?)\}\s*;\s*$", content, re.DOTALL)
    if not items_match:
        # Retry matching without the trailing end-of-file anchor
        items_match = re.search(r"const\s+MENU_ITEMS\s*=\s*\{(.*?)\}\s*;", content, re.DOTALL)
        
    if items_match:
        items_block = items_match.group(1)
        # Split by category key block, e.g. "biralar": [ ... ]
        cat_blocks = re.findall(r"[\"'](.*?)[\"']\s*:\s*\[(.*?)(?=\]|\Z)", items_block, re.DOTALL)
        for cat_slug, item_list_block in cat_blocks:
            # Parse individual item objects: { name: "...", desc: "...", image: "..." }
            # Some items might have null image or missing desc
            item_objects = re.findall(r"\{\s*name:\s*[\"'](.*?)[\"']\s*,\s*desc:\s*[\"'](.*?)[\"']\s*,\s*image:\s*(?:[\"'](.*?)[\"']|null)\s*\}", item_list_block)
            
            # Also catch simpler objects without desc or image details
            if not item_objects:
                item_objects = re.findall(r"\{\s*name:\s*[\"'](.*?)[\"']\s*,\s*desc:\s*[\"'](.*?)[\"']\s*(?:,\s*image:\s*(?:[\"'](.*?)[\"']|null))?\s*\}", item_list_block)
            
            items_list = []
            for item in item_objects:
                name = item[0]
                desc = item[1] if len(item) > 1 else ""
                items_list.append({
                    "name": name,
                    "desc": desc
                })
            items_dict[cat_slug] = items_list
            
    return categories, items_dict

def get_default_price(category_name: str) -> Decimal:
    """Assigns reasonable default pricing based on category classification."""
    cat = category_name.upper()
    if any(k in cat for k in ["BİRA", "ŞARAP", "ALKOLLÜ", "KOKTEYL"]):
        return Decimal("180.00")
    if any(k in cat for k in ["SOĞUK İÇECEK", "SICAK İÇECEK", "KAHVE"]):
        return Decimal("90.00")
    if "GÜNE BAŞLARKEN" in cat:
        return Decimal("165.00")
    if "NARGİLE" in cat:
        return Decimal("250.00")
    if "ATIŞTIRMALIK" in cat:
        return Decimal("140.00")
    if "HAMBURGER" in cat:
        return Decimal("280.00")
    if "SALATA" in cat:
        return Decimal("150.00")
    if "ANA YEMEK" in cat:
        return Decimal("320.00")
    if "PİZZA" in cat:
        return Decimal("260.00")
    if "MAKARNA" in cat:
        return Decimal("240.00")
    if "TATLI" in cat:
        return Decimal("120.00")
    return Decimal("150.00")

def seed_tenant_database(session: Session, tenant_slug: str, restaurant_name: str = "Moda Cafe"):
    """
    Seeds a freshly provisioned tenant database with all profile, station,
    categories, items, and tables retrieved from moda_src.
    """
    # 1. Seed Restaurant Profile
    profile = RestaurantProfile(
        name=restaurant_name,
        default_locale="tr-TR",
        default_currency="TRY",
        timezone="Europe/Istanbul"
    )
    session.add(profile)
    
    # 2. Seed Tenant Settings
    settings = TenantSettings(
        self_ordering_active=True,
        station_acceptance_required=True
    )
    session.add(settings)
    
    # 3. Seed Preparation Stations
    kitchen_station = Station(
        code="kitchen_main",
        name="Ana Mutfak",
        status="active"
    )
    bar_station = Station(
        code="bar_beverages",
        name="Bar / İçecekler",
        status="active"
    )
    session.add(kitchen_station)
    session.add(bar_station)
    session.commit()
    
    # 4. Parse categories & items from moda_src/data.js
    categories, items_dict = parse_moda_data()
    
    # If no categories were parsed from data.js, fallback to a minimal subset
    if not categories:
        categories = [
            {"slug": "hamburgerler", "name": "HAMBURGERLER", "display_order": 1},
            {"slug": "makarnalar", "name": "MAKARNALAR", "display_order": 2},
            {"slug": "tatlilar", "name": "TATLILAR", "display_order": 3},
            {"slug": "soguk-icecekler", "name": "SOĞUK İÇECEKLER", "display_order": 4},
        ]
        items_dict = {
            "hamburgerler": [{"name": "Moda Burger"}],
            "makarnalar": [{"name": "Penne Arabbiata"}],
            "tatlilar": [{"name": "San Sebastian"}],
            "soguk-icecekler": [{"name": "Ev Yapımı Limonata"}]
        }

    # 5. Insert Categories and Items
    for cat_data in categories:
        category = MenuCategory(
            name=cat_data["name"],
            display_order=cat_data["display_order"]
        )
        session.add(category)
        session.commit()
        session.refresh(category)
        
        # Insert items belonging to this category
        items = items_dict.get(cat_data["slug"], [])
        for item_data in items:
            # Smartly route drinks/beverages to bar station, other to kitchen
            is_drink = any(k in cat_data["name"].upper() for k in ["BİRA", "ŞARAP", "KOKTEYL", "İÇECEK", "KAHVE", "VOTKA", "CİN", "TEKİLA"])
            station_code = "bar_beverages" if is_drink else "kitchen_main"
            
            price = get_default_price(cat_data["name"])
            
            menu_item = MenuItem(
                name=item_data["name"],
                price=price,
                status="active",
                category_id=category.id,
                station_code=station_code
            )
            session.add(menu_item)
            
    # 6. Seed 5 Default Tables with automatically generated secure active QR tokens
    far_future = datetime.datetime.now() + datetime.timedelta(days=3650) # 10 years
    for i in range(1, 6):
        # Generate table secure QR token
        qr_token = f"qr_t_{secrets.token_hex(8)}"
        table = Table(
            table_number=f"Masa {i}",
            status="active",
            qr_token=qr_token,
            qr_expires_at=far_future
        )
        session.add(table)
        
    session.commit()
    print(f"Tenant database '{tenant_slug}' seeded successfully with {len(categories)} categories.")
