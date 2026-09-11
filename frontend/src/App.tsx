import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { SupportAgent } from './pages/SupportAgent';
import { Overview } from './pages/Overview';
import { Evaluation } from './pages/Evaluation';
import { Failures } from './pages/Failures';
import { Conversations } from './pages/Conversations';
import { Analytics } from './pages/Analytics';
import { Retrieval } from './pages/Retrieval';
import { System } from './pages/System';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Overview />} />
          <Route path="agent" element={<SupportAgent />} />
          <Route path="conversations" element={<Conversations />} />
          <Route path="evaluation" element={<Evaluation />} />
          <Route path="failures" element={<Failures />} />
          <Route path="retrieval" element={<Retrieval />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="system" element={<System />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
