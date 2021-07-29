import mysql.connector
import datetime
import random
# import pandas as pds
# import matplotlib as plot


def datetime_in_s():
    d=datetime.datetime.now()
    x=d-datetime.timedelta(microseconds=d.microsecond)
    return x


class mydatabase():
    def __init__(self):
        # db=mysql.connector.connect()
        self.db = mysql.connector.connect(host="localhost", user="slowcontrol", passwd="Th3Slow1!",database="SBCslowcontrol")
        self.mycursor = self.db.cursor()

    def query(self,statement):
        try:
            self.mycursor.execute(statement)
        except:
            print("Statement formal is wrong, please check it")
    # user slowcontrol doesn't have permission to create tables. Besides, table columVn name should be different
    # def create_table(self, table_name):
    #     self.mycursor.execute(
    #         "CREATE TABLE {}(Time DATETIME, Value DECIMAL(7,3), PRIMARY KEY(Time));".format(table_name))
    #     self.db.commit()

    def show_tables(self, key=None):
        if key is None:
            self.mycursor.execute(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'SBCslowcontrol'"
            )
        else:
            self.mycursor.execute(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'sbc' AND TABLE_NAME LIKE '%{}%'".format(key)
            )
        result = self.mycursor.fetchall()
        print(result)

    def insert_data_into_datastorage(self,instrument, time,value):
        # time must be like '2021-02-17 20:36:26' or datetime.datetime(yy,mm,dd,hh,mm,ss)
        # value is a decimal from -9999.999 to 9999.999
        # name must be consistent with P&ID
        data=(instrument, time,value)
        self.mycursor.execute(
            "INSERT INTO DataStorage (Instrument, Time, Value) VALUES(%s, %s, %s);", data)
        self.db.commit()

    def insert_data_into_metadata(self,instrument, Description,Unit):
        # time must be like '2021-02-17 20:36:26' or datetime.datetime(yy,mm,dd,hh,mm,ss)
        # value is a decimal from -9999.999 to 9999.999
        # name must be consistent with P&ID
        data=(instrument, Description,Unit)
        self.mycursor.execute(
            "INSERT INTO MetaDataStorage VALUES(%s, %s, %s);", data)
        self.db.commit()

    def show_data_datastorage(self,start_time=None, end_time=None):
        # if start_time==None or end_time==None:
        print(start_time,end_time)
        query = "SELECT * FROM DataStorage"
        self.mycursor.execute(query)
        for (ID,Instrument,Time, Value) in self.mycursor:
            print(str("DataStorage"+"| {} | {} | {}".format(Instrument,Time, Value)))

    def show_data_metadatastorage(self):
        query = "SELECT * FROM MetaDataStorage"
        self.mycursor.execute(query)
        for (Instrument, Description, unit) in self.mycursor:
            print(str("MetaDataStorage" + "| {} | {} | {}".format(Instrument, Description, unit)))

        # else:
        #     try:
        #         query = "SELECT * FROM {} WHERE Time BETWEEN %s AND %s".format(table_name)
        #         self.mycursor.execute(query,(start_time,end_time))
        #         for (Time, Value) in self.mycursor:
        #             print(str(table_name)+"| {}| {}".format(Time, Value))
        #     except:
        #         print("SHOW ERROR!")

    # No permission on user sbcslowcontrol
    # def drop_table(self,table_name):
    #     self.mycursor.execute(
    #         "DROP TABLE {}".format(table_name))
    #     self.db.commit()

    def close_database(self):
        self.mycursor.close()
        self.db.close()


if __name__ == "__main__":
    db = mydatabase()
    dt = datetime_in_s()
    # unix_timestamp = int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())
    print(dt)
    # print(unix_timestamp)
    db.insert_data_into_datastorage("test",dt,500.55)
    db.show_data_datastorage()

    # db.create_table("PV1204")
    # db.insert_data("PV1102", now, random.randrange(100))
    # db.show_data("PV1102")

    db.show_tables()

    db.close_database()
