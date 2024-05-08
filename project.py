import mysql.connector
from mysql.connector import Error
from datetime import datetime
import sys

#Help function for sending query to server
def send_query(cursor, query):
    """Help function for executing queries"""
    try:
        cursor.execute(query)
        return True
    except Error:
        print(Error)
        return False

#Create database if not exist
def create_database(cursor, DB):
    """Function for creating a database"""
    try:
        print(f"Creating database {DB}: ", end="")
        send_query(cursor, f"drop database if exists {DB};")
        send_query(cursor, f"create database {DB} default character set 'utf8mb4';")
        send_query(cursor, f"use {DB};")
        print("done.")
        return True
    except Error:
        print(f"Failed to create database, error: {Error}")
        return False

def create_t_floors(cursor):
    """Function for creating table Floors"""
    create_floors = '''
    create table Floors (
    spaceID int not null auto_increment,
    floorNum int not null,
    parkedRegNum varchar(30) default null,
    primary key (spaceID)
    );
    '''
    print("Creating table Floors: ", end="")
    send_query(cursor, create_floors)
    print("done.")
    return True

def insert_floor_spaces(cursor, floor_number, park_space_num):
    """Function for adding new parking spaces into table Floors 
       (function needs what floor these spaces are meant for and how many spaces to add)"""
    insert_space = f'''
    insert into Floors (floorNum) values ({floor_number});
    '''
    for i in range(1, park_space_num):
        print(f"Creating floor {floor_number} parking space {i}: ", end="")
        send_query(cursor, insert_space)
        print("done.")
    return True

def create_t_users(cursor):
    """Function for creating table Users"""
    create_users = '''
    create table Users (
    userID int not null auto_increment,
    name varchar(30) not null,
    password varchar(50) not null,
    email varchar(50) not null,
    createdDate datetime not null,
    primary key (userID)
    );
    '''
    print("Creating table Users: ", end="")
    send_query(cursor, create_users)
    print("done.")
    return True

def insert_user(cursor, name, passw, email):
    """Function for adding a new user into table Users"""
    date = datetime.today().strftime('%y-%m-%d %H:%M:%S')
    create_user = f'''
    insert into Users (name, password, email, createdDate)
    values ("{name}", "{passw}", "{email}", "{date}");
    '''
    print(f"Creating user {name}: ", end="")
    send_query(cursor, create_user)
    print("done.")
    return True

def create_t_bookings(cursor):
    """Function for creating table Bookings"""
    create_booking = '''
    create table Bookings (
    bookingID int not null auto_increment,
    regNum varchar(30) not null,
    spaceID int not null,
    userID int not null,
    startTime datetime not null,
    primary key (bookingID),
    foreign key (spaceID) references Floors(spaceID),
    foreign key (userID) references Users(userID)
    );
    '''
    print("Creating table Bookings: ", end="")
    send_query(cursor, create_booking)
    print("done.")
    return True

def create_t_logs(cursor):
    """Function for creating table Logs"""
    create_logs = '''
    create table Logs (
    logID int not null auto_increment,
    userID int not null,
    regNum varchar(30) not null,
    startTime datetime not null,
    endTime datetime not null,
    totalTime varchar(30) not null,
    primary key (logID),
    foreign key (userID) references Users(userID)
    );
    '''
    print("Creating table Logs: ", end="")
    send_query(cursor, create_logs)
    print("done.")
    return True

def create_booking_procedure(cursor):
    """Procedure for booking a space with your car and account"""
    create_procedure = '''
    create procedure insert_booking (IN rNum char(30), IN sID int, IN uID int, IN fNum int)
    begin
        if rNum not in (select regNum from Bookings) and sID not in (select spaceID from Bookings) then
            if sID in (select spaceID from Floors) and fNum in (select floorNum from Floors) then
                insert into Bookings (regNum, spaceID, userID, startTime) values (rNum, sID, uID, NOW());
            end if;
        end if;
    end;
    '''
    print("Creating procedure insert_booking: ", end="")
    send_query(cursor, create_procedure)
    print("done.")
    return True

