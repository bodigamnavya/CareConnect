from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

print("MongoDB connection successful")

print("Databases:")
print(client.list_database_names())

db = client["careconnect"]

print("\nCollections in careconnect:")
print(db.list_collection_names())

print("\nMedical profiles count:")
print(db["medical_profiles"].count_documents({}))

print("\nUsers count:")
print(db["users"].count_documents({}))