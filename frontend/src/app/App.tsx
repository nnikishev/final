import { BrowserRouter, Routes, Route } from 'react-router';
import { Toaster } from 'sonner';
import { Dashboard } from './pages/Dashboard';
import { BoardsList } from './pages/BoardsList';

export default function App() {
  return (
    <BrowserRouter>
      <div className="size-full">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/boards" element={<BoardsList />} />
        </Routes>
        <Toaster position="top-right" />
      </div>
    </BrowserRouter>
  );
}