import { useEffect, useState } from 'react';
import { Header } from '../components/Header';
import { getEvaluationSummary } from '../services/api';
import type { EvaluationSummary } from '../types/api';
import { ShieldCheck, Crosshair, BarChart2 } from 'lucide-react';

export const Overview: React.FC = () => {
  const [data, setData] = useState<EvaluationSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getEvaluationSummary().then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-8 text-slate-500">Loading overview data...</div>;
  }

  if (!data || !data.intent_metrics) {
    return (
      <div className="flex-1 flex flex-col h-full bg-slate-50">
        <Header title="AI Support Operations" description="Monitor AI-assisted customer support performance." />
        <div className="p-8 text-slate-500 text-center mt-20">
          <p className="text-lg">No evaluation data available.</p>
          <p className="text-sm">Run the offline evaluation pipeline first to generate results.</p>
        </div>
      </div>
    );
  }

  const { intent_metrics, escalation_metrics, reply_quality } = data;

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-auto">
      <Header title="AI Support Operations" description="Monitor AI-assisted customer support performance." />
      
      <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
        
        {/* Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-brand-50 text-brand-600 rounded-full"><Crosshair size={24} /></div>
            <div>
              <div className="text-sm text-slate-500 font-medium">Intent Accuracy</div>
              <div className="text-2xl font-bold text-slate-800">{(intent_metrics.accuracy * 100).toFixed(1)}%</div>
            </div>
          </div>
          
          <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-brand-50 text-brand-600 rounded-full"><BarChart2 size={24} /></div>
            <div>
              <div className="text-sm text-slate-500 font-medium">Macro F1 Score</div>
              <div className="text-2xl font-bold text-slate-800">{(intent_metrics.macro_f1 * 100).toFixed(1)}%</div>
            </div>
          </div>
          
          <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-green-50 text-green-600 rounded-full"><ShieldCheck size={24} /></div>
            <div>
              <div className="text-sm text-slate-500 font-medium">AUTO_HANDLE Rate</div>
              <div className="text-2xl font-bold text-slate-800">
                {escalation_metrics ? (escalation_metrics.AUTO_HANDLE_rate * 100).toFixed(1) + '%' : 'N/A'}
              </div>
            </div>
          </div>

          <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-blue-50 text-blue-600 rounded-full"><BarChart2 size={24} /></div>
            <div>
              <div className="text-sm text-slate-500 font-medium">Reply Helpfulness</div>
              <div className="text-2xl font-bold text-slate-800">
                {reply_quality && reply_quality.helpfulness ? (reply_quality.helpfulness * 100).toFixed(1) + '%' : 'N/A'}
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm mt-8">
          <h3 className="text-lg font-semibold text-slate-800 mb-2">Welcome to Hiver AI Support</h3>
          <p className="text-slate-600 mb-4">
            This dashboard monitors the offline-evaluated performance of the agent pipeline.
            To view detailed metrics, check the <strong>Analytics</strong> and <strong>Evaluation</strong> pages.
            To test the system live, visit the <strong>Support Agent</strong> workspace.
          </p>
        </div>
      </div>
    </div>
  );
};
