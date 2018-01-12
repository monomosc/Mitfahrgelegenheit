# Moritz Basel - Interne_Entities.py
# Version 0.1.0
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

#CLASS: USER
#///////////////////////////////////////////////////////////////////////////////////////////////////

SQLBase = declarative_base()

class User(SQLBase):
    "The User class represents the User Object as well as the ORM in the Database"
    # Fields:
    # id                     //The MySQL autoincreasing ID
    #username               //Username
    # password               //Hashed Password
    # email                  //Email Address
    # phoneNumber            //Phone Number
    # globalAdminStatus      //Global Admin Status, currently 0 or 1
    __tablename__ = 'users'
    id = Column(Integer, primary_key = True)
    username = Column(String(50), unique = True)
    password = Column(String(255))
    email = Column(String(100))
    phoneNumber = Column(String(40))
    globalAdminStatus = Column(Integer)
    appointments = relationship("User_Appointment_Rel", back_populates="user",
                                cascade = "delete, delete-orphan")

    def getAsJSON(self):
        "Returns a JSON representation of a User"
        return { 'id' : self.id, 'username' : self.username, 'email' : self.email, 'phoneNumber' : self.phoneNumber,
             'globalAdminStatus' : self.globalAdminStatus}


#CLASS: APPOINTMENT
#///////////////////////////////////////////////////////////////////////////////////////////////////


class Appointment(SQLBase):
    "Object to Entity Appointment in Database"


    __tablename__='appointments'
    id = Column (Integer, primary_key = True)
    startLocation = Column(String(40))
    startTime = Column(DateTime)
    repeatTime = Column(String(15))
    users = relationship("User_Appointment_Rel", back_populates="appointment",
                            cascade= "delete, delete-orphan")
    retired = Column(Boolean)
    distance = Column(Integer)
    def getAsJSON(self):
        return {'id' : self.id, 'startLocation' : self.startLocation, 
                'startTime' : self.startTime, 'repeatTime' : self.repeatTime, 
                'retired' : ('true' if self.retired is True else 'false'),
                'distance' : self.distance}                                 #distance in kilometers


class User_Appointment_Rel(SQLBase):
    " drivingLevel 0 means no car, 1 means Will definitely drive, 2 means may drive"
    __tablename__ = 'user_takesPart_appointment'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    appointment_id = Column(Integer, ForeignKey('appointments.id'), primary_key = True)
    drivingLevel = Column(Integer)
    actualDrivingParticipation = Column(Boolean)
    maximumPassengers = Column(Integer)     #Optional field for drivingLevel not 0
    appointment = relationship("Appointment", back_populates = "users")
    user = relationship("User", back_populates = "appointments")



