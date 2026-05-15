import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { Package, Clock, AlertCircle, CheckCircle, Video, VideoOff, Loader2, X } from 'lucide-react';
import { api } from '../services/api';
import { DashboardMetrics, Board } from '../types/board';
import { MetricCard } from '../components/MetricCard';
import { QualityBadge } from '../components/QualityBadge';

const QUALITY_COLORS = {
  A: '#10b981',
  B: '#3b82f6',
  C: '#f59e0b',
  D: '#ef4444'
};

export function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [recentBoards, setRecentBoards] = useState<Board[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Состояние для управления камерой
  const [cameraStatus, setCameraStatus] = useState<'running' | 'stopped' | 'unknown'>('unknown');
  const [cameraActionLoading, setCameraActionLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [cameraId, setCameraId] = useState('Конвейнер');
  const [rtspUrl, setRtspUrl] = useState('rtsp://mediamtx:8554/conveyor');

  useEffect(() => {
    loadData();
    loadCameraStatus();
    const interval = setInterval(loadData, 30000);
    const statusInterval = setInterval(loadCameraStatus, 5000);
    return () => {
      clearInterval(interval);
      clearInterval(statusInterval);
    };
  }, []);

  const loadData = async () => {
    try {
      setError(null);
      const [metricsData, boardsData] = await Promise.all([
        api.getDashboardMetrics(),
        api.getBoards({ limit: 10 })
      ]);
      setMetrics(metricsData);
      setRecentBoards(boardsData.boards);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError('Не удалось загрузить данные дашборда. Проверьте доступность backend.');
    } finally {
      setLoading(false);
    }
  };

  const loadCameraStatus = async () => {
    try {
      const status = await api.getCameraStatus();
      setCameraStatus(status.is_running ? 'running' : 'stopped');
    } catch (err) {
      console.warn('Failed to load camera status:', err);
      setCameraStatus('unknown');
    }
  };

  const handleOpenModal = () => {
    setIsModalOpen(true);
  };

  const handleStartCameraWithParams = async () => {
    if (!cameraId.trim() || !rtspUrl.trim()) {
      alert('Заполните оба поля');
      return;
    }
    setCameraActionLoading(true);
    try {
      await api.startCamera({ camera_id: cameraId, rtsp_url: rtspUrl });
      setCameraStatus('running');
      setIsModalOpen(false);
    } catch (err) {
      console.error('Failed to start camera:', err);
      alert('Ошибка запуска камеры. Проверьте настройки RTSP.');
    } finally {
      setCameraActionLoading(false);
    }
  };

  const handleStopCamera = async () => {
    setCameraActionLoading(true);
    try {
      await api.stopCamera();
      setCameraStatus('stopped');
    } catch (err) {
      console.error('Failed to stop camera:', err);
      alert('Ошибка остановки камеры.');
    } finally {
      setCameraActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">Загрузка...</div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 py-10">
          <div className="bg-white border border-red-200 text-red-700 rounded-lg p-4">
            {error || 'Нет данных для отображения дашборда.'}
          </div>
        </div>
      </div>
    );
  }

  const qualityData = [
    { name: 'A', value: metrics.qualityDistribution.A, color: QUALITY_COLORS.A },
    { name: 'B', value: metrics.qualityDistribution.B, color: QUALITY_COLORS.B },
    { name: 'C', value: metrics.qualityDistribution.C, color: QUALITY_COLORS.C },
    { name: 'D', value: metrics.qualityDistribution.D, color: QUALITY_COLORS.D }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Панель мониторинга качества</h1>
            <p className="text-gray-600">Обзор производственных показателей</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-2 bg-white rounded-lg shadow-sm border border-gray-200">
              {cameraStatus === 'running' ? (
                <Video className="w-4 h-4 text-green-600" />
              ) : (
                <VideoOff className="w-4 h-4 text-gray-500" />
              )}
              <span className="text-sm font-medium">
                Камера: {cameraStatus === 'running' ? 'Активна' : cameraStatus === 'stopped' ? 'Остановлена' : 'Неизвестно'}
              </span>
            </div>
            <button
              onClick={handleOpenModal}
              disabled={cameraActionLoading || cameraStatus === 'running'}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white rounded-lg shadow-sm flex items-center gap-2 transition"
            >
              {cameraActionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Video className="w-4 h-4" />}
              Запустить камеру
            </button>
            <button
              onClick={handleStopCamera}
              disabled={cameraActionLoading || cameraStatus === 'stopped'}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white rounded-lg shadow-sm flex items-center gap-2 transition"
            >
              {cameraActionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <VideoOff className="w-4 h-4" />}
              Остановить камеру
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Всего досок"
            value={metrics.totalBoards}
            icon={Package}
            color="bg-blue-500"
          />
          <MetricCard
            title="Среднее время (сек)"
            value={metrics.avgProcessingDuration.toFixed(1)}
            icon={Clock}
            color="bg-purple-500"
          />
          <MetricCard
            title="Всего дефектов"
            value={metrics.totalDefects}
            icon={AlertCircle}
            color="bg-orange-500"
          />
          <MetricCard
            title="Качество A"
            value={metrics.qualityDistribution.A}
            icon={CheckCircle}
            color="bg-green-500"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Распределение качества</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={qualityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {qualityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Топ-5 типов дефектов</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={metrics.topDefects} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="type" type="category" width={120} />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border border-gray-200 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Доски по часам</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={metrics.boardsByHour}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Последние 10 досок</h2>
            <Link to="/boards" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
              Все доски →
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID Доски
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Качество
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Дефектов
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Время
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Типы дефектов
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentBoards.map((board) => (
                  <tr key={board.board_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {board.board_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <QualityBadge quality={board.quality} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {board.defects.length}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(board.timestamp).toLocaleString('ru-RU')}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {board.defects.length > 0
                        ? board.defects.slice(0, 2).map(d => d.defect_type).join(', ') +
                          (board.defects.length > 2 ? '...' : '')
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Модальное окно */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Подключение к камере</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Название камеры (ID)</label>
                <input
                  type="text"
                  value={cameraId}
                  onChange={(e) => setCameraId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  placeholder="например: front_camera"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">RTSP-адрес</label>
                <input
                  type="text"
                  value={rtspUrl}
                  onChange={(e) => setRtspUrl(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  placeholder="rtsp://ip:port/stream"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
                >
                  Отмена
                </button>
                <button
                  onClick={handleStartCameraWithParams}
                  disabled={cameraActionLoading}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition disabled:opacity-50"
                >
                  {cameraActionLoading ? 'Подключение...' : 'Подключиться'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}