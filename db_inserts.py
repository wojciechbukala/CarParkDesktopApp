# from datetime import datetime
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from db_create import AuthorizedCars, Cars

# engine = create_engine("sqlite:///CarPark.db", echo=True)

# Session = sessionmaker(bind=engine)
# session = Session()


# car1 = Cars(1, "ZS4567", datetime(2024, 10, 9, 8, 0, 0),
#                     datetime(2024, 12, 31, 23, 59, 59), True)

# car2 = Cars(2, "DW4567", datetime(2024, 10, 9, 8, 0, 0),
#                     datetime(2024, 12, 31, 23, 59, 59), True)

# car3 = Cars(3, "WE4567", datetime(2024, 10, 9, 8, 0, 0),
#                     datetime(2024, 12, 31, 23, 59, 59), False)


# session.add(car1)
# session.add(car2)
# session.add(car3)
# session.commit()


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_create import AuthorizedCars, Cars

class Inserts():
    def __init__(self):
        engine = create_engine("sqlite:///CarPark.db", echo=True)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def __del__(self):
        self.session.close()

    def insert_auth_car(self, license_plate, start_time, end_time):
        auth_car = AuthorizedCars(license_plate, start_time, end_time)
        session.add(auth_car)

if __name__ == "__main__":
    insert = Inserts()
    insert.insert_auth_car("ZS1235", )
    