def create_floor_trigger(cursor):
    """Trigger for Floors table when someone parks on a space but it is not booked for that car"""
    create_trigger = '''
    create  trigger parkedRegNumUpdate before update on floors
    for each row
    begin
        if new.parkedRegNum not in (select regNum from Bookings where spaceID = new.spaceID) then
            set new.parkedRegNum = null;
        end if;
    end;
    '''
    print("Creating trigger parkedRegNumUpdate: ", end="")
    send_query(cursor, create_trigger)
    print("done.")
    return True

def create_drive_out_procedure(cursor):
    """Procedure for simulation when driving out from park house building"""
    create_procedure = '''
    create procedure drive_out (IN rNum char(30))
    begin
        declare uID int;
        declare sTime datetime;
        declare eTime datetime;
        if exists (select * from Floors where parkedRegNum = rNum) then
            update Floors set parkedRegNum = null where parkedRegNum = rNum;
        end if;
        if exists (select * from Bookings where regnum = rNum) then
            set uID = (select userID from Bookings where regNum = rNum);
            set sTime = (select startTime from Bookings where regNum = rNum);
            set eTime = (select NOW());
            insert into Logs (userID, regNum, startTime, endTime, totalTime)
            values (uID, rNum, sTime, eTime, TIMEDIFF(eTime, sTime));
            delete from Bookings where regNum = rNum;
        end if;
    end;
    '''
    print("Creating procedure drive_out: ", end="")
    send_query(cursor, create_procedure)
    print("done.")
    return True

def create_account_removal_procedure(cursor):
    """Procedure for the removal of an account"""
    create_procedure = '''
    create procedure account_removal (IN uID int)
    begin
        if exists (select * from Bookings where userID = uID) then
            if exists (select * from Floors where parkedRegNum = (select regNum from Bookings where userID = uID)) then
                update Floors set parkedRegNum = null where spaceID = (select spaceID from Bookings where userID = uID);
            end if;
            delete from Bookings where userID = uID;
        end if;
        if exists (select * from Logs where userID = uID) then
            delete from Logs where userID = uID;
        end if;
        delete from Users where userID = uID;
    end;
    '''
    print("Creating procedure account_removal: ", end="")
    send_query(cursor, create_procedure)
    print("done.")
    return True

def initialize_DB(cursor):
    """Function for initializing the database and all tables/triggers/procedures needed"""
    send_query(cursor, "drop table if exists Bookings;")
    send_query(cursor, "drop table if exists Logs;")
    send_query(cursor, "drop table if exists Floors;")
    send_query(cursor, "drop table if exists Users;")
    send_query(cursor, "drop procedure if exists insert_booking;")
    send_query(cursor, "drop trigger if exists parkedRegNumUpdate;")
    send_query(cursor, "drop procedure if exists drive_out;")
    send_query(cursor, "drop procedure if exists account_removal;")
    create_t_floors(cursor)
    for i in range(1, 4):
        insert_floor_spaces(cursor, i, 6)
    create_t_users(cursor)
    create_t_bookings(cursor)
    create_t_logs(cursor)
    create_booking_procedure(cursor)
    create_floor_trigger(cursor)
    create_drive_out_procedure(cursor)
    create_account_removal_procedure(cursor)
    return True

