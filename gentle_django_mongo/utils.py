from django.conf import settings
from pymongo import MongoClient


def mongo_db():

    return MongoClient(
        getattr(settings, "MONGODB_URL", "mongodb://localhost:27017")
    )[getattr(settings, "MONGODB_DATABASE", "archive")]

