# -*- coding: utf-8 -*- 
# Moritz Basel - Interne_Entities.py
# Version 0.2.0
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


import Interne_helpers
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
                                cascade = "delete, delete-orphan", foreign_keys = "User_Appointment_Rel.user_id")

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
    targetLocation = Column(String(100))
    startTime = Column(DateTime)
    repeatTime = Column(String(15))
    users = relationship("User_Appointment_Rel", back_populates="appointment",
                            cascade= "delete, delete-orphan", foreign_keys = "User_Appointment_Rel.appointment_id")

    distance = Column(Integer)
    
    status = Column(Integer)

    def getAsJSON(self):
        timeString = datetime.fromtimestamp(self.startTime).strftime('%c')
        return {'id' : self.id, 'startLocation' : self.startLocation, 
                'startTime' : self.startTime, 'repeatTime' : self.repeatTime, 
                'status' : Interne_helpers.getAppointmentStatusString(self.status),
                'distance' : self.distance,
                'targetLocation' : self.targetLocation,
                'startTimeString' : timeString}                                 #distance in kilometers


class User_Appointment_Rel(SQLBase):
    " drivingLevel 0 means no car, 1 means Will definitely drive, 2 means may drive"
    __tablename__ = 'user_takesPart_appointment'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)


    #who is my driver? - might be myself
    designatedDriverID = Column(Integer, ForeignKey('users.id'))

    appointment_id = Column(Integer, ForeignKey('appointments.id'), primary_key = True)
    drivingLevel = Column(Integer)
    actualDrivingParticipation = Column(Boolean)
    maximumPassengers = Column(Integer)     #Optional field for drivingLevel not 0

    appointment = relationship("Appointment", back_populates = "users", foreign_keys=[appointment_id])
    user = relationship("User", back_populates = "appointments", foreign_keys = [user_id])

    designatedDriverUser = relationship("User", foreign_keys = [designatedDriverID])


