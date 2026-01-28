from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get MongoDB URI
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

print("DEBUG: MONGODB_URI =", MONGODB_URI)

# Connect to MongoDB (SINGLE CLIENT)
client = MongoClient(MONGODB_URI)

# Database
db = client["feedback_ai_db"]
print("🔥 USING DATABASE:", db.name)

# Collections
feedbacks = db["feedbacks"]               # user submitted feedback
batches = db["batches"]                   # batch tracking
analysis_results = db["analysis_results"] # AI analysis output
global_issues = db["global_issues"]       # merged issues
