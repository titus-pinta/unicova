import pymongo
from bson.objectid import ObjectId
from celery import Celery
from celery import Task

import datetime
import hashlib
import re

email_re = re.compile('^[a-zA-Z0-9\.]*@[a-zA-Z]*\.[a-z]*$')
pwd_re = re.compile('^[a-zA-Z0-9]*$')
name_re = re.compile('^[a-zA-Z]*$')
licence_re = re.compile('^[A-Z]{2}[0-9]{2}[A-Z]{3}$')
location_re = re.compile('^[a-zA-Z0-9\ ]*$')
id_re = re.compile('^[a-zA-Z0-9]*$')

scheduler = Celery('mongo', backend='rpc://',
                   broker='pyamqp://guest@{}//'.format('127.0.0.1'))

class MongoTask(Task):

    def __init__(self, ip='127.0.0.1', port=27017, user='Titus',
                 pwd='unicova'):
        self._connection = pymongo.MongoClient(ip, port)

        self._db = self._connection['unicova']
        self._db.authenticate(user, pwd)

        self._client = self._db['client']
        self._parking = self._db['parking']
        self._info = self._db['info']

    def __del__(self):
        self._connection.close()

@scheduler.task(base=MongoTask)
def add_user(email, pwd, first_name, last_name, licence_plate):
    if not bool(email_re.match(email)):
        return {'error': 'Wrong format for email: {}'.format(email)}
    if not bool(pwd_re.match(pwd)):
        return {'error': 'Wrong format for password: {}'.format(pwd)}
    if not bool(name_re.match(first_name)):
        return {'error': 'Wrong format for first name: {}'.format(first_name)}
    if not bool(name_re.match(last_name)):
        return {'error': 'Wrong format for last name: {}'.format(last_name)}
    if not bool(licence_re.match(licence_plate)):
        return {'error': 'Wrong format for licence plate: {}'.format(
            licence_plate)}

    data = {'email': email}
    count_clients = add_user._client.count_documents(data)
    if count_clients != 0:
        return {'error': 'Email already used'}

    salt = hashlib.sha512(str(datetime.datetime.now()).encode(
        'ascii')).hexdigest()
    pwd = hashlib.sha512((pwd + salt).encode('ascii')).hexdigest()

    data = {'email': email, 'pwd': pwd, 'salt': salt, 'first_name': first_name,
            'last_name': last_name, 'licence_plate': licence_plate}
    return str(add_user._client.insert_one(data).inserted_id)

@scheduler.task(base=MongoTask)
def delete_user(_id):
    if not bool(id_re.match(_id)):
        return {'error': 'Invalid id: {}'.format(_id)}
    data = {'_id': ObjectId(_id)}
    count_clients = delete_user._client.count_documents(data)
    if count_clients != 1:
        return {'error': 'No user with this id'}
    delete_user._client.delete_one(data)

    return True

@scheduler.task(base=MongoTask)
def add_admin(email, pwd, first_name, last_name):
    if not bool(email_re.match(email)):
        return {'error': 'Wrong format for email: {}'.format(email)}
    if not bool(pwd_re.match(pwd)):
        return {'error': 'Wrong format for password: {}'.format(pwd)}
    if not bool(name_re.match(first_name)):
        return {'error': 'Wrong format for first name: {}'.format(first_name)}
    if not bool(name_re.match(last_name)):
        return {'error': 'Wrong format for last name: {}'.format(last_name)}

    data = {'email': email}
    count_clients = add_admin._client.count_documents(data)
    if count_clients != 0:
        return {'error': 'Email already used'}

    salt = hashlib.sha512(str(datetime.datetime.now()).encode(
        'ascii')).hexdigest()
    pwd = hashlib.sha512((pwd + salt).encode('ascii')).hexdigest()

    data = {'email': email, 'pwd': pwd, 'salt': salt, 'first_name': first_name,
            'last_name': last_name, 'admin': True}
    return str(add_user._client.insert_one(data).inserted_id)

@scheduler.task(base=MongoTask)
def delete_admin(_id):
    if not bool(id_re.match(_id)):
        return {'error': 'Invalid id: {}'.format(_id)}
    data = {'_id': ObjectId(_id)}
    count_admins = delete_admin._client.count_documents(data)
    if count_admins != 1:
        return {'error': 'No admin with this id'}
    delete_admin._client.delete_one(data)

    return True

@scheduler.task(base=MongoTask)
def add_parking(location, num_spots):
    if not bool(location_re.match(location)):
        return {'error': 'Parking already exists'}
    if not isinstance(num_spots, int):
        return {'error': ('Number of parking spots must be an' +
                          ' integer: {}').format(num_spots)}

    data = {'location': location}
    count_parkings = add_parking._parking.count_documents(data)
    if count_parkings != 0:
        return {'error': 'Parking already exists'}

    data = {'location': location, 'num_spots': num_spots,
            'available_spots': num_spots}
    return str(add_parking._parking.insert_one(data).inserted_id)

