export type Quality = 'A' | 'B' | 'C' | 'D';

export type DefectSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface Defect {
  id: string;
  defect_type: string;
  severity: DefectSeverity;
  location: string;
}

export interface DashboardMetrics {
  totalBoards: number;
  avgProcessingDuration: number;
  qualityDistribution: {
    A: number;
    B: number;
    C: number;
    D: number;
  };
  totalDefects: number;
  topDefects: {
    type: string;
    count: number;
  }[];
  boardsByHour: {
    hour: string;
    count: number;
  }[];
}

export interface CuttingSegment {
  from_mm: number;
  to_mm: number;
  grade: string;
  length_m: number;
  price: number;
}

export interface CuttingPlan {
  board_id: string;
  segments: CuttingSegment[];
  total_revenue: number;
  algorithm: string;
}

export interface Board {
  board_id: string;
  quality: Quality;
  defects: Defect[];
  timestamp: string;
  processing_duration: number;
  total_length_mm: number;
  cutting_plan?: CuttingPlan; // опционально, т.к. может быть не рассчитан
}
