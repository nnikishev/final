# app/services/frame_processor.py
import uuid
import os
import cv2
import asyncio
import io
import uuid
import boto3
from PIL import Image
from pathlib import Path
from app.services.video_source import VideoSource
from app.services.state_detector import StateDetector
from app.services.defect_detector import DefectDetector
from app.services.coordinate_converter import CoordinateConverter
from app.services.publisher import RedisPublisher
from app.models.schemas import BoardStartEvent, BoardEndEvent, DefectEvent, BBox
import concurrent.futures


class FrameProcessor:
    def __init__(self,
                 source: VideoSource,
                 state_detector: StateDetector,
                 defect_detector: DefectDetector,
                 converter: CoordinateConverter,
                 publisher: RedisPublisher,
                 camera_id: str,
                 fps_target: int = 30,
                 defect_every_n: int = 28,
                 save_defect_images: bool = True,
                 defect_images_root: Path = Path("defects")):
        self.source = source
        self.state_detector = state_detector
        self.defect_detector = defect_detector
        self.converter = converter
        self.publisher = publisher
        self.camera_id = camera_id
        self.fps_target = fps_target
        self.defect_every_n = defect_every_n
        self.save_defect_images = save_defect_images
        self.defect_images_root = Path(defect_images_root)
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.running = False
        self.current_board = None   # хранит board_id, start_frame, собранные дефекты, а также счётчик дефектов
        self.boards_processed = 0
        self.total_defects = 0
        self.frame_count = 0
        self.last_frame_time = 0.0
        self.minio_endpoint = os.getenv('MINIO_ENDPOINT', 'minio:9000')
        self.minio_access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.minio_secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        self.minio_bucket = os.getenv('MINIO_BUCKET', 'lining-defects')
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f'http://{self.minio_endpoint}',
            aws_access_key_id=self.minio_access_key,
            aws_secret_access_key=self.minio_secret_key,
            use_ssl=False,
            verify=False
        )
        # Создаём бакет, если его нет
        try:
            self.s3_client.create_bucket(Bucket=self.minio_bucket)
        except:
            pass

    def _save_defect_image(self, frame, defect: dict, board_id: uuid.UUID, defect_index: int, object_name: str):
        """Аннотирует кадр и загружает в MinIO (выполняется в потоке)."""
        annotated = frame.copy()
        bbox = defect['bbox']
        defect_type = defect['type']
        confidence = defect['confidence']

        color_map = {
            'alive_knot': (0, 255, 0),
            'dead_knot': (0, 165, 255),
            'missed_knot': (0, 0, 255),
            'resin_pocket': (255, 255, 0),
            'broken_board': (255, 0, 255)
        }
        color = color_map.get(defect_type, (0, 255, 0))

        cv2.rectangle(annotated, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
        label = f"{defect_type} {confidence:.2f}"
        cv2.putText(annotated, label, (bbox[0], bbox[1] - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(annotated_rgb)
        buffer = io.BytesIO()
        pil_img.save(buffer, format='JPEG', quality=95)
        buffer.seek(0)

        try:
            self.s3_client.upload_fileobj(
                buffer,
                self.minio_bucket,
                object_name,
                ExtraArgs={'ContentType': 'image/jpeg'}
            )
            print(f"Saved defect image to MinIO: {object_name}")
        except Exception as e:
            print(f"Failed to upload defect image to MinIO: {e}")

    # Асинхронная обёртка: возвращает object_name сразу, загрузка в фоне
    async def _save_defect_image_async(self, frame, defect: dict, board_id: uuid.UUID, defect_index: int) -> str:
        object_name = f"defects/board_{board_id}/defect_{defect_index:04d}.jpg"
        loop = asyncio.get_running_loop()
        # Запускаем загрузку в потоке без ожидания (fire-and-forget)
        loop.run_in_executor(self._executor, self._save_defect_image,
                            frame, defect, board_id, defect_index, object_name)
        return object_name

    async def run(self):
        """Запускает обработку видеопотока."""
        self.running = True
        frame_idx = 0
        fps = self.fps_target

        # Для подсчёта дефектов в пределах одной доски
        defect_counter = 0

        while self.running:
            ret, frame = self.source.read()
            if not ret:
                break

            # 1. Детекция состояния (начало/конец доски)
            state_event = self.state_detector.process_frame(frame, frame_idx, fps)
            if state_event:
                if state_event['type'] == 'board_start':
                    board_id = uuid.uuid4()
                    self.current_board = {
                        'board_id': board_id,
                        'start_frame': state_event['start_frame'],
                        'start_time_sec': state_event['start_time_sec'],
                        'defects': []
                    }
                    defect_counter = 0  # сброс счётчика для новой доски
                    event = BoardStartEvent(
                        board_id=board_id,
                        camera_id=self.camera_id,
                        start_frame=state_event['start_frame'],
                        start_time_sec=state_event['start_time_sec']
                    )
                    await self.publisher.publish(event)

                elif state_event['type'] == 'board_end' and self.current_board:
                    # Подсчёт суммарных дефектов по типам
                    summary = {}
                    for d in self.current_board['defects']:
                        d_type = d['defect_type']
                        summary[d_type] = summary.get(d_type, 0) + 1
                    length_mm = (state_event['end_time_sec'] - self.current_board['start_time_sec']) * self.converter.speed
                    end_event = BoardEndEvent(
                        board_id=self.current_board['board_id'],
                        total_length_mm=length_mm,
                        defects_summary=summary
                    )
                    await self.publisher.publish(end_event)
                    self.boards_processed += 1
                    self.current_board = None

            # 2. Детекция дефектов (только если внутри доски)
            if self.current_board and (frame_idx % self.defect_every_n == 0):
                defects = self.defect_detector.detect(frame)
                for defect in defects:
                    # Вычисляем позицию в миллиметрах
                    bbox_center_x = (defect['bbox'][0] + defect['bbox'][2]) // 2
                    bbox_center_y = (defect['bbox'][1] + defect['bbox'][3]) // 2
                    position_mm = self.converter.convert(
                        frame_idx=frame_idx,
                        board_start_frame=self.current_board['start_frame'],
                        fps=fps,
                        bbox_center_x=bbox_center_x,
                        bbox_center_y=bbox_center_y
                    )
                    defect_counter += 1
                    image_src = await self._save_defect_image_async(frame, defect, self.current_board['board_id'], defect_counter)
                    defect_event = DefectEvent(
                        board_id=self.current_board['board_id'],
                        defect_type=defect['type'],
                        confidence=defect['confidence'],
                        position_mm=position_mm,
                        bbox_px=BBox(x1=defect['bbox'][0], y1=defect['bbox'][1],
                                     x2=defect['bbox'][2], y2=defect['bbox'][3]),
                        frame_idx=frame_idx,
                        image_source=image_src
                    )
                    await self.publisher.publish(defect_event)
                        
                    self.current_board['defects'].append(defect_event.dict())
                    self.total_defects += 1

            frame_idx += 1
            await asyncio.sleep(1 / self.fps_target)

        self.source.release()

    async def stop(self):
        self.running = False