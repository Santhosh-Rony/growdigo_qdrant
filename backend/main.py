from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib
import json

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Growdigo AI Backend", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://growdigo.netlify.app",
        "http://localhost:3000",
        "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Qdrant client initialization
QDRANT_URL = os.getenv("QDRANT_URL", "https://34d79981-cd9b-4e4b-903f-453cf103e9b1.us-west-1-0.aws.cloud.qdrant.io:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "chat_conversations"

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# Pydantic models
class Message(BaseModel):
    id: int
    role: str
    content: str
    timestamp: str

class Conversation(BaseModel):
    id: int
    title: Optional[str] = None
    messages: List[Message]
    user_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ConversationUpdate(BaseModel):
    messages: List[Message]

# Utility functions
def generate_vector(data: Dict[str, Any]) -> List[float]:
    """Generate a simple vector from conversation data"""
    text = json.dumps(data, sort_keys=True)
    vector = [0.0] * 1536
    for i, char in enumerate(text[:1536]):
        vector[i] = ord(char) / 255.0
    return vector

def generate_title(first_message: str) -> str:
    """Generate conversation title from first message"""
    words = first_message.split()[:6]
    return " ".join(words) + ("..." if len(first_message.split()) > 6 else "")

# Initialize collection
@app.on_event("startup")
async def startup_event():
    try:
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if COLLECTION_NAME not in collection_names:
            # Create collection
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
            print(f"Created collection: {COLLECTION_NAME}")
        else:
            print(f"Collection {COLLECTION_NAME} already exists")
    except Exception as e:
        print(f"Error initializing collection: {e}")

# API endpoints
@app.get("/")
async def root():
    return {
        "message": "Growdigo AI Backend", 
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    try:
        # Test Qdrant connection
        collections = client.get_collections()
        return {
            "status": "healthy",
            "qdrant_connected": True,
            "collections": len(collections.collections),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "qdrant_connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/conversations")
async def save_conversation(conversation: Conversation):
    """Save a new conversation"""
    try:
        # Generate title if not provided
        if not conversation.title and conversation.messages:
            first_message = conversation.messages[0].content
            conversation.title = generate_title(first_message)
        
        # Set timestamps
        now = datetime.utcnow().isoformat()
        conversation.created_at = conversation.created_at or now
        conversation.updated_at = now
        
        # Generate vector
        vector = generate_vector({
            "title": conversation.title,
            "messages": [msg.dict() for msg in conversation.messages],
            "user_id": conversation.user_id
        })
        
        # Create point
        point = PointStruct(
            id=conversation.id,
            vector=vector,
            payload={
                "id": conversation.id,
                "title": conversation.title,
                "messages": [msg.dict() for msg in conversation.messages],
                "user_id": conversation.user_id,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at
            }
        )
        
        # Upload to Qdrant
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[point]
        )
        
        return {
            "id": conversation.id,
            "title": conversation.title,
            "messages": [msg.dict() for msg in conversation.messages],
            "user_id": conversation.user_id,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving conversation: {str(e)}")

@app.get("/conversations/{user_id}")
async def get_conversations(user_id: str, limit: int = 50):
    """Get all conversations for a user"""
    try:
        # Get all points from collection
        points = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )[0]
        
        # Filter by user_id
        user_conversations = [
            point.payload for point in points 
            if point.payload.get("user_id") == user_id
        ]
        
        # Sort by updated_at
        user_conversations.sort(
            key=lambda x: x.get("updated_at", ""), 
            reverse=True
        )
        
        return user_conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversations: {str(e)}")

@app.get("/conversations/{user_id}/{conversation_id}")
async def get_conversation(user_id: str, conversation_id: int):
    """Get a specific conversation"""
    try:
        point = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[conversation_id],
            with_payload=True
        )
        
        if not point or point[0].payload.get("user_id") != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return point[0].payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversation: {str(e)}")

@app.put("/conversations/{user_id}/{conversation_id}")
async def update_conversation(user_id: str, conversation_id: int, update: ConversationUpdate):
    """Update an existing conversation"""
    try:
        # Get existing conversation
        point = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[conversation_id],
            with_payload=True
        )
        
        if not point or point[0].payload.get("user_id") != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        existing = point[0].payload
        
        # Update conversation
        updated_conversation = {
            **existing,
            "messages": [msg.dict() for msg in update.messages],
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Generate new vector
        vector = generate_vector(updated_conversation)
        
        # Update point
        new_point = PointStruct(
            id=conversation_id,
            vector=vector,
            payload=updated_conversation
        )
        
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[new_point]
        )
        
        return updated_conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating conversation: {str(e)}")

@app.delete("/conversations/{user_id}/{conversation_id}")
async def delete_conversation(user_id: str, conversation_id: int):
    """Delete a conversation"""
    try:
        # Check if conversation exists and belongs to user
        point = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[conversation_id],
            with_payload=True
        )
        
        if not point or point[0].payload.get("user_id") != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Delete point
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=[conversation_id]
        )
        
        return {"message": "Conversation deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 