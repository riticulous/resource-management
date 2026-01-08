from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middlewares.auth import auth_middleware
from app.api.admin import users, projects
from app.api.admin import shifts
from app.api import auth
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="Resource Management System")

app.middleware("http")(auth_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(auth.router)

from app.api.time import history
app.include_router(history.router)
from app.api import me
app.include_router(me.router)

app.include_router(shifts.router)

from app.api.admin import user_daily

app.include_router(user_daily.router)
