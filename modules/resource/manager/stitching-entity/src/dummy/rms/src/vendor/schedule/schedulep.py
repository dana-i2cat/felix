from datetime import datetime, timedelta

from amsoil.core import pluginmanager as pm
from amsoil.core import serviceinterface
from amsoil.core.exception import CoreException
from amsoil.config import expand_amsoil_path

import amsoil.core.log
logger=amsoil.core.log.getLogger('schedule')

import scheduleexceptions as sex
from attributedict import AttributeDict

class Schedule(object):
    """
    
    Please see the wiki for more information: https://github.com/motine/AMsoil/wiki/Schedule
    Please create one instance of this class for each schedule_subject.
    
    NOTE:
    This class will never deliver a Database record to the outside.
    It will copy the contents of the database record, so the plugin user can not accidentally change the database.
    For problem statement see https://github.com/motine/AMsoil/wiki/Persistence#expunge
    """
    
    @serviceinterface
    def __init__(self, schedule_subject, default_duration):
        """
        There is one schedule for each subject (resource classification/type). 
        {schedule_subject} This paramenter limits the scope of this class to the given subject (see above).
        {default_duration} (number in seconds) If no {end_time} is given in subsequent methods, this value will be added to the {start_time} to get the end of the reservation.
        """
        self.schedule_subject = schedule_subject
        self.default_duration = default_duration

    @serviceinterface
    def reserve(self, resource_id, resource_spec=None, slice_id=None, user_id=None, start_time=None, end_time=None):
        """
        Creates a reservation.
        Raises an ScheduleOverbookingError if there is already an entry for the given subject, resource_id and time (see constraints above).
        Returns the reservation id.

        Please see class description for info on parameters.
        """
        if start_time == None:
            start_time = datetime.utcnow()
        if end_time == None:
            end_time =  start_time + timedelta(0, self.default_duration)

        if len(self.find(resource_id=resource_id, start_time=start_time, end_time=end_time)) > 0:
            raise sex.ScheduleOverbookingError(self.schedule_subject, resource_id, start_time, end_time)
        
        new_record = ReservationRecord(
            schedule_subject=self.schedule_subject, resource_id=resource_id,
            resource_spec=resource_spec,
            start_time=start_time, end_time=end_time,
            slice_id=slice_id, user_id=user_id)
        db_session.add(new_record)
        db_session.commit()
        db_session.expunge_all()
        return self._convert_record_to_value_object(new_record)
    
    @serviceinterface
    def find(self, reservation_id=None, resource_id=None, slice_id=None, user_id=None, start_time=None, end_time=None):
        """
        Returns a list of reservation value objects (see class description).
        If all parameters a None, all reservations for this schedule_subject will be returned.
        If given parameters are not-None the result will be filtered by the respective field.
        If multiple params are given the result will be reduced (conditions will be AND-ed).
        If the times are given, all records which touch the given period will be returned.
        If {start_time} is given, but {end_time} is omitted, all records which span start_time will be returned.
        
        Limitations:
        - This method can not be used to filter records with NULL fields. E.g. it is not possible to filter all records to the ones which have set user_id to NULL.
        """
        q = db_session.query(ReservationRecord)
        q = q.filter_by(schedule_subject=self.schedule_subject)
        if not reservation_id is None:
            q = q.filter_by(reservation_id=reservation_id)
        if not resource_id is None:
            q = q.filter_by(resource_id=resource_id)
        if not slice_id is None:
            q = q.filter_by(slice_id=slice_id)
        if not user_id is None:
            q = q.filter_by(user_id=user_id)

        if (not start_time is None) and (end_time is None):
            end_time = start_time
        if (not start_time is None) and (not end_time is None):
            q = q.filter(not_(or_(ReservationRecord.end_time < start_time, ReservationRecord.start_time > end_time)))

        records = q.all()
        result = [self._convert_record_to_value_object(r) for r in records]
        db_session.expunge_all()
        return result

    def update(self, reservation_id, resource_id=None, resource_spec=None, slice_id=None, user_id=None, start_time=None, end_time=None):
        """
        Finds the reservation by its {reservation_id} and updates the fields by the given parameters.
        If a parameter is None, the field will be left unchanged.
        Raises ScheduleNoSuchReservationError if there is no such reservation.
        Returns the changed reservation as value object (see class description).
        
        Limitation:
        - It is not possible make a field None/NULL with this method, because the None parameter will be interpreted as 'please leave unchanged'.
        """
        reservation = self._find_reservation(reservation_id)
        # this could be done shorter with setattr, but I rather have it expicit
        if not resource_id is None:
            reservation.reservation_id = reservation_id
        if not resource_spec is None:
            reservation.resource_spec = resource_spec
        if not slice_id is None:
            reservation.slice_id = slice_id
        if not user_id is None:
            reservation.user_id = user_id
        if not start_time is None:
            reservation.start_time = start_time
        if not end_time is None:
            reservation.end_time = end_time
        db_session.commit()
        db_session.expunge_all()
        return self._convert_record_to_value_object(reservation)

    def cancel(self, reservation_id):
        """
        Removes the reservation with the given id.
        Raises ScheduleNoSuchReservationError if there is no such reservation.
        Returns the values of the removed object as value object (see class description).
        """
        reservation = self._find_reservation(reservation_id)
        result = self._convert_record_to_value_object(reservation)
        db_session.delete(reservation)
        db_session.commit()
        db_session.expunge_all()
        return result

    def _find_reservation(self, reservation_id):
        try:
            return db_session.query(ReservationRecord).filter_by(schedule_subject=self.schedule_subject).filter_by(reservation_id=reservation_id).one()
        except MultipleResultsFound, e: # this should never happen, because reservation_id is the primary key in the database
            raise RuntimeError("There are multiple primary keys %d" % (reservation_id,))
        except NoResultFound, e:
            raise sex.ScheduleNoSuchReservationError(reservation_id)

    def _convert_record_to_value_object(self, db_record):
        """Converts a given database record to a value object (see class description)."""
        result_dict = {c.name: getattr(db_record, c.name) for c in db_record.__table__.columns}
        del result_dict['schedule_subject']
        return AttributeDict(result_dict)

# ----------------------------------------------------
# ------------------ database stuff ------------------
# ----------------------------------------------------
from sqlalchemy import Column, Integer, String, DateTime, PickleType, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import exists
from sqlalchemy.sql.expression import and_, or_, not_

from amsoil.config import expand_amsoil_path

# initialize sqlalchemy
DB_PATH = expand_amsoil_path(pm.getService('config').get('schedule.dbpath'))
DB_ENGINE = create_engine("sqlite:///%s" % (DB_PATH,)) # please see the wiki for more info
DB_SESSION_FACTORY = sessionmaker(autoflush=True, bind=DB_ENGINE, expire_on_commit=False)
db_session = scoped_session(DB_SESSION_FACTORY)
DB_Base = declarative_base() # get the base class for the ORM, which includes the metadata object (collection of table descriptions)

class ReservationRecord(DB_Base):
    """Encapsulates a record in the database."""
    __tablename__ = 'reservations'
    
    reservation_id = Column(Integer, primary_key=True)
    
    schedule_subject = Column(String(255))
    resource_id = Column(String(255))
    
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    slice_id = Column(String(255))
    user_id = Column(String(255))
    
    resource_spec = Column(PickleType())

DB_Base.metadata.create_all(DB_ENGINE) # create the tables if they are not there yet