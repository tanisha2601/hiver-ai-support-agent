import { useEffect, useState } from 'react';
import { Header } from '../components/Header';
import { getHealth } from '../services/api';
import type { HealthStatus } from '../types/api';
import { Server, Database, BrainCircuit, Activity } from 'lucide-react';

export const System: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(console.error);
  }, []);

  if (!health) {
    return <div className="p-8 text-slate-500 flex items-center gap-2"><Activity className="animate-spin" /> Loading system status...</div>;
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-auto">
      <Header title="System Health & Config" description="Monitor API status and agent configurations." />
      
      <div className="p-8 max-w-4xl mx-auto w-full space-y-6">
        
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-2">
            <Server size={18} className="text-slate-500" />
            <h2 className="font-semibold text-slate-800">API Status</h2>
          </div>
          <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatusItem label="API Server" status={health.status} />
            <StatusItem label="Agent Runtime" status={health.agent} />
            <StatusItem label="Retrieval Engine" status={health.retrieval} />
            <StatusItem label="Response Generator" status={health.generation} />
          </div>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-2">
            <Database size={18} className="text-slate-500" />
            <h2 className="font-semibold text-slate-800">Data & Evaluation</h2>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="text-sm text-slate-500 mb-1">Dataset</div>
              <div className="font-medium text-slate-800">{health.dataset}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">Evaluation Data</div>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${health.evaluation_data === 'available' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                <span className="font-medium text-slate-800 capitalize">{health.evaluation_data}</span>
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">Evaluation Examples</div>
              <div className="font-medium text-slate-800">200</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-2">
            <BrainCircuit size={18} className="text-slate-500" />
            <h2 className="font-semibold text-slate-800">Model Configuration</h2>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="text-sm text-slate-500 mb-1">Retrieval Methodology</div>
              <div className="font-medium text-slate-800">{health.retrieval_type}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">Embedding Model</div>
              <div className="font-medium text-slate-800">{health.embedding_model}</div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

const StatusItem = ({ label, status }: { label: string, status: string }) => {
  const isOk = ['ok', 'ready', 'online'].includes(status.toLowerCase());
  return (
    <div className="p-4 rounded border border-slate-100 bg-slate-50 flex flex-col items-center justify-center text-center">
      <div className={`w-3 h-3 rounded-full mb-2 ${isOk ? 'bg-green-500' : 'bg-red-500'}`}></div>
      <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">{label}</div>
      <div className="font-semibold text-slate-800 capitalize">{status}</div>
    </div>
  );
};
