from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.bookings.router import router as bookings_router
from src.categories.router import router as categories_router
from src.config import settings
from src.locations.router import router as locations_router
from src.master_offering.router import router as offering_router
from src.master_schedule.router import router as schedules_router
from src.masters.router import router as masters_router
from src.offering_images.router import router as offering_images_router
from src.redis.manager import (
    close_redis,
    create_redis,
)
from src.reviews.router import router as reviews_router
from src.tags.router import router as tags_router
from src.users.profile_router import router as user_profile_router
from src.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_redis()

    yield

    await close_redis()


UPLOADS_DIR = Path("uploads")
AVATARS_DIR = UPLOADS_DIR / "avatars"
OFFERINGS_DIR = UPLOADS_DIR / "offerings"

AVATARS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OFFERINGS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


app = FastAPI(
    title="MasterBooking",
    debug=settings.debug,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)
    



app.mount(
    "/uploads",
    StaticFiles(
        directory=UPLOADS_DIR
    ),
    name="uploads",
)


app.include_router(users_router)
app.include_router(user_profile_router)

app.include_router(locations_router)
app.include_router(categories_router)
app.include_router(tags_router)

app.include_router(masters_router)
app.include_router(offering_router)
app.include_router(offering_images_router)
app.include_router(schedules_router)

app.include_router(bookings_router)
app.include_router(reviews_router)