import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { Search, Filter, Edit2, Trash2, ChevronLeft, ChevronRight, ArrowUpDown } from 'lucide-react';
import { api } from '../services/api';
import { Board, Quality } from '../types/board';
import { QualityBadge } from '../components/QualityBadge';
import { EditBoardModal } from '../components/EditBoardModal';
import { toast } from 'sonner';
import { BoardVisualizationModal } from '../components/BoardVisualizationModal';
import { MapPin } from 'lucide-react';

export function BoardsList() {
  const [visualizeBoard, setVisualizeBoard] = useState<Board | null>(null);
  const [boards, setBoards] = useState<Board[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [editingBoard, setEditingBoard] = useState<Board | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const [search, setSearch] = useState('');
  const [qualityFilter, setQualityFilter] = useState<Quality | ''>('');
  const [sortBy, setSortBy] = useState<'quality' | 'date' | 'defects'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const [limit] = useState(20);

  useEffect(() => {
    loadBoards();
  }, [search, qualityFilter, sortBy, sortOrder, page]);

  const loadBoards = async () => {
    setLoading(true);
    try {
      const data = await api.getBoards({
        search,
        quality: qualityFilter || undefined,
        sortBy,
        sortOrder,
        page,
        limit
      });
      setBoards(data.boards);
      setTotal(data.total);
    } catch (error) {
      console.error('Error loading boards:', error);
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async (updates: Partial<Board>) => {
    if (!editingBoard) return;

    try {
      await api.updateBoard(editingBoard.board_id, updates);
      toast.success('Доска обновлена');
      setEditingBoard(null);
      loadBoards();
    } catch (error) {
      console.error('Error updating board:', error);
      toast.error('Ошибка обновления');
    }
  };

  const handleDelete = async (boardId: string) => {
    try {
      await api.deleteBoard(boardId);
      toast.success('Доска удалена');
      setDeleteConfirm(null);
      loadBoards();
    } catch (error) {
      console.error('Error deleting board:', error);
      toast.error('Ошибка удаления');
    }
  };

  const toggleSort = (field: 'quality' | 'date' | 'defects') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Все доски</h1>
              <p className="text-gray-600">Управление и мониторинг досок</p>
            </div>
            <Link
              to="/"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              ← Дашборд
            </Link>
          </div>

          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Поиск по ID..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <select
                value={qualityFilter}
                onChange={(e) => {
                  setQualityFilter(e.target.value as Quality | '');
                  setPage(1);
                }}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Все качества</option>
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
                <option value="D">D</option>
              </select>

              <button
                onClick={() => {
                  setSearch('');
                  setQualityFilter('');
                  setSortBy('date');
                  setSortOrder('desc');
                  setPage(1);
                }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 flex items-center justify-center gap-2"
              >
                <Filter className="w-4 h-4" />
                Сбросить
              </button>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border border-gray-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID Доски
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => toggleSort('quality')}
                  >
                    <div className="flex items-center gap-1">
                      Качество
                      {sortBy === 'quality' && <ArrowUpDown className="w-3 h-3" />}
                    </div>
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => toggleSort('defects')}
                  >
                    <div className="flex items-center gap-1">
                      Дефектов
                      {sortBy === 'defects' && <ArrowUpDown className="w-3 h-3" />}
                    </div>
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => toggleSort('date')}
                  >
                    <div className="flex items-center gap-1">
                      Дата и время
                      {sortBy === 'date' && <ArrowUpDown className="w-3 h-3" />}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Типы дефектов
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                      Загрузка...
                    </td>
                  </tr>
                ) : boards.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                      Нет досок по заданным фильтрам
                    </td>
                  </tr>
                ) : (
                  boards.map((board) => (
                    <tr key={board.board_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {board.board_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <QualityBadge quality={board.quality} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-sm ${board.defects.length > 0 ? 'text-red-600 font-medium' : 'text-gray-500'}`}>
                          {board.defects.length}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(board.timestamp).toLocaleString('ru-RU')}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {board.defects.length > 0 ? (
                          <div className="max-w-xs">
                            {board.defects.map((d, i) => (
                              <span key={i}>
                                {d.defect_type}
                                {i < board.defects.length - 1 ? ', ' : ''}
                              </span>
                            ))}
                          </div>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => setVisualizeBoard(board)}
                          className="text-indigo-600 hover:text-indigo-900 inline-flex items-center gap-1"
                        >
                          <MapPin className="w-4 h-4" />
                          Схема
                        </button>
                        {/* <button
                          onClick={() => setEditingBoard(board)}
                          className="text-blue-600 hover:text-blue-900 mr-4 inline-flex items-center gap-1"
                        >
                          <Edit2 className="w-4 h-4" />
                          Редактировать
                        </button>
                        {deleteConfirm === board.board_id ? (
                          <div className="inline-flex items-center gap-2">
                            <button
                              onClick={() => handleDelete(board.board_id)}
                              className="text-red-600 hover:text-red-900"
                            >
                              Подтвердить
                            </button>
                            <button
                              onClick={() => setDeleteConfirm(null)}
                              className="text-gray-600 hover:text-gray-900"
                            >
                              Отмена
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setDeleteConfirm(board.board_id)}
                            className="text-red-600 hover:text-red-900 inline-flex items-center gap-1"
                          >
                            <Trash2 className="w-4 h-4" />
                            Удалить
                          </button>
                        )} */}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Показано <span className="font-medium">{(page - 1) * limit + 1}</span> -{' '}
                <span className="font-medium">{Math.min(page * limit, total)}</span> из{' '}
                <span className="font-medium">{total}</span> досок
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <span className="text-sm text-gray-700">
                  Страница {page} из {totalPages}
                </span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page === totalPages}
                  className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {editingBoard && (
        <EditBoardModal
          board={editingBoard}
          onClose={() => setEditingBoard(null)}
          onSave={handleEdit}
        />
      )}
      {visualizeBoard && (
  <BoardVisualizationModal
    board={visualizeBoard}
    onClose={() => setVisualizeBoard(null)}
  />
)}
    </div>
  );
}
