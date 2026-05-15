import { Board, DashboardMetrics, Quality } from '../types/board';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const CV_BASE_URL = import.meta.env.VITE_CV_API_URL || 'http://localhost:8002';

const getJson = async <T>(url: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(url, init);
  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(errorBody || `Request failed: ${response.status}`);
  }
  return response.json();
};

export const api = {
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    return getJson<DashboardMetrics>(`${BASE_URL}/lining-board/frontend/metrics`);
  },

  async getBoards(params?: {
    search?: string;
    quality?: Quality;
    sortBy?: 'quality' | 'date' | 'defects';
    sortOrder?: 'asc' | 'desc';
    page?: number;
    limit?: number;
  }): Promise<{ boards: Board[]; total: number }> {
    const query = new URLSearchParams();
    if (params?.search) query.set('search', params.search);
    if (params?.quality) query.set('quality', params.quality);
    if (params?.sortBy) query.set('sort_by', params.sortBy);
    if (params?.sortOrder) query.set('sort_order', params.sortOrder);
    query.set('page', String(params?.page || 1));
    query.set('limit', String(params?.limit || 20));

    return getJson<{ boards: Board[]; total: number }>(
      `${BASE_URL}/lining-board/frontend/boards?${query.toString()}`
    );
  },

  async getBoard(boardId: string): Promise<Board | null> {
    const result = await this.getBoards({ search: boardId, page: 1, limit: 1 });
    return result.boards.find((board) => board.board_id === boardId) || null;
  },

  async updateBoard(boardId: string, updates: Partial<Board>): Promise<Board> {
    const boardNumber = Number(boardId.replace('BOARD-', ''));
    const payload: Record<string, unknown> = {};
    if (updates.quality) payload.quality = updates.quality;
    if (updates.defects) {
      const defectCounts: Record<string, number> = {};
      updates.defects.forEach((defect) => {
        defectCounts[defect.defect_type] = (defectCounts[defect.defect_type] || 0) + 1;
      });
      payload.defect_counts = defectCounts;
      payload.total_defects = updates.defects.length;
    }

    await getJson<{ status: string }>(`${BASE_URL}/lining-board/${boardNumber}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const refreshed = await this.getBoard(boardId);
    if (!refreshed) throw new Error('Board not found');
    return refreshed;
  },

  async deleteBoard(boardId: string): Promise<void> {
    const boardNumber = Number(boardId.replace('BOARD-', ''));
    await getJson<{ status: string }>(`${BASE_URL}/lining-board/${boardNumber}`, {
      method: 'DELETE'
    });
  },

  // === Управление RTSP-камерой (CV-сервис) ===
  async startCamera(data: { camera_id: string; rtsp_url: string }): Promise<{ status: string; camera_id: string }> {
    return getJson<{ status: string; camera_id: string }>(`${CV_BASE_URL}/camera/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },

  async stopCamera(): Promise<{ status: string }> {
    return getJson<{ status: string }>(`${CV_BASE_URL}/camera/stop`, {
      method: 'POST'
    });
  },

  async getCameraStatus(): Promise<{
    is_running: boolean;
    camera_id?: string;
    boards_processed?: number;
    total_defects_detected?: number;
  }> {
    return getJson(`${CV_BASE_URL}/camera/status`);
  }
};