import asyncio
import uuid
from typing import Dict, Any
from pathlib import Path
import tempfile
import shutil
import logging
from app.services.video_source import FileVideoSource
from app.services.frame_processor import FrameProcessor

logger  = logging.getLogger(__name__)

class DummyPublisher:
    """Заглушка издателя для тестов (ничего не отправляет в Redis)."""
    async def publish(self, event):
        logger.log(event)
    async def close(self):
        pass

class TaskManager:
    """Хранилище фоновых задач обработки видео (для тестового эндпоинта)."""
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}

    async def run_video_task(self, video_path: Path,
                            state_detector, defect_detector, converter,
                            defect_every_n: int, fps_target: int,
                            save_defect_images: bool = True,
                            defect_images_root: Path = Path("defects")):
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {"status": "processing", "result": None}
        try:
            source = FileVideoSource(str(video_path))
            publisher = DummyPublisher()
            processor = FrameProcessor(
                source=source,
                state_detector=state_detector,
                defect_detector=defect_detector,
                converter=converter,
                publisher=publisher,
                camera_id="test",
                fps_target=fps_target,
                defect_every_n=defect_every_n,
                save_defect_images=save_defect_images,
                defect_images_root=defect_images_root
            )
            await processor.run()
            self.tasks[task_id] = {
                "status": "completed",
                "result": {
                    "boards_processed": processor.boards_processed,
                    "total_defects": processor.total_defects,
                    "defect_images_saved_to": str(defect_images_root)
                }
            }
        except Exception as e:
            self.tasks[task_id] = {"status": "failed", "error": str(e)}
        finally:
            if video_path.exists():
                video_path.unlink()
        return task_id

    def get_task(self, task_id: str) -> dict:
        return self.tasks.get(task_id, {"status": "not_found"})