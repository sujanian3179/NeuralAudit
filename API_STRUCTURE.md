# NeuralAudit Production-Ready API Structure

## 📁 Project Structure

```
NeuralAudit/
├── app/                           # FastAPI Application Package (PRODUCTION-READY)
│   ├── __init__.py               # Package initialization
│   ├── server.py                 # FastAPI app configuration & middleware
│   │
│   ├── routers/                  # API endpoint routers (modular & organized)
│   │   ├── __init__.py
│   │   ├── audit.py              # Manual audits & single product processing
│   │   ├── batch.py              # Batch processing & CSV uploads
│   │   ├── results.py            # Query audit results
│   │   └── health.py             # Health checks & utilities
│   │
│   ├── schemas/                  # Request/Response Pydantic models
│   │   ├── __init__.py
│   │   ├── audit_schemas.py      # Audit request/response models
│   │   ├── health_schemas.py     # Health check models
│   │   └── result_schemas.py     # Result response models
│   │
│   └── dependencies/             # Dependency injection
│       └── __init__.py           # Singleton instances (pipeline, db)
│
├── main.py                       # CLI entry point (updated for new structure)
├── api.py                        # DEPRECATED - Use app/server.py instead
│
├── Core Modules (unchanged)
├── pipeline.py                   # Processing pipeline orchestration
├── auditor.py                    # Color family mapping & decision logic
├── model.py                      # ResNet-18 CNN model
├── scraper.py                    # Selenium web automation
├── preprocessing.py              # Image preprocessing
├── database.py                   # Database management
├── config.py                     # Configuration loading
├── logger.py                     # Logging setup
│
├── Configuration Files
├── .env                          # Environment variables (DO NOT COMMIT)
├── .env.example                  # Template for .env (COMMIT THIS)
├── .gitignore                    # Git ignore patterns (COMPREHENSIVE)
├── requirements.txt              # Python dependencies
├── config.py                     # Configuration management
│
├── Resources
├── models/                       # Trained model weights
├── logs/                         # Application logs
├── data/                         # Data storage
└── README.md                     # This file
```

## 🚀 Running the Production-Ready Server

### Option 1: Using main.py (Recommended)
```bash
# Start the API server
python main.py --api

# Or with verbose logging
python main.py --api --verbose
```

### Option 2: Direct import
```python
from app.server import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Option 3: Using Gunicorn (Production)
```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:8000 app.server:app
```

### Option 4: Using Docker
```bash
# Build image
docker build -t neuralaudit .

