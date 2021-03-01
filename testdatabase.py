import mysql.connector
import datetime
import random
import pandas as pds
import matplotlib as plot

class mydatabase():
    def __init__(self):
        # db=mysql.connector.connect()
        self.db = mysql.connector.connect(host="localhost", user="root", passwd="mysql0226",database="SBC")
        self.mycursor = self.db.cursor()

    def query(self,statement):
        try:
            self.mycursor.execute(statement)
        except:
            print("Statement formal is wrong, please check it")

    def create_table(self, table_name):
        self.mycursor.execute(
            "CREATE TABLE {}(Time DATETIME, Value DECIMAL(7,3), PRIMARY KEY(Time));".format(table_name))
        self.db.commit()

    def show_tables(self, key=None):
        if key == None:
            self.mycursor.execute(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'sbc'"
            )
        else:
            self.mycursor.execute(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'sbc' AND TABLE_NAME LIKE '%{}%'".format(key)
            )
        result = self.mycursor.fetchall()
        print(result)

    def insert_data(self,table_name, time, value):
        #time must be like '2021-02-17 20:36:26' or datetime.datetime(yy,mm,dd,hh,mm,ss) value is a decimal from -9999.999 to 9999.999
        #name must be consistent with P&ID
        data=(time,value)
        self.mycursor.execute(
            "INSERT INTO {} VALUES(%s, %s);".format(table_name),data)
        self.db.commit()

    def show_data(self,table_name,start_time=None, end_time=None):
        if start_time==None or end_time==None:
            print(start_time,end_time)
            query = "SELECT * FROM {}".format(table_name)
            self.mycursor.execute(query)
            for (Time, Value) in self.mycursor:
                print(str(table_name)+"| {} | {}".format(Time, Value))

        else:
            try:
                query = "SELECT * FROM {} WHERE Time BETWEEN %s AND %s".format(table_name)
                self.mycursor.execute(query,(start_time,end_time))
                for (Time, Value) in self.mycursor:
                    print(str(table_name)+"| {}| {}".format(Time, Value))
            except:
                print("SHOW ERROR!")

    def drop_table(self,table_name):
        self.mycursor.execute(
            "DROP TABLE {}".format(table_name))
        self.db.commit()

    def close_database(self):
        self.mycursor.close()
        self.db.close()


if __name__ == "__main__":
    db = mydatabase()
    now = datetime.datetime.now()

    db.create_table("PV1204")
    # db.insert_data("PV1102", now, random.randrange(100))
    # db.show_data("PV1102")

    db.show_tables("PV")

    db.close_database()
