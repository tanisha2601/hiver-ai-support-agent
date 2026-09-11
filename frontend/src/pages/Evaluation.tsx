import { useEffect, useState } from 'react';
import { Header } from '../components/Header';
import { getEvaluationSummary } from '../services/api';
import type { EvaluationSummary } from '../types/api';
import { AlertTriangle } from 'lucide-react';

export const Evaluation: React.FC = () => {
  const [data, setData] = useState<EvaluationSummary | null>(null);

  useEffect(() => {
    getEvaluationSummary().then(setData).catch(console.error);
  }, []);

  if (!data || !data.intent_metrics) return <div className="p-8">Loading...</div>;

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-auto">
      <Header title="Model Evaluation" description="Comprehensive performance metrics." />
      
      <div className="p-8 max-w-5xl mx-auto w-full space-y-8">
        
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-md flex gap-3 text-amber-800 text-sm">
          <AlertTriangle size={20} className="shrink-0" />
          <div>
            <strong>Methodology Warning:</strong> The evaluation labels are AI-assisted stratified evaluation labels rather than manually verified human labels. The weak-supervision TF-IDF baseline should not be interpreted as human-validated accuracy.
          </div>
        </div>

        <section>
          <h2 className="text-xl font-semibold text-slate-800 mb-4 border-b pb-2">Intent Classification</h2>
          <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-slate-800 font-medium border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Model</th>
                  <th className="py-3 px-4">Accuracy</th>
                  <th className="py-3 px-4">Macro F1</th>
                  <th className="py-3 px-4">Weighted F1</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-4">Majority Baseline</td>
                  <td className="py-3 px-4">{data.majority_metrics ? (data.majority_metrics.accuracy * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="py-3 px-4">{data.majority_metrics && data.majority_metrics.macro_f1 ? (data.majority_metrics.macro_f1 * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="py-3 px-4">{data.majority_metrics && data.majority_metrics.weighted_f1 ? (data.majority_metrics.weighted_f1 * 100).toFixed(2) + '%' : 'N/A'}</td>
                </tr>
                <tr className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-4">TF-IDF + Logistic Regression</td>
                  <td className="py-3 px-4">{data.tfidf_metrics ? (data.tfidf_metrics.accuracy * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="py-3 px-4">{data.tfidf_metrics && data.tfidf_metrics.macro_f1 ? (data.tfidf_metrics.macro_f1 * 100).toFixed(2) + '%' : 'N/A'}</td>
                  <td className="py-3 px-4">{data.tfidf_metrics && data.tfidf_metrics.weighted_f1 ? (data.tfidf_metrics.weighted_f1 * 100).toFixed(2) + '%' : 'N/A'}</td>
                </tr>
                <tr className="hover:bg-slate-50 font-medium text-brand-700 bg-brand-50/30">
                  <td className="py-3 px-4">Final Agent</td>
                  <td className="py-3 px-4">{(data.intent_metrics.accuracy * 100).toFixed(2)}%</td>
                  <td className="py-3 px-4">{(data.intent_metrics.macro_f1 * 100).toFixed(2)}%</td>
                  <td className="py-3 px-4">{(data.intent_metrics.weighted_f1 * 100).toFixed(2)}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-slate-800 mb-4 border-b pb-2">Reply Quality</h2>
          <p className="text-sm text-slate-500 mb-4 italic">Note: These metrics are based on Heuristic evaluation / LLM-as-judge evaluation proxies depending on configuration.</p>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {['relevance', 'grounding', 'helpfulness', 'unsupported_claims', 'tone'].map(key => {
              const val = data.reply_quality?.[key];
              return (
                <div key={key} className="bg-white p-4 rounded border border-slate-200 shadow-sm">
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">{key.replace('_', ' ')}</div>
                  <div className="text-xl font-bold text-slate-800">{val !== undefined ? (val * 100).toFixed(1) + '%' : 'N/A'}</div>
                </div>
              );
            })}
          </div>
        </section>

      </div>
    </div>
  );
};
