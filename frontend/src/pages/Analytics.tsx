import { useEffect, useState } from 'react';
import { Header } from '../components/Header';
import { getEvaluationSummary } from '../services/api';
import type { EvaluationSummary } from '../types/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { AlertTriangle } from 'lucide-react';

const COLORS = ['#14b8a6', '#0d9488', '#134e4a', '#ccfbf1', '#0f766e', '#042f2e'];
const DECISION_COLORS = { 'AUTO_HANDLE': '#10b981', 'ESCALATE': '#ef4444' };
const GROUNDING_COLORS = { 'STRONG': '#10b981', 'MODERATE': '#f59e0b', 'WEAK': '#f97316', 'NONE': '#ef4444' };

export const Analytics: React.FC = () => {
  const [data, setData] = useState<EvaluationSummary | null>(null);

  useEffect(() => {
    getEvaluationSummary().then(setData).catch(console.error);
  }, []);

  if (!data) return <div className="p-8 text-slate-500">Loading analytics...</div>;

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-auto">
      <Header title="Analytics Dashboard" description="Deep dive into pipeline distributions and decisions." />
      
      <div className="p-8 max-w-7xl mx-auto w-full space-y-8">
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Intent Distribution */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm flex flex-col">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Predicted Intent Distribution</h3>
            <div className="flex-1 min-h-75">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.intent_distribution} layout="vertical" margin={{ left: 50, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={120} tick={{fontSize: 10}} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#0d9488" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Actual Intent Distribution */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm flex flex-col">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Actual (AI-Assisted) Intent Distribution</h3>
            <div className="flex-1 min-h-75">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.true_intent_distribution} layout="vertical" margin={{ left: 50, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={120} tick={{fontSize: 10}} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#14b8a6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Decisions */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm flex flex-col">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Escalation Decisions</h3>
            <div className="flex-1 min-h-62.5 flex justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.decision_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    label={({name, percent}) => percent ? `${name} ${(percent * 100).toFixed(0)}%` : name}
                  >
                    {data.decision_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={DECISION_COLORS[entry.name as keyof typeof DECISION_COLORS] || COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Grounding */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm flex flex-col">
            <h3 className="text-lg font-semibold text-slate-800 mb-1">Grounding Quality Distribution</h3>
            <p className="text-xs text-slate-500 mb-4">
              Note: The high concentration of WEAK/NONE is due to hybrid cosine similarity thresholds (&gt;0.5) against short tweets.
            </p>
            <div className="flex-1 min-h-62.5 flex justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.grounding_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    label={({name, percent}) => percent ? `${name} ${(percent * 100).toFixed(0)}%` : name}
                  >
                    {data.grounding_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={GROUNDING_COLORS[entry.name as keyof typeof GROUNDING_COLORS] || COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Confidence */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm flex flex-col">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Intent Confidence Distribution</h3>
            <div className="flex-1 min-h-62.5">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.confidence_distribution}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{fontSize: 12}} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Failures */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm flex flex-col">
            <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
              <AlertTriangle size={20} className="text-amber-500" /> Top Failure Modes
            </h3>
            <div className="flex-1 min-h-62.5">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.failure_distribution} layout="vertical" margin={{ left: 10, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={180} tick={{fontSize: 11}} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#ef4444" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
