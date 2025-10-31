# 🚀 Get Started in 5 Minutes

Welcome to the GenAI Document Mapping Microservice! This guide will get you up and running quickly.

## ⚡ Quick Start

### Step 1: Configure Environment (1 min)
```bash
cd microservice
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 2: Start Services (2 min)
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

This starts:
- ✅ PostgreSQL database
- ✅ Qdrant vector database
- ✅ FastAPI application

### Step 3: Verify Running (1 min)
Open in browser: http://localhost:8000/docs

You should see the interactive API documentation!

### Step 4: Test the API (1 min)
```bash
# Check health
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "healthy",
  "vector_store": "healthy"
}
```

## 🎯 Your First Document

### Option A: Use the Example Script
```bash
python scripts/example_usage.py
```

Follow the prompts to upload and process a document!

### Option B: Use cURL
```bash
# 1. Upload document
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@your-document.pdf"

# Copy the document_id from response

# 2. Process document
curl -X POST "http://localhost:8000/documents/process" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "YOUR_DOCUMENT_ID"}'

# 3. Vectorize document
curl -X POST "http://localhost:8000/documents/vectorize" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "YOUR_DOCUMENT_ID"}'

# 4. Generate topics
curl -X POST "http://localhost:8000/topics/generate" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "YOUR_DOCUMENT_ID", "num_topics": 5}'
```

### Option C: Use Postman
1. Import `postman_collection.json` into Postman
2. Set `document_id` variable
3. Execute requests in order

## 📚 What's Next?

### Learn More
- 📖 **Full Documentation**: [README.md](README.md)
- 🏗️ **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- 🔧 **Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- 🗂️ **Project Structure**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

### Development
- 👨‍💻 **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)
- ✅ **Run Tests**: `pytest tests/ -v`
- 🎨 **Format Code**: `black app/ tests/`

### Interactive API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 Common Commands

```bash
# Start services
./scripts/start.sh

# Stop services
./scripts/stop.sh

# View logs
docker-compose logs -f api

# Run tests
pytest tests/ -v

# Check health
curl http://localhost:8000/health
```

## 📝 API Workflow

```
1. Upload Document    → POST /documents/upload
2. Process Document   → POST /documents/process
3. Vectorize Chunks   → POST /documents/vectorize
4. Generate Topics    → POST /topics/generate
5. Generate Subtopics → POST /topics/subtopics/generate
6. Generate Summary   → POST /topics/summary/generate
7. Get Full Content   → POST /topics/content
```

## 🆘 Troubleshooting

### Services won't start?
```bash
# Check Docker is running
docker ps

# Restart services
docker-compose restart
```

### API key error?
```bash
# Verify .env file
cat .env | grep OPENAI_API_KEY

# Make sure no quotes around the key
# Wrong: OPENAI_API_KEY="sk-..."
# Right: OPENAI_API_KEY=sk-...
```

### Database connection failed?
```bash
# Check PostgreSQL
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

## 🎓 Key Features

✅ **Multi-format Support**: PDF, EPUB, MOBI
✅ **Smart Chunking**: LangChain text splitters
✅ **Vector Search**: Qdrant for semantic search
✅ **Mind Mapping**: AI-generated topic hierarchy
✅ **Summarization**: AI-powered summaries
✅ **API-First**: Complete control via REST API
✅ **Type Safe**: Pydantic V2 validation
✅ **Production Ready**: Docker, tests, docs

## 💡 Example Use Cases

### 1. Research Paper Analysis
Upload → Process → Generate topics → Get summaries for each topic

### 2. Book Knowledge Extraction
Upload → Process → Generate chapters as topics → Generate subsections as subtopics

### 3. Document Q&A
Upload → Process → Vectorize → Use topic content for context

### 4. Content Organization
Upload → Generate mind map → Export hierarchical structure

## 📊 Architecture at a Glance

```
Client
  ↓
FastAPI (API Layer)
  ↓
Services (Business Logic)
  ↓
Repositories (Data Access)
  ↓
Databases (PostgreSQL + Qdrant)
```

## 🔐 Security Notes

**For Production:**
- Add authentication (JWT/API keys)
- Enable HTTPS
- Set up rate limiting
- Use secrets management
- Restrict CORS origins
- Scan uploaded files

## 📞 Support

- **Documentation**: Check README.md
- **API Reference**: http://localhost:8000/docs
- **Examples**: scripts/example_usage.py
- **Issues**: Create GitHub issue

## 🌟 What Makes This Special?

- ✨ **Senior-Level Architecture**: Clean, scalable, maintainable
- ✨ **Latest LangChain**: LCEL, structured outputs
- ✨ **Type Safety**: Pydantic V2 everywhere
- ✨ **Complete Docs**: 6 documentation files
- ✨ **Production Ready**: Docker, tests, monitoring
- ✨ **API-First**: Each action is a separate endpoint

## 🎉 You're Ready!

You now have a production-ready GenAI microservice running locally.

**Next Steps:**
1. Try the example script: `python scripts/example_usage.py`
2. Explore the API docs: http://localhost:8000/docs
3. Read the full documentation: [README.md](README.md)
4. Build something amazing! 🚀

---

**Questions?** Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common commands and troubleshooting.

**Want to contribute?** Read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Need architecture details?** See [ARCHITECTURE.md](ARCHITECTURE.md) for deep dive.

---

Built with ❤️ using FastAPI, LangChain, PostgreSQL, and Qdrant

