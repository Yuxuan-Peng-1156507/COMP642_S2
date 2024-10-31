from database import engine, db_session
from models import (
    Base, PrivateCustomer, CorporateCustomer, Staff,
    WeightedVeggie, PackVeggie, UnitPriceVeggie,
    PremadeBox, Veggie
)
import datetime

def insert_initial_data():
    try:
        Base.metadata.drop_all(engine)  
        Base.metadata.create_all(engine) 

        private_customer_person = PrivateCustomer(
            first_name='John',
            last_name='Doe',
            username='johndoe',
            cust_address='123 Main St',
            max_owing=100.0
        )
        private_customer_person.set_password('password123')
        db_session.add(private_customer_person)
        

        corporate_customer_person = CorporateCustomer(
            first_name='Alice',
            last_name='Smith',
            username='alicesmith',
            cust_address='456 Corporate Ave',
            max_credit=1000.0,
            discount_rate=0.1
        )
        corporate_customer_person.set_password('password123')
        db_session.add(corporate_customer_person)
        

        staff_member = Staff(
            first_name='Bob',
            last_name='Johnson',
            username='bobjohnson',
            dept_name='Sales',
            date_joined=datetime.datetime.now()
        )
        staff_member.set_password('password123')
        db_session.add(staff_member)
        
        db_session.commit()
        

        carrot = WeightedVeggie(
            veg_name='Carrot',
            veg_type='weighted',
            price_per_kilo=2.5
        )
        db_session.add(carrot)
        

        spinach = PackVeggie(
            veg_name='Spinach',
            veg_type='pack',
            pack_size=1,
            price_per_pack=3.0
        )
        db_session.add(spinach)
        

        tomato = UnitPriceVeggie(
            veg_name='Tomato',
            veg_type='unit_price',
            price_per_unit=0.5
        )
        db_session.add(tomato)
        

        cucumber = UnitPriceVeggie(
            veg_name='Cucumber',
            veg_type='unit_price',
            price_per_unit=0.3
        )
        db_session.add(cucumber)
        
        broccoli = WeightedVeggie(
            veg_name='Broccoli',
            veg_type='weighted',
            price_per_kilo=1.8
        )
        db_session.add(broccoli)
        
        db_session.commit()
        

        small_box = PremadeBox(
            box_size='small',
            price=15.0
        )
        medium_box = PremadeBox(
            box_size='medium',
            price=25.0
        )
        large_box = PremadeBox(
            box_size='large',
            price=35.0
        )
        db_session.add_all([small_box, medium_box, large_box])
        
        db_session.commit()
        

        small_box.assemble_box(db_session)
        medium_box.assemble_box(db_session)
        large_box.assemble_box(db_session)
        db_session.commit()

        print("Success.")
    except Exception as e:
        db_session.rollback()
        print(f"Error：{e}")
    finally:
        db_session.remove()

if __name__ == '__main__':
    insert_initial_data()
