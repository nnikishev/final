import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.models.schemas import TestImageResponse, TestVideoTaskResponse, DefectInFrame, BBox
from app.services.defect_detector import DefectDetector
from app.services.coordinate_converter import CoordinateConverter
from app.services.task_manager import TaskManager
from app.core.dependencies import get_defect_detector, get_coordinate_converter
from app.core.config import settings

router = APIRouter(prefix="/test", tags=["Test"])

_task_manager = TaskManager()

@router.post(
    "/image",
    response_model=TestImageResponse,
    summary="Тест на одном изображении",
    description="Загрузите фото доски – сервис вернёт список обнаруженных дефектов."
)
async def test_image(
    file: UploadFile = File(...),
    defect_detector: DefectDetector = Depends(get_defect_detector)
):
    """Загружает фото, возвращает список обнаруженных дефектов."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    import cv2
    frame = cv2.imread(tmp_path)
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    defects = defect_detector.detect(frame)
    defects_schema = []
    for d in defects:
        bbox = BBox(x1=d['bbox'][0], y1=d['bbox'][1], x2=d['bbox'][2], y2=d['bbox'][3])
        defects_schema.append(DefectInFrame(
            type=d['type'],
            confidence=d['confidence'],
            bbox_px=bbox,
            frame_idx=0
        ))
    return TestImageResponse(defects=defects_schema, annotated_image_url=None)

@router.post(
    "/video",
    response_model=TestVideoTaskResponse,
    summary="Тест на видеофайле",
    description="Загрузите видео – обработка в фоне, возвращается task_id для опроса результата."
)
async def test_video(
    file: UploadFile = File(...),
    defect_detector: DefectDetector = Depends(get_defect_detector),
    converter: CoordinateConverter = Depends(get_coordinate_converter)
):
    """Загружает видео, запускает фоновую обработку, возвращает task_id."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    from app.services.state_detector import StateDetector
    state_detector = StateDetector(
        model_path=settings.STATE_MODEL_PATH,
        window_size=settings.STATE_WINDOW_SIZE,
        smoothing_buffer=settings.STATE_SMOOTHING,
        inference_every_n=settings.STATE_INFERENCE_EVERY_N_FRAMES
    )

    task_id = await _task_manager.run_video_task(
        video_path=tmp_path,
        state_detector=state_detector,
        defect_detector=defect_detector,
        converter=converter,
        defect_every_n=settings.DEFECT_INFERENCE_EVERY_N_FRAMES,
        fps_target=settings.FPS_TARGET
    )
    return TestVideoTaskResponse(task_id=task_id, status="pending")

@router.get(
    "/video/{task_id}",
    summary="Получить результат обработки видео",
    description="По task_id возвращает статус и результат фоновой обработки."
)
async def get_video_result(task_id: str):
    """Возвращает результат обработки видео по task_id."""
    task = _task_manager.get_task(task_id)
    return JSONResponse(content=task)