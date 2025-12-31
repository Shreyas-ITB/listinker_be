from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import connect_to_mongo, close_mongo_connection
from routers import auth, users, ads, favorites, chatrooms, categories
from database import get_database
from utils.load_categories import initialize_categories_collection
from utils.load_follow_relations import initialize_follow_relations_collections
from fastapi.openapi.docs import get_swagger_ui_html
from config import DOCS_USERNAME, DOCS_PASSWORD
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, status, HTTPException
import secrets

app = FastAPI(title="Listinker API", description="Classified Ads Platform API", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await connect_to_mongo()
    db = await get_database()
    await initialize_categories_collection(db)
    await initialize_follow_relations_collections(db)

@app.on_event("shutdown")
async def shutdown():
    await close_mongo_connection()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ads.router)
app.include_router(favorites.router)
app.include_router(categories.router)
app.include_router(chatrooms.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Listinker API"}

security = HTTPBasic()

def verify_docs_access(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, DOCS_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, DOCS_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials for API documentation",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

# ✅ Override Swagger UI
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui(credentials: HTTPBasicCredentials = Depends(verify_docs_access)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Listinker API Docs")

# ✅ Protect openapi.json schema itself
@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(credentials: HTTPBasicCredentials = Depends(verify_docs_access)):
    return get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description=app.description,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
