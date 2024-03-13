import os.path
from sshtunnel import SSHTunnelForwarder
import mysql.connector
import datetime
import time as tm
import paramiko, pymysql
import random
import pandas as pd
# import matplotlib as plot

"""PASSWORD IN THIS DOCUMENT are saved as enviroment variable at slowcontrol machine
 You can also get it from SBC mysql document configuration
 https://docs.google.com/document/d/1o2LEL3cKEVQ6zuR_jJgt-p3UgnVysMm6LkXXOvfMZeE/edit
 """


def datetime_in_s():
    d=datetime.datetime.now()
    timeR = int(d.microsecond%1e6)
    delta=datetime.timedelta(microseconds=timeR)
    x=d-delta
    return x

def datetime_in_1e5micro():
    d=datetime.datetime.now()
    timeR = int(d.microsecond%1e5)
    delta=datetime.timedelta(microseconds=timeR)
    x=d-delta
    return x

def early_datetime():
    d = datetime.datetime.now()
    timeR = int(d.microsecond % 1e5)
    delta = datetime.timedelta(microseconds=timeR)
    x = d - delta - datetime.timedelta(microseconds=1e5)
    return x

def later_datetime():
    d = datetime.datetime.now()
    timeR = int(d.microsecond % 1e5)
    delta = datetime.timedelta(microseconds=timeR)
    x = d - delta + datetime.timedelta(microseconds=1e5)
    return x

def UNIX_time(self):
    return int(tm.time())



class mydatabase():
    def __init__(self):
        # db=mysql.connector.connect()
        self.db = mysql.connector.connect(host="localhost", user="slowcontrol", passwd=os.environ.get("SLOWCONTROL_LOCAL_TOKEN"), database="SBCslowcontrol")

        self.mycursor = self.db.cursor()
        self.stack= pd.DataFrame(columns=['Instrument', 'Time', 'Value'])

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

    def insert_data_into_datastorage_wocommit(self,instrument, time,value):
        # time must be like '2021-02-17 20:36:26' or datetime.datetime(yy,mm,dd,hh,mm,ss)
        # value is a decimal from -9999.999 to 9999.999
        # name must be consistent with P&ID
        data=(instrument, time,value)
        self.mycursor.execute(
            "INSERT INTO DataStorage (Instrument, Time, Value) VALUES(%s, %s, %s);", data)
    def insert_data_into_stack(self,instrument, time,value):
        # time must be like '2021-02-17 20:36:26' or datetime.datetime(yy,mm,dd,hh,mm,ss)
        # value is a decimal from -9999.999 to 9999.999
        # name must be consistent with P&ID
        data=(instrument, time,value)
        new_df=pd.DataFrame({'Instrument':instrument,"Time":time,"Value": value},index=[len(self.stack)])
        self.stack = pd.concat((self.stack,new_df), axis=0,ignore_index= True)

    def sort_stack(self):
        self.stack = self.stack.sort_values(by=['Time'])
        self.stack = self.stack.reset_index(drop=True)
        # print("first", self.stack.iloc[:5])
        # print("last",self.stack.iloc[-5:])

    def convert_stack_into_queries(self):
        for idx in self.stack.index:
            newdata = (self.stack['Instrument'][idx], self.stack['Time'][idx], self.stack['Value'][idx])
            # print(newdata)

            self.mycursor.execute(
                "INSERT INTO DataStorage (Instrument, Time, Value) VALUES(%s, %s, %s);", newdata)

    def drop_stack(self):
        self.stack = self.stack.iloc[0:0]
        # print(self.stack)

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


