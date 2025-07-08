from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import openai
from openai import OpenAI
import aiohttp
import asyncio
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# OpenAI configuration
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class Target(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    title: str
    company: str
    linkedin_url: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: str = "India"
    profile_summary: Optional[str] = None
    recent_activity: Optional[str] = None
    connection_status: str = "not_connected"  # not_connected, pending, connected, messaged
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TargetCreate(BaseModel):
    name: str
    title: str
    company: str
    linkedin_url: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: str = "India"
    profile_summary: Optional[str] = None
    recent_activity: Optional[str] = None

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_id: str
    content: str
    message_type: str = "connection_request"  # connection_request, follow_up, viral_post
    status: str = "draft"  # draft, sent, delivered, replied
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None

class MessageCreate(BaseModel):
    target_id: str
    content: str
    message_type: str = "connection_request"

class MessageGenerateRequest(BaseModel):
    target_id: str
    profile_data: Dict[str, Any]
    message_type: str = "connection_request"
    llm_provider: str = "openai"  # openai or ollama
    model: str = "gpt-4"

class ViralPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_content: str
    author: str
    engagement_score: int
    reactions: int
    comments: int
    shares: int
    linkedin_url: str
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

class GeneratedPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    based_on_viral_posts: List[str]  # List of viral post IDs
    status: str = "draft"  # draft, approved, published
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

class Analytics(BaseModel):
    total_targets: int
    connections_sent: int
    connections_accepted: int
    messages_sent: int
    messages_replied: int
    acceptance_rate: float
    reply_rate: float
    daily_activity: Dict[str, int]

# LLM Service Functions
async def generate_message_openai(profile_data: Dict[str, Any], message_type: str = "connection_request") -> str:
    """Generate personalized message using OpenAI"""
    try:
        system_prompt = f"""You are an expert at writing personalized LinkedIn {message_type} messages.
        
        Guidelines:
        - Keep messages under 250 words
        - Be professional but friendly
        - Reference specific details from their profile
        - Focus on AI/ML expertise and hiring
        - Include a clear call to action
        - Avoid generic phrases
        """
        
        user_prompt = f"""Generate a {message_type} message for this LinkedIn profile:
        
        Name: {profile_data.get('name', 'Unknown')}
        Title: {profile_data.get('title', 'Unknown')}
        Company: {profile_data.get('company', 'Unknown')}
        Profile Summary: {profile_data.get('profile_summary', 'No summary available')}
        Recent Activity: {profile_data.get('recent_activity', 'No recent activity')}
        
        The message should be personalized and mention their AI/ML work and hiring expertise.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

async def generate_message_ollama(profile_data: Dict[str, Any], message_type: str = "connection_request") -> str:
    """Generate personalized message using Ollama"""
    try:
        system_prompt = f"""You are an expert at writing personalized LinkedIn {message_type} messages.
        
        Guidelines:
        - Keep messages under 250 words
        - Be professional but friendly
        - Reference specific details from their profile
        - Focus on AI/ML expertise and hiring
        - Include a clear call to action
        - Avoid generic phrases
        """
        
        user_prompt = f"""Generate a {message_type} message for this LinkedIn profile:
        
        Name: {profile_data.get('name', 'Unknown')}
        Title: {profile_data.get('title', 'Unknown')}
        Company: {profile_data.get('company', 'Unknown')}
        Profile Summary: {profile_data.get('profile_summary', 'No summary available')}
        Recent Activity: {profile_data.get('recent_activity', 'No recent activity')}
        
        The message should be personalized and mention their AI/ML work and hiring expertise.
        """
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": "llama3.1",
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', '').strip()
                else:
                    raise HTTPException(status_code=500, detail="Ollama API error")
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        raise HTTPException(status_code=500, detail=f"Ollama API error: {str(e)}")

async def generate_viral_post_openai(viral_posts: List[Dict[str, Any]]) -> str:
    """Generate viral post using OpenAI"""
    try:
        system_prompt = """You are an expert at creating viral LinkedIn posts about AI/ML.
        
        Guidelines:
        - Keep posts under 1300 characters
        - Start with a compelling hook
        - Include a data point or insight
        - End with a clear call to action
        - Use line breaks for readability
        - Make it algorithm-friendly
        """
        
        viral_content = "\n\n".join([f"Post {i+1}: {post['content'][:200]}..." for i, post in enumerate(viral_posts)])
        
        user_prompt = f"""Based on these viral AI/ML posts, create a new viral post:
        
        {viral_content}
        
        Create an original post that captures the essence of what makes these posts viral while adding your own unique perspective on AI/ML trends.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=400,
            temperature=0.8
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

# API Routes
@api_router.get("/")
async def root():
    return {"message": "LinkedIn AI Automation System"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Target Management
@api_router.post("/targets", response_model=Target)
async def create_target(target: TargetCreate):
    target_dict = target.dict()
    target_obj = Target(**target_dict)
    await db.targets.insert_one(target_obj.dict())
    return target_obj

@api_router.get("/targets", response_model=List[Target])
async def get_targets():
    targets = await db.targets.find().to_list(1000)
    return [Target(**target) for target in targets]

@api_router.get("/targets/{target_id}", response_model=Target)
async def get_target(target_id: str):
    target = await db.targets.find_one({"id": target_id})
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return Target(**target)

@api_router.put("/targets/{target_id}", response_model=Target)
async def update_target(target_id: str, target_update: Dict[str, Any]):
    target_update["updated_at"] = datetime.utcnow()
    result = await db.targets.update_one({"id": target_id}, {"$set": target_update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Target not found")
    
    updated_target = await db.targets.find_one({"id": target_id})
    return Target(**updated_target)

# Message Management
@api_router.post("/messages", response_model=Message)
async def create_message(message: MessageCreate):
    message_dict = message.dict()
    message_obj = Message(**message_dict)
    await db.messages.insert_one(message_obj.dict())
    return message_obj

@api_router.get("/messages", response_model=List[Message])
async def get_messages():
    messages = await db.messages.find().to_list(1000)
    return [Message(**message) for message in messages]

@api_router.post("/messages/generate", response_model=Message)
async def generate_message(request: MessageGenerateRequest):
    """Generate personalized message using AI"""
    try:
        if request.llm_provider == "openai":
            content = await generate_message_openai(request.profile_data, request.message_type)
        else:
            content = await generate_message_ollama(request.profile_data, request.message_type)
        
        message_obj = Message(
            target_id=request.target_id,
            content=content,
            message_type=request.message_type,
            status="draft"
        )
        
        await db.messages.insert_one(message_obj.dict())
        return message_obj
    except Exception as e:
        logger.error(f"Message generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Message generation failed: {str(e)}")

# Viral Posts
@api_router.get("/viral-posts", response_model=List[ViralPost])
async def get_viral_posts():
    posts = await db.viral_posts.find().sort("engagement_score", -1).to_list(10)
    return [ViralPost(**post) for post in posts]

@api_router.post("/viral-posts", response_model=ViralPost)
async def create_viral_post(post: ViralPost):
    await db.viral_posts.insert_one(post.dict())
    return post

@api_router.post("/generate-post", response_model=GeneratedPost)
async def generate_post():
    """Generate viral post based on trending content"""
    try:
        # Get top viral posts
        viral_posts = await db.viral_posts.find().sort("engagement_score", -1).to_list(5)
        
        if not viral_posts:
            raise HTTPException(status_code=404, detail="No viral posts available")
        
        # Generate new post
        content = await generate_viral_post_openai(viral_posts)
        
        post_obj = GeneratedPost(
            content=content,
            based_on_viral_posts=[post["id"] for post in viral_posts],
            status="draft"
        )
        
        await db.generated_posts.insert_one(post_obj.dict())
        return post_obj
    except Exception as e:
        logger.error(f"Post generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Post generation failed: {str(e)}")

@api_router.get("/generated-posts", response_model=List[GeneratedPost])
async def get_generated_posts():
    posts = await db.generated_posts.find().sort("created_at", -1).to_list(10)
    return [GeneratedPost(**post) for post in posts]

# Analytics
@api_router.get("/analytics", response_model=Analytics)
async def get_analytics():
    """Get system analytics"""
    try:
        # Get counts
        total_targets = await db.targets.count_documents({})
        connections_sent = await db.messages.count_documents({"message_type": "connection_request", "status": "sent"})
        connections_accepted = await db.targets.count_documents({"connection_status": "connected"})
        messages_sent = await db.messages.count_documents({"status": "sent"})
        messages_replied = await db.messages.count_documents({"status": "replied"})
        
        # Calculate rates
        acceptance_rate = (connections_accepted / max(connections_sent, 1)) * 100
        reply_rate = (messages_replied / max(messages_sent, 1)) * 100
        
        # Get daily activity (last 7 days)
        daily_activity = {}
        for i in range(7):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            count = await db.messages.count_documents({
                "created_at": {
                    "$gte": datetime.utcnow() - timedelta(days=i+1),
                    "$lt": datetime.utcnow() - timedelta(days=i)
                }
            })
            daily_activity[date] = count
        
        return Analytics(
            total_targets=total_targets,
            connections_sent=connections_sent,
            connections_accepted=connections_accepted,
            messages_sent=messages_sent,
            messages_replied=messages_replied,
            acceptance_rate=round(acceptance_rate, 2),
            reply_rate=round(reply_rate, 2),
            daily_activity=daily_activity
        )
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

# Test endpoints
@api_router.get("/test/openai")
async def test_openai():
    """Test OpenAI connection"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'OpenAI connection successful'"}],
            max_tokens=10
        )
        return {"status": "success", "response": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@api_router.get("/test/ollama")
async def test_ollama():
    """Test Ollama connection"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": "llama3.1",
                    "prompt": "Say 'Ollama connection successful'",
                    "stream": False
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"status": "success", "response": result.get('response', '')}
                else:
                    return {"status": "error", "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()