# 🚀 Growdigo AI Backend

FastAPI backend for handling chat conversations with Qdrant vector database.

## **📋 Quick Deploy to Render**

### **1. Connect to Render**

1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the `backend` folder

### **2. Configure Service**

**Name:** `growdigo-ai-backend`

**Environment:** `Python 3`

**Build Command:** `chmod +x build.sh && ./build.sh`

**Start Command:** `chmod +x start.sh && ./start.sh`

### **3. Set Environment Variables**

Add these environment variables in Render dashboard:

```
QDRANT_URL=https://34d79981-cd9b-4e4b-903f-453cf103e9b1.us-west-1-0.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key_here
```

### **4. Deploy**

Click "Create Web Service" and wait for deployment.

## **🔧 Local Development**

### **Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Set Environment Variables**
```bash
export QDRANT_URL="https://your-qdrant-url.cloud.qdrant.io:6333"
export QDRANT_API_KEY="your_qdrant_api_key"
```

### **Run Locally**
```bash
python main.py
```

### **Test Endpoints**
```bash
# Health check
curl http://localhost:8000/health

# Save conversation
curl -X POST http://localhost:8000/conversations \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "user_id": "test", "messages": []}'
```

## **📡 API Endpoints**

### **Health Check**
- `GET /health` - Check backend and Qdrant connection

### **Conversations**
- `POST /conversations` - Save new conversation
- `GET /conversations/{user_id}` - Get user conversations
- `GET /conversations/{user_id}/{conversation_id}` - Get specific conversation
- `PUT /conversations/{user_id}/{conversation_id}` - Update conversation
- `DELETE /conversations/{user_id}/{conversation_id}` - Delete conversation

## **🔒 Security Features**

- ✅ **CORS configured** for frontend domains
- ✅ **User isolation** - Users only see their conversations
- ✅ **API key protection** - Qdrant API key not exposed to frontend
- ✅ **Input validation** - Pydantic models validate all inputs

## **📊 Monitoring**

### **Health Check Response**
```json
{
  "status": "healthy",
  "qdrant_connected": true,
  "collections": 1,
  "timestamp": "2024-01-01T12:00:00"
}
```

### **Logs**
Check Render logs for:
- Startup messages
- Collection creation
- API request logs
- Error messages

## **🛠️ Troubleshooting**

### **Common Issues**

1. **Build Fails**
   - Check Python version (3.9+)
   - Verify requirements.txt
   - Check build logs

2. **Qdrant Connection Fails**
   - Verify QDRANT_URL and QDRANT_API_KEY
   - Check Qdrant service status
   - Test connection locally

3. **CORS Errors**
   - Verify frontend domain in CORS config
   - Check browser console for errors

### **Debug Commands**
```bash
# Test Qdrant connection
python -c "
from qdrant_client import QdrantClient
client = QdrantClient(url='$QDRANT_URL', api_key='$QDRANT_API_KEY')
print(client.get_collections())
"
```

## **🚀 Deployment Files**

- `main.py` - FastAPI application
- `requirements.txt` - Python dependencies
- `build.sh` - Build script for Render
- `start.sh` - Start script for Render
- `render.yaml` - Render configuration
- `Procfile` - Heroku deployment
- `runtime.txt` - Python version specification

## **📈 Next Steps**

1. **Deploy to Render** using the steps above
2. **Update frontend** with backend URL
3. **Test all endpoints** thoroughly
4. **Monitor logs** for any issues
5. **Scale as needed**

**Your backend is ready for production deployment!** 🎉 