def main():
    """Main function for this application"""
    #Connect to server
    try:
        session = mysql.connector.connect(
            host = "127.0.0.1",
            user = "root",
            password = "admin",
            database = "project"
        )
        cursor = session.cursor()
    except Error:
        print(Error)
        session = mysql.connector.connect(
            host = "127.0.0.1",
            user = "root",
            password = "admin"
        )
        DB_NAME = "project"
        cursor = session.cursor()
        create_database(cursor, DB_NAME)

    #Uncomment to reset database
    #initialize_DB(cursor)

    #signed_in = [name, password, userID]
    signed_in = ["", "", 0]
    intro = True
    #Create an account or sign in to an account
    while intro:
        choice = main_intro()
        if choice == "1": #sign in
            name = input("Write username: ")
            passw = input("Write password: ")
            send_query(cursor, "select name, password from Users;")
            result = cursor.fetchall()
            for x in result:
                if name == x[0] and passw == x[1]:
                    intro = False
                    signed_in[0] = name
                    signed_in[1] = passw
                    break
            if intro is True:
                print("Wrong username or password.")

        elif choice == "2": #create account
            name = input("Write username: ")
            passw = input("Write password: ")
            mail = input("Write email: ")
            #Check if user already exists
            send_query(cursor, "select name, email from Users;")
            result = cursor.fetchall()
            account_exist = False
            for x in result:
                if name == x[0] or mail.lower() == x[1].lower():
                    account_exist = True
                    if name == x[0]:
                        print("Name already exists.")
                    else:
                        print("Email already exists.")
                    break
            #Account does not exist yet -> creating account
            if account_exist is False:
                insert_user(cursor, name, passw, mail)
                session.commit()
                signed_in[0] = name
                signed_in[1] = passw
                intro = False

        elif choice == "3": #car simulation
            regNum = input("Car register number: ")
            choice = input("Drive into building (1) or out (2): ")
            if choice == "1":
                spaceID = input("\nParking space ID to park in: ")
                send_query(cursor, f"update Floors set parkedRegNum = '{regNum}' where spaceID = {spaceID};")
                session.commit()
                send_query(cursor, f"select parkedRegNum from Floors where parkedRegNum = '{regNum}';")
                if cursor.fetchall() == []:
                    print("\nParked on wrong space and got removed!")
                else:
                    print("\nParked on space that was also booked.")
            
            elif choice == "2":
                send_query(cursor, f"select * from Floors where parkedRegNum = '{regNum}';")
                if cursor.fetchall() != []:
                    send_query(cursor, f"call drive_out('{regNum}');")
                    session.commit()
                    print("\nReservation unbooked because you drove out.")
                else:
                    print("\nNothing unbooked because you were not parked.")
            else:
                print("Wrong input!")

        elif choice == "4": #exit
            intro = False
            session.disconnect()
            sys.exit(0)
        else:
            print("Wrong input!")
    
    #Main menu for users to interact with park house app
    menu = True
    send_query(cursor, f"select userID from Users where name = '{signed_in[0]}' and password = '{signed_in[1]}';")
    result = cursor.fetchall()
    signed_in[2] = result[0][0]
    while menu:
        choice = main_menu_user()
        if choice == "1": #See free park spaces
            send_query(cursor, "select floorNum, count(floorNum) from Floors where spaceID "
                                "not in (select spaceID from Bookings) group by floorNum;")
            result = cursor.fetchall()
            for x in result:
                print(f"\nFloor {x[0]} -> {x[1]} free spaces  |  ", end="")
            print("")

        elif choice == "2": #Reserve park space
            regNum = input("Please enter your register number for your car: ")
            floor = input("Which floor do you want to park in that has free park spaces left: ")
            #Check if floor number exists
            send_query(cursor, f"select count(floorNum) from Floors where floorNum = {floor};")
            result = cursor.fetchall()
            if result[0][0] == 0:
                print(f"\nFloor {floor} does not exist!")
            else:
                #Print out available spaceID for that floor
                send_query(cursor, f"select spaceID from Floors where floorNum = {floor} and spaceID "
                                    "not in (select spaceID from Bookings);")
                result = cursor.fetchall()
                print(f"Free parking ID's in floor {floor}: ", end="")
                for x in result:
                    print(f"{x[0]}, ", end="")
                print("")
                spaceID = input("Which parking space ID do you want to reserve: ")
                #Check if spaceID exists in given floor
                send_query(cursor, f"select count(spaceID) from Floors where spaceID = {spaceID} and floorNum = {floor};")
                result = cursor.fetchall()
                if result[0][0] == 0:
                    print(f"\nSpaceID {spaceID} does not exists on floor {floor}!")
                else:
                    userID = signed_in[2]
                    #Call procedure to insert booking
                    send_query(cursor, f"call insert_booking('{regNum}', {spaceID}, {userID}, {floor});")
                    session.commit()
                    #Check if insert was successful
                    send_query(cursor, f"select regNum, spaceID, userID from Bookings where spaceID = {spaceID};")
                    result = cursor.fetchall()
                    #Not successful
                    if result == []:
                        print("-> Car register number was already used to reserve a parking space! <-")
                    #Reserved by another person
                    elif result[0][0] != regNum or result[0][2] != userID:
                        print("-> Parking space is already reserved! <-")
                    #Success
                    else:
                        print("-> Parking space was reserved, you can view your booking in your profile. <-")

        elif choice == "3": #View profile
            send_query(cursor, "select u.name, u.email, u.createdDate, b.regNum, b.spaceID, f.floorNum, l.regNum, l.startTime, l.totalTime from "
                               "Users u left join Bookings b on u.userID = b.userID "
                               "left join Floors f on b.spaceID = f.spaceID "
                               f"left join Logs l on u.userID = l.userID where u.userID = {signed_in[2]} order by l.logID desc;")
            result = cursor.fetchall()
            print(f"Username: {result[0][0]}        Email: {result[0][1]}       Account was created: {result[0][2]}")
            print("\nCurrent reservation:")
            print(f"     Parking ID: {result[0][4]}")
            print(f"     On floor number: {result[0][5]}")
            print(f"     With register number: {result[0][3]}")
            print("\nPrevious parking times:")
            for x in result:
                print(f"     Date: {x[7]}       Register number: {x[6]}     Total park time: {x[8]}")

        elif choice == "4": #Delete reservation
            remove = input("\nAre you sure you want to delete your reservation (y/yes or n/no): ")

            if remove.lower() == "y" or remove.lower() == "yes":
                #Check if user made a reservation
                send_query(cursor, f"select regNum, spaceID from Bookings where userID = '{signed_in[2]}';")
                result = cursor.fetchall()
                if result == []:
                    print("No reservation made!")
                #Check if user is parked on parking space or not
                else:
                    rNum = result[0][0]
                    sID = result[0][1]
                    send_query(cursor, f"select parkedRegNum from Floors where parkedRegNum = '{rNum}' and spaceID = {sID};")
                    result = cursor.fetchall()
                    if result == []:
                        send_query(cursor, f"delete from Bookings where userID = {signed_in[2]};")
                        session.commit()
                    else:
                        print("Can't remove reservation while parking space is used!")

            elif remove.lower() == "n" or remove.lower() == "no":
                print("Canceling deletion of your reservation!")
            else:
                print("Bad input, canceling deletion of reservation!")

        elif choice == "5": #Logout
            menu = False
            signed_in = ["", "", 0]
            session.disconnect()
            main()

        elif choice == "6": #Delete account
            remove = input("\nAre you sure you want to delete your account (y/yes or n/no): ")
            if remove.lower() == "y" or remove.lower() == "yes":
                send_query(cursor, f"call account_removal({signed_in[2]})")
                session.commit()
                menu = False
                signed_in = ["", "", 0]
                session.disconnect()
                main()
            elif remove.lower() == "n" or remove.lower() == "no":
                print("Canceling removal of your account!")
            else:
                print("Bad input, canceling removal of account!")

        else:
            print("Wrong input!")

    sys.exit(0)

#-------------------------------------------------------------------------------
#Functions for main app
def main_intro():
    """Function to print out intro for application"""
    date = datetime.today().strftime('%y-%m-%d %H-%M-%S')
    print("")
    print("--------------------------------------------")
    print(f"| Park APP (PAPP)   Time: {date}|")
    print("--------------------------------------------")
    print("")
    print("Sign in: 1")
    print("Create account: 2")
    print("Car mode (for simulation): 3")
    print("Exit: 4")
    inp = input("-> ")
    return inp

def main_menu_user():
    """Function to print out menu for application"""
    date = datetime.today().strftime('%y-%m-%d %H-%M-%S')
    print("")
    print("--------------------------------------------")
    print(f"| Park APP (PAPP)   Time: {date}|")
    print("--------------------------------------------")
    print("")
    print("See free park spaces: 1")
    print("Reserve a park space: 2")
    print("View profile: 3")
    print("Delete a reservation for parking space: 4")
    print("Logout: 5")
    print("Remove account: 6")
    inp = input("-> ")
    return inp

if __name__ == "__main__":
    main()
