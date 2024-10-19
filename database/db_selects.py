from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.db_create import AuthorizedCars, Cars

class Selects():
    def __init__(self):
        engine = create_engine("sqlite:///CarPark.db", echo=True)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def __del__(self):
        self.session.close()

    def get_current_cars(self):
        cars_list = []
        result = self.session.query(Cars).filter_by(currently_parked=True)
        for row in result:
            cars_list.append([row.carID, row.license_plate, row.entry_time, row.exit_time])

        return cars_list

    def get_auth_cars(self):
        cars_list = []
        result = self.session.query(AuthorizedCars)
        for row in result:
            cars_list.append([row.license_plate, row.authorization_start_date, row.authorization_end_date])

        return cars_list

if __name__ == "__main__":
    selects = Selects()
    print(selects.get_current_cars())