# Run container
docker run -p 8000:8000 neuralaudit
```

## 📚 API Documentation

Once the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🏗️ Architecture Overview

### Routers (Modular Endpoints)

| Router | Purpose | Endpoints |
|--------|---------|-----------|
| `audit.py` | Manual audits & single products | `/api/audit`, `/api/process-product` |
| `batch.py` | Batch processing & CSV uploads | `/api/process-batch`, `/api/upload-csv` |
| `results.py` | Query audit results | `/api/product-report/{url}`, `/api/results/*` |
| `health.py` | Health checks & utilities | `/health`, `/stats`, `/color-*` |

### Schemas (Type Safety)

All request/response models are organized in `app/schemas/`:
- **audit_schemas.py**: AuditRequest, AuditResponse, ProductUrl, BatchAuditRequest
- **health_schemas.py**: HealthResponse, StatsResponse
- **result_schemas.py**: ResultsResponse, ProductReportResponse

Benefits:
- ✅ Automatic input validation (Pydantic)
- ✅ Auto-generated OpenAPI documentation
- ✅ Type hints for IDE support
- ✅ Easy to test and maintain

### Dependencies (Singleton Pattern)

Located in `app/dependencies/__init__.py`:
```python
from app.dependencies import get_pipeline, get_database

# In routers, use:
pipeline = get_pipeline()  # Returns singleton instance
db = get_database()        # Returns singleton instance
```

Benefits:
- ✅ Single instance of expensive objects (pipeline, database)
- ✅ Easy to mock for testing
- ✅ Clean dependency injection

## 🔒 .gitignore - What Gets Committed

### ✅ COMMITTED (Important for running code)
```
- Source code (.py files)
- Configuration templates (.env.example)
- Requirements (requirements.txt)
- Setup scripts (setup.sh, setup.bat)
- Documentation (README.md, etc.)
```

### ❌ NOT COMMITTED (Keep local only)
```
- Environment variables (.env) - Contains secrets
- Logs (logs/) - Large & temporary
- Model weights (models/*.pth) - Download at runtime
- Database files (*.db, database.json) - Local data
- IDE files (.vscode/, .idea/) - Personal setup
- Cache (__pycache__/) - Build artifacts
- Virtual environments (venv/, .venv/) - User-specific
- Credentials & secrets - NEVER commit
```

### 📋 Gitignore Organization

The `.gitignore` file is organized by category:
1. **Python** - Standard Python artifacts
2. **IDE & Editors** - VS Code, PyCharm, Sublime, etc.
3. **Project-Specific** - Development files, secrets, data
4. **Docker** - Container configurations
5. **Deployment** - CI/CD artifacts
6. **Exceptions** - Important files to keep

## 🔄 Migration from Old Structure

### Before (api.py)
```python
from api import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)
```

### After (app/server.py)
```python
from app.server import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Using CLI (Simplest)
```bash
# Both work the same now!
python main.py --api
```

## 📦 Adding New Endpoints

### Step 1: Create router file
```python
# app/routers/new_feature.py
from fastapi import APIRouter

router = APIRouter(
    prefix="/api",
    tags=["New Feature"],
)

@router.get("/new-endpoint")
async def new_endpoint():
    return {"status": "ok"}
```

### Step 2: Register in __init__.py
```python
# app/routers/__init__.py
from .new_feature import router as new_feature_router

__all__ = [
    ...,
    "new_feature_router",
]
```

### Step 3: Add to server.py
```python
# app/server.py
from app.routers import new_feature_router

app.include_router(new_feature_router)
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_health_check
```

## 🚨 Common Errors & Solutions

### Error: `ModuleNotFoundError: No module named 'app'`
**Solution**: Run from project root, not from subdirectories
```bash
cd /Users/ayushranjanjha/code_repo/NeuralAudit
python main.py --api
```

### Error: `Cannot import from app.dependencies`
**Solution**: Ensure all `__init__.py` files exist in app/ subdirectories
```bash
ls -la app/__init__.py          # Should exist
ls -la app/routers/__init__.py  # Should exist
ls -la app/schemas/__init__.py  # Should exist
```

### Error: Circular imports
**Solution**: The new structure avoids this by using clean separation:
- Routers import from schemas & dependencies, not from each other
- Dependencies inject instances, not import everything

## 📊 Performance Improvements

The new structure provides:
- ✅ **Faster startup**: Only loads what's needed
- ✅ **Better scaling**: Modular code easier to parallelize
- ✅ **Cleaner code**: Routers focus on their endpoints
- ✅ **Easier testing**: Each router can be tested independently

## 🔐 Security Best Practices

1. **Never commit .env** - Use `.env.example` template
2. **Use environment variables** for secrets
3. **Validate all inputs** - Pydantic handles this automatically
4. **Use CORS carefully** - Currently allows all origins, restrict in production
5. **Run with Gunicorn** - Better than Uvicorn for production
6. **Use HTTPS** - Configure reverse proxy (nginx) to terminate SSL

### Production Deployment Checklist
- [ ] Update CORS origins in `app/server.py`
- [ ] Set `API_DEBUG=False` in .env
- [ ] Use proper database (not JSON)
- [ ] Set up logging to file
- [ ] Run behind reverse proxy (nginx)
- [ ] Enable HTTPS
- [ ] Monitor logs and errors
- [ ] Set up automated backups

## 📖 Documentation Files

- **API_STRUCTURE.md** - This file (architecture & migration)
- **IMPLEMENTATION_GUIDE.md** - How to add features
- **DEPLOYMENT_GUIDE.md** - Production deployment
- **TESTING_GUIDE.md** - Testing strategies

## ❓ FAQ

**Q: Should I still use api.py?**
A: No, api.py is deprecated. Use `app/server.py` and the new router structure.

**Q: Do I need to change my CLI commands?**
A: No! `python main.py --api` still works. It now uses the new server internally.

**Q: Can I run tests with the new structure?**
A: Yes! Tests automatically work with the modular structure. Check test files.

**Q: How do I add CORS for specific domains?**
A: Edit `app/server.py` and change `allow_origins` from `["*"]` to your domains:
```python
allow_origins=[
    "https://example.com",
    "https://app.example.com",
]
```

**Q: What's the difference between routers and blueprints?**
A: Routers are FastAPI's equivalent to Flask blueprints. Each router handles a set of related endpoints.

## 🤝 Contributing

When adding new features:
1. Create router file in `app/routers/`
2. Create schemas in `app/schemas/`
3. Add dependencies in `app/dependencies/`
4. Register in appropriate `__init__.py` files
5. Update documentation
6. Add tests
7. Ensure `requirements.txt` is up-to-date

## 📞 Support

For issues or questions:
1. Check existing issues in GitHub
2. Review documentation files
3. Check server logs in `logs/` directory
4. Enable verbose logging: `python main.py --api --verbose`

---

**Last Updated**: April 25, 2024
**Version**: 1.0.0 (Production-Ready)