class COUPP_database():
    def __init__(self):
        # save the password in ENV at sbcslowcontrol machine
        self.home = os.path.expanduser('~')
        self.sql_hostname = 'localhost'
        self.sql_username = 'coupp_monitor'
        self.sql_password = os.environ.get("COUPP_SQL_TOKEN")
        self.sql_main_database = 'coupp_alarms'
        self.sql_port = 3306
        self.ssh_host = 'dm.phys.northwestern.edu'
        self.ssh_password = os.environ.get("PEGASUS_SSH_TOKEN")
        self.ssh_user = 'pico'
        self.ssh_port = 22
        self.sql_ip = '1.1.1.1'
        print(self.ssh_password)

    def ssh_write(self):
        with SSHTunnelForwarder(
                (self.ssh_host, self.ssh_port),
                ssh_username=self.ssh_user,
                ssh_password= self.ssh_password,
                remote_bind_address=(self.sql_hostname, self.sql_port)) as tunnel:

            self.db = pymysql.connect(host="localhost", user=self.sql_username, passwd=self.sql_password, database=self.sql_main_database, port=tunnel.local_bind_port)
            self.mycursor = self.db.cursor()
            self.update_alarm()
            self.close_database()

            # conn = pymysql.connect(host='127.0.0.1', user=sql_username,
            #                        passwd=sql_password, db=sql_main_database,
            #                        port=tunnel.local_bind_port)
            # query = '''SELECT VERSION();'''
            # data = pd.read_sql_query(query, conn)
            # conn.close()

    def ssh_select(self):
        with SSHTunnelForwarder(
                (self.ssh_host, self.ssh_port),
                ssh_username=self.ssh_user,
                ssh_password= self.ssh_password,
                remote_bind_address=(self.sql_hostname, self.sql_port)) as tunnel:
            print("pointer 0")
            print(tunnel.local_bind_port)
            self.db = pymysql.connect(host="127.0.0.1", user=self.sql_username, passwd=self.sql_password, database=self.sql_main_database, port=tunnel.local_bind_port)
            # self.db = mysql.connector.connect(host="127.0.0.1", user=self.sql_username, passwd=self.sql_password, database=self.sql_main_database, port=tunnel.local_bind_port)
            self.mycursor = self.db.cursor()
            self.show_data()
            self.close_database()


            # conn = pymysql.connect(host='127.0.0.1', user=sql_username,
            #                        passwd=sql_password, db=sql_main_database,
            #                        port=tunnel.local_bind_port)
            # query = '''SELECT VERSION();'''
            # data = pd.read_sql_query(query, conn)
            # conn.close()
    def ssh_state_only(self):
        with SSHTunnelForwarder(
                (self.ssh_host, self.ssh_port),
                ssh_username=self.ssh_user,
                ssh_password= self.ssh_password,
                remote_bind_address=(self.sql_hostname, self.sql_port)) as tunnel:
            print("pointer 0")
            print(tunnel.local_bind_port)
            self.db = pymysql.connect(host="127.0.0.1", user=self.sql_username, passwd=self.sql_password, database=self.sql_main_database, port=tunnel.local_bind_port)
            # self.db = mysql.connector.connect(host="127.0.0.1", user=self.sql_username, passwd=self.sql_password, database=self.sql_main_database, port=tunnel.local_bind_port)
            self.mycursor = self.db.cursor()
            state = self.show_status()
            self.close_database()
        return state

    def show_data(self,start_time=None, end_time=None):
        # if start_time==None or end_time==None:
        print(start_time,end_time)
        query = "SELECT * FROM sbc_FNAL_alarms"
        self.mycursor.execute(query)
        for (id,datime,alarm_state, alarm_message) in self.mycursor:
            print(str("Alarm_info"+"| {} | {} | {}".format(datime,alarm_state, alarm_message)))

    def show_status(self,start_time=None, end_time=None):
        # if start_time==None or end_time==None:
        print(start_time,end_time)
        query = "SELECT * FROM sbc_FNAL_alarms"
        self.mycursor.execute(query)
        for (id,datime,alarm_state, alarm_message) in self.mycursor:
            print(str("Alarm_info"+"| {} | {} | {}".format(datime,alarm_state, alarm_message)))
        return alarm_state

    def update_alarm(self):
        Unixtime = int(tm.time())
        state = 'OK'
        message = 'AOK'
        data = (Unixtime, state, message)
        self.mycursor.execute(
            "UPDATE sbc_FNAL_alarms SET datime=%s, alarm_state=%s, alarm_message=%s WHERE id=1;", data)
        self.db.commit()
        # self.close_database()


    def ssh_alarm(self,message="AOK"):
        with SSHTunnelForwarder(
                (self.ssh_host, self.ssh_port),
                ssh_username=self.ssh_user,
                ssh_password= self.ssh_password,
                remote_bind_address=(self.sql_hostname, self.sql_port)) as tunnel:

            self.db = pymysql.connect(host="localhost", user=self.sql_username, passwd=self.sql_password, database=self.sql_main_database, port=tunnel.local_bind_port)
            self.mycursor = self.db.cursor()

            self.update_status(message)
            # limit the max lengh of the string
            self.close_database()


    def update_status(self, message='AOK'):
        Unixtime = int(tm.time())
        state = 'ALARM'

        data = (Unixtime, state, message)
        self.mycursor.execute(
            "UPDATE sbc_FNAL_alarms SET datime=%s, alarm_state=%s, alarm_message=%s WHERE id=1;", data)
        self.db.commit()
        # self.close_database()


    def close_database(self):
        self.mycursor.close()
        self.db.close()

    def test_gateway(self):
        ssh_config = {
            'hostname': self.ssh_host,
            'port': 22,
            'username': self.ssh_user,
            'password': self.ssh_password,
        }

        # MySQL connection details
        db_config = {
            'host': self.sql_hostname,
            'user': self.sql_username,
            'password': self.sql_password,
            'database': self.sql_main_database,
        }

        # Establish an SSH connection
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh_client.connect(**ssh_config)

            # MySQL connection through SSH tunnel
            with ssh_client.get_transport().open_channel('direct-tcpip', (db_config['host'], 3306),
                                                         ('localhost', 0)) as tunnel:
                db_config['host'] = '127.0.0.1'
                db_config['port'] = tunnel.local_address[1]

                # Establish a connection to the MySQL database
                connection = mysql.connector.connect(**db_config)
                # cursor = connection.cursor()
                #
                # # Example: Insert data into a table
                # sql_query = "INSERT INTO your_table_name (column1, column2) VALUES (%s, %s)"
                # data_to_insert = ('value1', 'value2')
                #
                # cursor.execute(sql_query, data_to_insert)
                #
                # # Commit changes and close connection
                # connection.commit()
                connection.close()

        finally:
            ssh_client.close()

