// components/BoardVisualizationModal.tsx
import { useEffect, useRef, useState } from 'react';
import { X } from 'lucide-react';
import { Board, Defect } from '../types/board';

interface Props {
  board: Board;
  onClose: () => void;
}

// Цвета для разных сортов (ключ - число grade)
const GRADE_COLORS: Record<number, string> = {
  0: '#10b981', // A
  1: '#3b82f6', // B
  2: '#f59e0b', // C
  3: '#ef4444', // D
};

const GRADE_LETTER: Record<number, string> = {
  0: 'Экстра',
  1: 'А',
  2: 'B',
  3: 'BC',
};

const DEFECT_RU: Record<string, string> = {
  alive_knot: 'Живой сучок',
  dead_knot: 'Мёртвый сучок',
  missed_knot: 'Выпавший сучок',
  resin_pocket: 'Смоляной карман',
  broken_board: 'Битая доска',
};

const DEFECT_COLORS: Record<string, string> = {
  alive_knot: '#22c55e',
  dead_knot: '#f97316',
  missed_knot: '#ef4444',
  resin_pocket: '#facc15',
  broken_board: '#ec4899',
};

function parseLocationToMm(location: string | number | undefined): number | null {
  if (location === undefined || location === null) return null;
  if (typeof location === 'number') return location;
  const match = String(location).match(/^(\d+(?:\.\d+)?)/);
  if (match) return parseFloat(match[1]);
  return null;
}

