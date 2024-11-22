from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from .database import engine
from .models import models
from .routers import auth, students, managers, admin
from .schemas import schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom OpenAPI schema with security
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Student Financial Aid System API",
        version="1.0.0",
        description="API for managing student financial aid applications",
        routes=app.routes,
    )
    
    # Add security scheme
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
        
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Add schemas if they don't exist
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}

    # Add your schema definitions
    openapi_schema["components"]["schemas"].update({
        "Token": {
            "title": "Token",
            "type": "object",
            "properties": {
                "access_token": {"title": "Access Token", "type": "string"},
                "token_type": {"title": "Token Type", "type": "string"}
            },
            "required": ["access_token", "token_type"]
        },
        "TokenData": {
            "title": "TokenData",
            "type": "object",
            "properties": {
                "email": {"title": "Email", "type": "string"}
            }
        },
        # Add other schema definitions as needed
    })
    
    # Add global security requirement
    openapi_schema["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(
    students.router, 
    prefix="/students", 
    tags=["Students"],
    dependencies=[Depends(auth.get_current_user)]
)
app.include_router(
    managers.router, 
    prefix="/managers", 
    tags=["Managers"],
    dependencies=[Depends(auth.get_current_user)]
)
app.include_router(
    admin.public_router,
    prefix="/admin",
    tags=["Admin"]
)
app.include_router(
    admin.protected_router,
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(auth.get_current_user)]
)

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to Student Financial Aid System API",
        "documentation": "/docs",
        "redoc": "/redoc"
    }