"""
good example of how to check mysql connections
import mysql.connector
from mysql.connector import Error
import time

def connect_to_database():
    while True:
        try:
            # Attempt to establish a connection to the MySQL database
            connection = mysql.connector.connect(
                host="localhost", user="slowcontrol", passwd=os.environ.get("SLOWCONTROL_LOCAL_TOKEN"), database="SBCslowcontrol")


            if connection.is_connected():
                print("Connected to MySQL database")

                # Print a string every 1 second if the connection is established
                while True:
                    try:
                        # Check if the connection is still alive
                        connection.ping(reconnect=True)

                        # Perform database operation
                        print("Doing something in the database...")

                    except mysql.connector.Error as e:
                        # Handle database errors (e.g., connection lost)
                        print("Database error:", e)
                        print("Attempting to reconnect...")
                        break  # Exit the inner loop to attempt reconnection

                    time.sleep(1)

        except Error as e:
            # Handle connection errors (e.g., initial connection failure)
            print("Error connecting to MySQL database:", e)
            print("Retrying connection in 5 seconds...")
            time.sleep(5)

"""

# test sbcslowcontrol database

if __name__ == "__main__":
    connection = connect_to_database()

    # db = mydatabase()
    # dt = datetime_in_s()
    # early_dt = early_datetime()
    # # unix_timestamp = int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())
    # print(dt)
    # # print(unix_timestamp)
    # # db.insert_data_into_datastorage("test",dt,500.55)
    #
    # db.insert_data_into_stack("PV5535", early_dt, 0)
    # db.insert_data_into_stack("PV5535", dt, 1)
    # db.insert_data_into_stack("PV5485", early_dt, 1)
    # db.insert_data_into_stack("PV5485", dt, 0)
    # db.insert_data_into_stack("PV5935", early_dt, 0)
    # db.insert_data_into_stack("PV5595", dt, 1)
    # db.sort_stack()

    # db.show_data_datastorage()

    # db.create_table("PV1204")
    # db.insert_data("PV1102", now, random.randrange(100))
    # db.show_data("PV1102")

    # db.show_tables()

    # db.close_database()

    #test datetime function
    # print(datetime_in_1e5micro())
    # print(early_datetime())

#test NW sbc alarm database

# if __name__ == "__main__":
    # db = COUPP_database()
    # dt = datetime_in_s()
    # unix_timestamp = int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())
    # print(dt)
    # print(unix_timestamp)
    # db.insert_data_into_datastorage("test",dt,500.55)
    # db.ssh_select()
    # db.ssh_write()
    # db.ssh_select()
    # print(db.ssh_state_only())
    # db.test_gateway()


    # db.close_database()

    #test datetime function
    # print(datetime_in_1e5micro())
    # print(early_datetime())

