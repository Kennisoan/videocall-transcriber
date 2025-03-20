from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers import recordings, recorder, auth, users, permissions

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1234", "http://localhost:3000",
                   "http://localhost:80", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Hello from the Video Call Transcriber API"}


# Include routers
app.include_router(recordings.router)
app.include_router(recorder.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(permissions.router)
