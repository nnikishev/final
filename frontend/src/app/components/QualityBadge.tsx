import { Quality } from '../types/board';

interface QualityBadgeProps {
  quality: Quality;
}

const qualityColors: Record<Quality, string> = {
  A: 'bg-green-100 text-green-800 border-green-200',
  B: 'bg-blue-100 text-blue-800 border-blue-200',
  C: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  D: 'bg-red-100 text-red-800 border-red-200'
};

export function QualityBadge({ quality }: QualityBadgeProps) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium border ${qualityColors[quality]}`}>
      {quality}
    </span>
  );
}
