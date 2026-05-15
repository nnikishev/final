import { useState } from 'react';
import { Board, Quality, DefectSeverity } from '../types/board';
import { X, Plus, Trash2 } from 'lucide-react';

interface EditBoardModalProps {
  board: Board;
  onClose: () => void;
  onSave: (updates: Partial<Board>) => void;
}

export function EditBoardModal({ board, onClose, onSave }: EditBoardModalProps) {
  const [quality, setQuality] = useState<Quality>(board.quality);
  const [defects, setDefects] = useState(board.defects);

  const handleAddDefect = () => {
    setDefects([
      ...defects,
      {
        id: `new-${Date.now()}`,
        defect_type: '',
        severity: 'medium' as DefectSeverity,
        location: ''
      }
    ]);
  };

  const handleRemoveDefect = (id: string) => {
    setDefects(defects.filter(d => d.id !== id));
  };

  const handleDefectChange = (id: string, field: string, value: string) => {
    setDefects(defects.map(d =>
      d.id === id ? { ...d, [field]: value } : d
    ));
  };

  const handleSave = () => {
    onSave({ quality, defects });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Редактировать доску {board.board_id}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Качество
            </label>
            <select
              value={quality}
              onChange={(e) => setQuality(e.target.value as Quality)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="A">A</option>
              <option value="B">B</option>
              <option value="C">C</option>
              <option value="D">D</option>
            </select>
          </div>

          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Дефекты ({defects.length})
              </label>
              <button
                onClick={handleAddDefect}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                Добавить
              </button>
            </div>

            <div className="space-y-3">
              {defects.map((defect) => (
                <div key={defect.id} className="p-4 border border-gray-200 rounded-md">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">Тип дефекта</label>
                        <input
                          type="text"
                          value={defect.defect_type}
                          onChange={(e) => handleDefectChange(defect.id, 'defect_type', e.target.value)}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                          placeholder="Scratch, Crack..."
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">Серьезность</label>
                        <select
                          value={defect.severity}
                          onChange={(e) => handleDefectChange(defect.id, 'severity', e.target.value)}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                          <option value="critical">Critical</option>
                        </select>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemoveDefect(defect.id)}
                      className="ml-2 p-1.5 text-red-600 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">Локация</label>
                    <input
                      type="text"
                      value={defect.location}
                      onChange={(e) => handleDefectChange(defect.id, 'location', e.target.value)}
                      className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      placeholder="x:100,y:200"
                    />
                  </div>
                </div>
              ))}
              {defects.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">Нет дефектов</p>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            Отмена
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Сохранить
          </button>
        </div>
      </div>
    </div>
  );
}
