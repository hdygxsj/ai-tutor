from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.settings import (
    TutorConnectionTestResponse,
    TutorSettingsResponse,
    TutorSettingsUpdate,
)
from app.services.tutor_settings_service import TutorSettingsService, tutor_settings_service

router = APIRouter(prefix="/settings/tutor", tags=["settings"])


def get_tutor_settings_service() -> TutorSettingsService:
    return tutor_settings_service


@router.get("", response_model=TutorSettingsResponse)
def get_tutor_settings(
    service: Annotated[TutorSettingsService, Depends(get_tutor_settings_service)],
) -> TutorSettingsResponse:
    return service.get_settings()


@router.put("", response_model=TutorSettingsResponse)
def save_tutor_settings(
    settings: TutorSettingsUpdate,
    service: Annotated[TutorSettingsService, Depends(get_tutor_settings_service)],
) -> TutorSettingsResponse:
    return service.save_settings(settings)


@router.post("/test", response_model=TutorConnectionTestResponse)
def test_tutor_settings(
    settings: TutorSettingsUpdate,
    service: Annotated[TutorSettingsService, Depends(get_tutor_settings_service)],
) -> TutorConnectionTestResponse:
    return service.test_settings(settings)