@scheduler.task(base=MongoTask)
def delete_parking(_id):
    if not bool(id_re.match(_id)):
        return {'error': 'Invalid id: {}'.format(_id)}
    data = {'_id': ObjectId(_id)}
    count_parkings = delete_parking._client.count_documents(data)
    if count_parkings != 1:
        return {'error': 'No parking with this id'}
    delete_parking._parking.delete_one(data)

    return True

@scheduler.task(base=MongoTask)
def authentificate_user(email, pwd):
    if not bool(email_re.match(email)):
        return {'error': 'Wrong format for email: {}'.format(email)}
    if not bool(pwd_re.match(pwd)):
        return {'error': 'Wrong format for password: {}'.format(pwd)}

    data = {'email': email, 'admin': {'$exists': False}}
    cursor  = authentificate_user._client.find(data)
    entries = list(cursor)

    if len(entries) != 1:
        return {'error': 'Email and password do not match'}

    salt = entries[0]['salt']
    pwd = hashlib.sha512((pwd + salt).encode('ascii')).hexdigest()

    if pwd != entries[0]['pwd']:
        return {'error': 'Email and password do not match'}

    entries[0].pop('pwd')
    entries[0].pop('salt')
    return repr(entries[0])

@scheduler.task(base=MongoTask)
def authentificate_admin(email, pwd):
    if not bool(email_re.match(email)):
        return {'error': 'Wrong format for email: {}'.format(email)}
    if not bool(pwd_re.match(pwd)):
        return {'error': 'Wrong format for password: {}'.format(pwd)}

    data = {'email': email, 'pwd': pwd, 'admin': True}
    cursor  = authentificate_admin._client.find(data)
    entries = list(cursor)

    if len(entries) != 1:
        return {'error': 'Email and password do not match'}

    salt = entries[0]['salt']
    pwd = hashlib.sha512((pwd + salt).encode('ascii')).hexdigest()

    if pwd != entries[0]['pwd']:
        return {'error': 'Email and password do not match'}

    entries[0].pop('pwd')
    entries[0].pop('salt')
    return repr(entries[0])

@scheduler.task(base=MongoTask)
def get_parkings():
    return repr(list(get_parkings._parking.find()))

#TODO locking for the database

@scheduler.task(base=MongoTask)
def reserve_parking(user_id, parking_id, _type):
    if not bool(id_re.match(user_id)):
        return {'error': 'Invalid user id: {}'.format(user_id)}
    if not bool(id_re.match(parking_id)):
        return {'error': 'Invalid parking id: {}'.format(parking_id)}

    data = {'_id': ObjectId(user_id), 'parking_id':
            {'$exists': True, '$ne': None}}

    count_clients = reserve_parking._client.count_documents(data)
    if count_clients != 0:
        return {'error': 'Already reserved a parking spot'}

    data = {'_id': ObjectId(parking_id), 'available_spots': {'$gt': 0}}
    count_parkings = reserve_parking._parking.count_documents(data)
    if count_parkings != 1:
        return {'error': 'No available parking spots'}

    times = reserve_parking._info.find_one({'times':
                                {'$exists': True, '$ne': None}})['times']

    if _type not in times.keys():
        return {'error': 'Invalid parking type'}

    data = {'_id': ObjectId(user_id)}
    reserve_parking._client.update_one(data, {'$set':
            {'parking_id': ObjectId(parking_id), 'type': _type}})

    data = {'_id': ObjectId(parking_id)}
    reserve_parking._parking.update_one(data,
                                       {'$inc': {'available_spots': -1}})

    return True, times[_type]

@scheduler.task(base=MongoTask)
def free_parking(user_id, parking_id):
    if not bool(id_re.match(user_id)):
        return {'error': 'Invalid user id: {}'.format(user_id)}
    if not bool(id_re.match(parking_id)):
        return {'error': 'Invalid parking id: {}'.format(parking_id)}

    data_user = {'_id': ObjectId(user_id)}
    count_clients = reserve_parking._client.count_documents(data_user)
    if count_clients != 1:
        return {'error': 'Not a valid user'}

    data_parking = {'_id': ObjectId(parking_id)}
    count_parkings = reserve_parking._parking.count_documents(data_parking)
    if count_parkings != 1:
        return {'error': 'Not a valid parking spot'}

    free_parking._client.update_one(data_user, {'$unset':
            {'parking_id': '', 'type': ''}})

    free_parking._parking.update_one(data_parking,
            {'$inc': {'available_spots': 1}})

    return True

@scheduler.task(base=MongoTask)
def block_spot(_id):
    if not bool(id_re.match(_id)):
        return {'error': 'Invalid id: {}'.format(_id)}
    data = {'_id': ObjectId(_id), 'available_spots': {'$gt': 0}}
    count_parkings = block_spot._parking.count_documents(data)
    if count_parkings != 1:
        return {'error': 'No parcking with this id and ' +
                'available parking spots'}
    block_spot._parking.update_one(data, {'$inc': {'available_spots': -1}})

