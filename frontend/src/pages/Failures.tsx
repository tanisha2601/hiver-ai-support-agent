import { useEffect, useState } from 'react';
import { Header } from '../components/Header';
import { getFailures } from '../services/api';
import type { FailureMode } from '../types/api';
import { ShieldAlert, AlertTriangle } from 'lucide-react';

export const Failures: React.FC = () => {
  const [failures, setFailures] = useState<FailureMode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getFailures().then(setFailures).finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-auto">
      <Header title="Top Failure Modes" description="Analysis of system errors and limitations." />
      
      <div className="p-8 max-w-4xl mx-auto w-full space-y-6">
        
        {loading ? (
          <div className="text-slate-500">Loading failure analysis...</div>
        ) : failures.length === 0 ? (
          <div className="text-slate-500">No failures recorded.</div>
        ) : (
          <div className="space-y-4">
            {failures.map((f, i) => (
              <div key={i} className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
                <div className="bg-red-50 px-6 py-4 border-b border-red-100 flex justify-between items-center">
                  <h3 className="font-semibold text-red-800 flex items-center gap-2">
                    <ShieldAlert size={18} /> {f['Failure name']}
                  </h3>
                  <span className="bg-red-100 text-red-800 text-xs font-bold px-2 py-1 rounded">
                    {f['Number of affected examples']} examples
                  </span>
                </div>
                <div className="p-6 space-y-4 text-sm text-slate-700">
                  <div>
                    <span className="font-semibold text-slate-900 block mb-1">Example</span>
                    <div className="bg-slate-50 p-3 rounded border border-slate-200 font-mono text-xs">
                      {f.Example}
                    </div>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-900 mb-1 flex items-center gap-2">
                      <AlertTriangle size={16} className="text-amber-500" /> Why the system failed
                    </span>
                    <p>{f['Why the system failed']}</p>
                  </div>
                  <div className="pt-2 border-t border-slate-100">
                    <span className="font-semibold text-slate-900 block mb-1">Proposed improvement</span>
                    <p className="text-brand-700">{f['Proposed improvement']}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
