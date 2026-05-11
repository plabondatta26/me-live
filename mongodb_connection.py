# # mongodb://localhost:27017
# from pymongo import MongoClient

# class MeLiveMongoDB:
#   melive_mongo_db = None

#   def __new__(cls):
#     if cls.melive_mongo_db is None:
#         # print('Creating the melive_mongo_db object')
#         client = MongoClient('mongodb://localhost:27017')
#         cls.melive_mongo_db = client['melive_db']
#     return cls.melive_mongo_db
