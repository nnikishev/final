// components/BoardVisualizationModal.tsx
import { useEffect, useRef, useState } from 'react';
import { X, Ruler } from 'lucide-react';
import { Board, Defect } from '../types/board';

interface Props {
  board: Board;
  onClose: () => void;
}

// Цвета для разных сортов
const GRADE_COLORS: Record<string, string> = {
  A: '#10b981', // зелёный
  B: '#3b82f6', // синий
  C: '#f59e0b', // оранжевый
  D: '#ef4444', // красный
};

// Отображение типа дефекта на русский
const DEFECT_RU: Record<string, string> = {
  alive_knot: 'Живой сучок',
  dead_knot: 'Мёртвый сучок',
  missed_knot: 'Выпавший сучок',
  resin_pocket: 'Смоляной карман',
  broken_board: 'Битая доска',
};

// Цвета для маркеров дефектов
const DEFECT_COLORS: Record<string, string> = {
  alive_knot: '#22c55e',
  dead_knot: '#f97316',
  missed_knot: '#ef4444',
  resin_pocket: '#facc15',
  broken_board: '#ec4899',
};

export function BoardVisualizationModal({ board, onClose }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; text: string } | null>(null);

  const maxLength = board.total_length_mm || 6000;

  // Стандартная ширина доски для визуализации (в мм)
  const BOARD_WIDTH_MM = 200;
  // Размеры canvas в px (фиксированные для простоты)
  const canvasWidth = 900;
  const canvasHeight = 220;
  // Масштаб: мм -> px
  const scaleX = canvasWidth / maxLength;
  const scaleY = canvasHeight / BOARD_WIDTH_MM;

  // Форматирование миллиметров в метры/сантиметры
  const formatLength = (mm: number) => {
    if (mm >= 1000) return `${(mm / 1000).toFixed(1)} м`;
    return `${mm} мм`;
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvasWidth, canvasHeight);

    // 1. Рисуем фон доски (светло-жёлтый, имитация дерева)
    ctx.fillStyle = '#fef3c7';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);
    ctx.strokeStyle = '#78350f';
    ctx.lineWidth = 2;
    ctx.strokeRect(0, 0, canvasWidth, canvasHeight);

    // 2. Рисуем линии разметки длины (каждые 500 мм)
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

    // 3. Рисуем сегменты раскроя (если есть)
    if (board.cutting_plan && board.cutting_plan.segments.length > 0) {
      for (const seg of board.cutting_plan.segments) {
        const x1 = seg.from_mm * scaleX;
        const x2 = seg.to_mm * scaleX;
        const grade = seg.grade;
        const color = GRADE_COLORS[grade] || '#9ca3af';
        ctx.fillStyle = color + '60'; // полупрозрачный
        ctx.fillRect(x1, 0, x2 - x1, canvasHeight);
        ctx.strokeStyle = '#374151';
        ctx.lineWidth = 1;
        ctx.strokeRect(x1, 0, x2 - x1, canvasHeight);
        // Подпись сорта и длины
        ctx.fillStyle = '#1f2937';
        ctx.font = 'bold 12px sans-serif';
        ctx.fillText(`${grade} (${formatLength(seg.to_mm - seg.from_mm)})`, x1 + 5, 25);
        // Подпись цены
        ctx.font = '10px sans-serif';
        ctx.fillStyle = '#4b5563';
        ctx.fillText(`${seg.price} руб`, x1 + 5, 45);
      }
    } else {
      // Если плана раскроя нет, просто показываем пустую доску
      ctx.fillStyle = '#9ca3af';
      ctx.font = 'italic 14px sans-serif';
      ctx.fillText('План раскроя не рассчитан', canvasWidth / 2 - 100, canvasHeight / 2);
    }

    // 4. Рисуем дефекты
    for (const defect of board.defects) {
      const x = (defect.position_from_start_mm || 0) * scaleX;
      // y координата по ширине: width_mm может быть от 0 до BOARD_WIDTH_MM
      let y = (defect.width_mm || BOARD_WIDTH_MM / 2) * scaleY;
      // Ограничиваем, чтобы не вылезать за края
      y = Math.min(Math.max(y, 8), canvasHeight - 8);
      const color = DEFECT_COLORS[defect.defect_type] || '#ef4444';

      ctx.beginPath();
      ctx.arc(x, y, 7, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();
      // Маленькая белая точка в центре для акцента
      ctx.beginPath();
      ctx.arc(x, y, 2, 0, 2 * Math.PI);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
    }

    // Обработчик движения мыши для тултипа
    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left) * (canvasWidth / rect.width);
      const mouseY = (e.clientY - rect.top) * (canvasHeight / rect.height);
      let found: Defect | null = null;
      for (const defect of board.defects) {
        const x = (defect.position_from_start_mm || 0) * scaleX;
        let y = (defect.width_mm || BOARD_WIDTH_MM / 2) * scaleY;
        y = Math.min(Math.max(y, 8), canvasHeight - 8);
        const dx = mouseX - x;
        const dy = mouseY - y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 10) {
          found = defect;
          break;
        }
      }
      if (found) {
        setTooltip({
          x: e.clientX,
          y: e.clientY,
          text: `${DEFECT_RU[found.defect_type] || found.defect_type} (${(found.confidence || 0).toFixed(2)})`
        });
      } else {
        setTooltip(null);
      }
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', () => setTooltip(null));

    return () => {
      canvas.removeEventListener('mousemove', handleMouseMove);
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
            style={{ width: '100%', height: 'auto', border: '1px solid #d1d5db', borderRadius: '8px', backgroundColor: '#fef3c7' }}
          />
          {tooltip && (
            <div
              style={{
                position: 'fixed',
                left: tooltip.x + 10,
                top: tooltip.y - 30,
                backgroundColor: '#1f2937',
                color: 'white',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '12px',
                pointerEvents: 'none',
                zIndex: 60,
                whiteSpace: 'nowrap',
                boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
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
          <div className="flex items-center gap-2 ml-4"><div className="w-4 h-4 bg-green-500/40 border border-gray-500"></div> Сорт A</div>
          <div className="flex items-center gap-2"><div className="w-4 h-4 bg-blue-500/40 border border-gray-500"></div> Сорт B</div>
          <div className="flex items-center gap-2"><div className="w-4 h-4 bg-orange-500/40 border border-gray-500"></div> Сорт C</div>
          <div className="flex items-center gap-2"><div className="w-4 h-4 bg-red-500/40 border border-gray-500"></div> Сорт D</div>
        </div>

        <div className="mt-2 text-xs text-gray-400 text-center">
          Наведите на кружок дефекта для подробностей. Цветные полосы — сегменты раскроя с указанием сорта, длины и цены.
        </div>
      </div>
    </div>
  );
}