export function BoardVisualizationModal({ board, onClose }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; text: string; imageUrl: string } | null>(null);
  const [lightboxImage, setLightboxImage] = useState<string | null>(null);

  const maxLength = board.total_length_mm || 6000;
  const BOARD_WIDTH_MM = 200;
  const canvasWidth = 900;
  const canvasHeight = 220;
  const scaleX = canvasWidth / maxLength;
  const scaleY = canvasHeight / BOARD_WIDTH_MM;

  const formatLength = (mm: number) => {
    const rounded = Math.round(mm);
    if (rounded >= 1000) return `${(rounded / 1000).toFixed(1)} м`;
    return `${rounded} мм`;
  };

  // Функция для получения позиции дефекта на холсте (используется и для тултипа, и для клика)
  const getDefectCanvasCoords = (defect: Defect) => {
    let posMm: number | null = null;
    if (defect.position_from_start_mm !== undefined && defect.position_from_start_mm !== null) {
      posMm = defect.position_from_start_mm;
    } else if (defect.position_mm !== undefined && defect.position_mm !== null) {
      posMm = defect.position_mm;
    } else if (defect.location !== undefined) {
      posMm = parseLocationToMm(defect.location);
    }
    if (posMm === null || posMm < 0 || posMm > maxLength) return null;
    const x = posMm * scaleX;
    let y = (defect.width_mm || BOARD_WIDTH_MM / 2) * scaleY;
    y = Math.min(Math.max(y, 8), canvasHeight - 8);
    return { x, y };
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvasWidth, canvasHeight);
    ctx.fillStyle = '#fef3c7';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);
    ctx.strokeStyle = '#78350f';
    ctx.lineWidth = 2;
    ctx.strokeRect(0, 0, canvasWidth, canvasHeight);

    // Разметка
    ctx.fillStyle = '#6b7280';
    ctx.font = '10px sans-serif';
    ctx.strokeStyle = '#d1d5db';
    ctx.lineWidth = 0.5;
    for (let mm = 0; mm <= maxLength; mm += 500) {
      const x = mm * scaleX;
      if (x > canvasWidth) break;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvasHeight);
      ctx.stroke();
      ctx.fillText(formatLength(mm), x + 2, 15);
    }

    // Сегменты раскроя
    if (board.cutting_plan && board.cutting_plan.segments.length > 0) {
      for (const seg of board.cutting_plan.segments) {
        const x1 = seg.from_mm * scaleX;
        const x2 = seg.to_mm * scaleX;
        const gradeNum = seg.grade;
        const color = GRADE_COLORS[gradeNum] || '#9ca3af';
        ctx.fillStyle = color + '60';
        ctx.fillRect(x1, 0, x2 - x1, canvasHeight);
        ctx.strokeStyle = '#374151';
        ctx.lineWidth = 1;
        ctx.strokeRect(x1, 0, x2 - x1, canvasHeight);
        ctx.fillStyle = '#1f2937';
        ctx.font = 'bold 12px sans-serif';
        const gradeLetter = GRADE_LETTER[gradeNum] || '?';
        ctx.fillText(`${gradeLetter} (${formatLength(seg.to_mm - seg.from_mm)})`, x1 + 5, 25);
        ctx.font = '10px sans-serif';
        ctx.fillStyle = '#4b5563';
        ctx.fillText(`${seg.price} руб`, x1 + 5, 45);
      }
    } else {
      ctx.fillStyle = '#9ca3af';
      ctx.font = 'italic 14px sans-serif';
      ctx.fillText('План раскроя не рассчитан', canvasWidth / 2 - 100, canvasHeight / 2);
    }

    // Дефекты
    for (const defect of board.defects) {
      const coords = getDefectCanvasCoords(defect);
      if (!coords) continue;
      const { x, y } = coords;
      const color = DEFECT_COLORS[defect.defect_type] || '#ef4444';
      ctx.beginPath();
      ctx.arc(x, y, 7, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(x, y, 2, 0, 2 * Math.PI);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
    }

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left) * (canvasWidth / rect.width);
      const mouseY = (e.clientY - rect.top) * (canvasHeight / rect.height);
      let foundDefect: Defect | null = null;
      for (const defect of board.defects) {
        const coords = getDefectCanvasCoords(defect);
        if (!coords) continue;
        const dx = mouseX - coords.x;
        const dy = mouseY - coords.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 10) {
          foundDefect = defect;
          break;
        }
      }
      if (foundDefect) {
        const imageUrl = `http://localhost:9000/lining-defects/${foundDefect.image_source}`;
        setTooltip({
          x: e.clientX,
          y: e.clientY,
          text: `${DEFECT_RU[foundDefect.defect_type] || foundDefect.defect_type}${foundDefect.confidence ? ` (${foundDefect.confidence.toFixed(2)})` : ''}`,
          imageUrl,
        });
      } else {
        setTooltip(null);
      }
    };

    const handleCanvasClick = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left) * (canvasWidth / rect.width);
      const mouseY = (e.clientY - rect.top) * (canvasHeight / rect.height);
      for (const defect of board.defects) {
        const coords = getDefectCanvasCoords(defect);
        if (!coords) continue;
        const dx = mouseX - coords.x;
        const dy = mouseY - coords.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 10) {
          const imageUrl = `http://localhost:9000/lining-defects/${defect.image_source}`;
          setLightboxImage(imageUrl);
          break;
        }
      }
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', () => setTooltip(null));
    canvas.addEventListener('click', handleCanvasClick);

    return () => {
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('click', handleCanvasClick);
    };
  }, [board, canvasWidth, canvasHeight, maxLength, scaleX, scaleY]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold text-gray-900">Визуализация доски</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
          <div><span className="font-medium">ID доски:</span> {board.board_id}</div>
          <div><span className="font-medium">Качество:</span> <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
            board.quality === 'A' ? 'bg-green-100 text-green-800' :
            board.quality === 'B' ? 'bg-blue-100 text-blue-800' :
            board.quality === 'C' ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>{board.quality}</span></div>
          <div><span className="font-medium">Дефектов:</span> {board.defects.length}</div>
          {board.cutting_plan && (
            <div><span className="font-medium">Общая выручка:</span> {board.cutting_plan.total_revenue.toFixed(2)} руб</div>
          )}
          <div><span className="font-medium">Общая длина:</span> {formatLength(maxLength)}</div>
          <div><span className="font-medium">Время обработки:</span> {board.processing_duration.toFixed(1)} с</div>
        </div>

        <div className="relative mt-4">
          <canvas
            ref={canvasRef}
            width={canvasWidth}
            height={canvasHeight}
            style={{ width: '100%', height: 'auto', border: '1px solid #d1d5db', borderRadius: '8px', backgroundColor: '#fef3c7', cursor: 'pointer' }}
          />
          {tooltip && (
            <div
              style={{
                position: 'fixed',
                left: tooltip.x + 10,
                top: tooltip.y - 60,
                backgroundColor: '#1f2937',
                color: 'white',
                padding: '6px 10px',
                borderRadius: '8px',
                fontSize: '12px',
                pointerEvents: 'none',
                zIndex: 60,
                boxShadow: '0 4px 8px rgba(0,0,0,0.3)',
                whiteSpace: 'nowrap',
              }}
            >
              {tooltip.text}
            </div>
          )}
        </div>

        <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-500 border-t pt-4">
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-green-500"></div> Живой сучок</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-orange-500"></div> Мёртвый сучок</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-red-500"></div> Выпавший сучок</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-yellow-400"></div> Смоляной карман</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-pink-500"></div> Битая доска</div>
          <div className="flex items-center gap-2 ml-4"><div className="w-4 h-4 bg-green-500/40 border border-gray-500"></div> Экстра </div>
          <div className="flex items-center gap-2"><div className="w-4 h-4 bg-blue-500/40 border border-gray-500"></div> Сорт A</div>
          <div className="flex items-center gap-2"><div className="w-4 h-4 bg-orange-500/40 border border-gray-500"></div> Сорт B</div>
          <div className="flex items-center gap-2"><div className="w-4 h-4 bg-red-500/40 border border-gray-500"></div> Сорт BC</div>
        </div>

        <div className="mt-2 text-xs text-gray-400 text-center">
          Кликните на кружок дефекта, чтобы открыть увеличенное изображение.
        </div>
      </div>

      {/* Lightbox */}
      {lightboxImage && (
        <div
          className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50"
          onClick={() => setLightboxImage(null)}
        >
          <div className="relative max-w-4xl max-h-screen p-4">
            <img
              src={lightboxImage}
              alt="Увеличенное изображение дефекта"
              className="max-w-full max-h-[90vh] object-contain rounded-lg"
            />
            <button
              onClick={() => setLightboxImage(null)}
              className="absolute top-2 right-2 text-white bg-black bg-opacity-50 rounded-full p-1 hover:bg-opacity-75"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}