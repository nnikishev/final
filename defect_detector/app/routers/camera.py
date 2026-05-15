import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.models.schemas import StartCameraRequest, CameraStatusResponse
from app.core.dependencies import get_publisher, get_state_detector, get_defect_detector, get_coordinate_converter
from app.services.publisher import RedisPublisher
from app.services.state_detector import StateDetector
from app.services.defect_detector import DefectDetector
from app.services.coordinate_converter import CoordinateConverter
from app.services.video_source import RTSPSource
from app.services.frame_processor import FrameProcessor
from app.core.config import settings

router = APIRouter(prefix="/camera", tags=["Camera"])

_active_processor: FrameProcessor = None
_active_task: asyncio.Task = None

@router.post(
    "/start",
    response_model=dict,
    summary="Запустить обработку RTSP-камеры",
    description="Начинает чтение видеопотока, детекцию дефектов и публикацию событий."
)
async def start_camera(
    req: StartCameraRequest,
    background_tasks: BackgroundTasks,
    publisher: RedisPublisher = Depends(get_publisher),
    state_detector: StateDetector = Depends(get_state_detector),
    defect_detector: DefectDetector = Depends(get_defect_detector),
    converter: CoordinateConverter = Depends(get_coordinate_converter),
):
    """Запускает обработку RTSP-потока с указанной камеры."""
    global _active_processor, _active_task
    if _active_processor is not None and _active_processor.running:
        raise HTTPException(status_code=400, detail="Camera already processing")

    source = RTSPSource(req.rtsp_url, reconnect_interval_sec=settings.RTSP_RECONNECT_INTERVAL_SEC)
    _active_processor = FrameProcessor(
        source=source,
        state_detector=state_detector,
        defect_detector=defect_detector,
        converter=converter,
        publisher=publisher,
        camera_id=req.camera_id,
        fps_target=settings.FPS_TARGET,
        defect_every_n=settings.DEFECT_INFERENCE_EVERY_N_FRAMES,
        save_defect_images=settings.SAVE_DEFECT_IMAGES,
        defect_images_root=settings.DEFECT_IMAGES_ROOT
    )
    _active_task = asyncio.create_task(_active_processor.run())
    return {"status": "started", "camera_id": req.camera_id}

@router.post(
    "/stop",
    response_model=dict,
    summary="Остановить обработку камеры",
    description="Прекращает чтение видеопотока и освобождает ресурсы."
)
async def stop_camera():
    """Останавливает обработку камеры."""
    global _active_processor, _active_task
    if _active_processor is None or not _active_processor.running:
        raise HTTPException(status_code=400, detail="No active camera processing")
    await _active_processor.stop()
    if _active_task:
        _active_task.cancel()
    _active_processor = None
    _active_task = None
    return {"status": "stopped"}

@router.get(
    "/status",
    response_model=CameraStatusResponse,
    summary="Статус обработки",
    description="Возвращает информацию о текущем состоянии камеры и количестве обработанных досок."
)
async def camera_status():
    """Возвращает статус обработки."""
    if _active_processor is None or not _active_processor.running:
        return CameraStatusResponse(is_running=False)
    return CameraStatusResponse(
        is_running=True,
        camera_id=_active_processor.camera_id,
        boards_processed=_active_processor.boards_processed,
        total_defects_detected=_active_processor.total_defects,
        processing_fps=0.0
    )