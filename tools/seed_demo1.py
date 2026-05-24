import sys
import os
import datetime

# Append src/backend to python path so imports resolve cleanly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/backend")))

from app.core.infrastructure import session_manager
from app.modules.Platform.domain.models import Tenant
from app.modules.Tenancy.domain.models import RestaurantProfile, TenantSettings
from app.modules.Stations.domain.models import Station
from app.modules.Tables.domain.models import Table
from app.modules.MenuCatalog.domain.models import MenuCategory, MenuItem

def main():
    print("Starting database seeding for tenant 'demo1'...")
    
    # 1. Update Platform Database Tenant Status to active
    with session_manager.platform_session() as plat_session:
        tenant = plat_session.query(Tenant).filter_by(slug="demo1").first()
        if not tenant:
            print("ERROR: Tenant 'demo1' not found in platform database!")
            sys.exit(1)
        
        tenant.status = "active"
        plat_session.add(tenant)
        plat_session.commit()
        print("Updated tenant 'demo1' status to 'active' in platform control-plane database.")

    # 2. Seed Tenant Database
    with session_manager.tenant_session("demo1") as tenant_session:
        # Clear existing data if any (idempotency)
        tenant_session.query(MenuItem).delete()
        tenant_session.query(MenuCategory).delete()
        tenant_session.query(Station).delete()
        tenant_session.query(Table).delete()
        tenant_session.query(TenantSettings).delete()
        tenant_session.query(RestaurantProfile).delete()
        tenant_session.commit()
        print("Cleared any existing data in demo1 tenant database.")

        # Seed Restaurant Profile
        profile = RestaurantProfile(
            name="Moda Cafe & Lounge",
            default_locale="tr-TR",
            default_currency="TRY",
            timezone="Europe/Istanbul"
        )
        tenant_session.add(profile)
        
        # Seed Tenant Settings
        settings = TenantSettings(
            self_ordering_active=True,
            station_acceptance_required=True
        )
        tenant_session.add(settings)
        
        # Seed Stations
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
        tenant_session.add(kitchen_station)
        tenant_session.add(bar_station)
        tenant_session.commit()
        print("Seeded profile, settings, and stations.")

        # Seed Categories
        burger_cat = MenuCategory(name="Burgerler", display_order=1)
        pasta_cat = MenuCategory(name="Makarnalar", display_order=2)
        dessert_cat = MenuCategory(name="Tatlılar", display_order=3)
        drink_cat = MenuCategory(name="İçecekler", display_order=4)
        
        tenant_session.add(burger_cat)
        tenant_session.add(pasta_cat)
        tenant_session.add(dessert_cat)
        tenant_session.add(drink_cat)
        tenant_session.commit()
        print("Seeded menu categories.")

        # Seed Menu Items
        menu_items = [
            # Burgerler
            MenuItem(name="Moda Burger", price=320.00, status="active", category_id=burger_cat.id, station_code="kitchen_main"),
            MenuItem(name="Cheeseburger", price=290.00, status="active", category_id=burger_cat.id, station_code="kitchen_main"),
            MenuItem(name="Tavuk Burger", price=260.00, status="active", category_id=burger_cat.id, station_code="kitchen_main"),
            
            # Makarnalar
            MenuItem(name="Penne Arabbiata", price=240.00, status="active", category_id=pasta_cat.id, station_code="kitchen_main"),
            MenuItem(name="Fettuccine Alfredo", price=280.00, status="active", category_id=pasta_cat.id, station_code="kitchen_main"),
            
            # Tatlılar
            MenuItem(name="San Sebastian Cheesecake", price=180.00, status="active", category_id=dessert_cat.id, station_code="kitchen_main"),
            MenuItem(name="Çikolatalı Sufle", price=160.00, status="active", category_id=dessert_cat.id, station_code="kitchen_main"),
            
            # İçecekler
            MenuItem(name="Ev Yapımı Limonata", price=90.00, status="active", category_id=drink_cat.id, station_code="bar_beverages"),
            MenuItem(name="Freddo Espresso", price=110.00, status="active", category_id=drink_cat.id, station_code="bar_beverages"),
            MenuItem(name="Taze Portakal Suyu", price=100.00, status="active", category_id=drink_cat.id, station_code="bar_beverages"),
        ]
        
        for item in menu_items:
            tenant_session.add(item)
            
        # Seed Tables with permanent test QR tokens
        far_future = datetime.datetime.now() + datetime.timedelta(days=3650) # 10 years
        
        tables = [
            Table(table_number="Masa 1", status="active", qr_token="demo_token_1", qr_expires_at=far_future),
            Table(table_number="Masa 2", status="active", qr_token="demo_token_2", qr_expires_at=far_future),
            Table(table_number="Masa 3", status="active", qr_token="demo_token_3", qr_expires_at=far_future),
            Table(table_number="Masa 4", status="active", qr_token="demo_token_4", qr_expires_at=far_future),
            Table(table_number="Masa 5", status="active", qr_token="demo_token_5", qr_expires_at=far_future),
        ]
        
        for table in tables:
            tenant_session.add(table)
            
        tenant_session.commit()
        print("Seeded menu items and physical tables successfully.")
        
        print("\nDemo QR URLs for customer ordering:")
        for table in tables:
            print(f"  {table.table_number}: https://demo1.iotables.net/g/{table.qr_token}")

if __name__ == "__main__":
    main()
