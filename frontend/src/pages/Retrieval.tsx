import { useEffect, useState } from 'react';
import { Header } from '../components/Header';
import { getEvaluationSummary } from '../services/api';
import type { EvaluationSummary } from '../types/api';
import { Search, GitMerge, FileText, Database } from 'lucide-react';

export const Retrieval: React.FC = () => {
  const [data, setData] = useState<EvaluationSummary | null>(null);

  useEffect(() => {
    getEvaluationSummary().then(setData).catch(console.error);
  }, []);

  if (!data) return <div className="p-8 text-slate-500">Loading retrieval metrics...</div>;

  const rm = data.retrieval_metrics;

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-auto">
      <Header title="Retrieval Engine" description="Analyze the Hybrid Search implementation and evidence grounding." />
      
      <div className="p-8 max-w-5xl mx-auto w-full space-y-8">
        
        {/* Architecture Section */}
        <section>
          <h2 className="text-xl font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Search size={22} className="text-brand-600" />
            Hybrid Retrieval Architecture
          </h2>
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6 text-center text-sm font-medium">
              <div className="flex-1 w-full bg-slate-50 p-4 rounded border border-slate-200">
                <FileText size={24} className="mx-auto text-blue-500 mb-2" />
                <div>Customer Query</div>
              </div>
              
              <div className="flex flex-col gap-4 text-slate-400">
                <span>→</span>
                <span>→</span>
              </div>
              
              <div className="flex-1 w-full space-y-4">
                <div className="bg-slate-50 p-4 rounded border border-slate-200 relative">
                  <div className="text-xs text-slate-500 uppercase mb-1">TF-IDF Vectorizer</div>
                  <div className="text-brand-600">Lexical Match Score</div>
                </div>
                <div className="bg-slate-50 p-4 rounded border border-slate-200 relative">
                  <div className="text-xs text-slate-500 uppercase mb-1">all-MiniLM-L6-v2</div>
                  <div className="text-brand-600">Semantic Cosine Score</div>
                </div>
              </div>
              
              <div className="text-slate-400">→</div>
              
              <div className="flex-1 w-full bg-slate-50 p-4 rounded border border-slate-200 relative">
                <GitMerge size={24} className="mx-auto text-purple-500 mb-2" />
                <div className="text-xs text-slate-500 uppercase mb-1">Normalization</div>
                <div className="text-slate-800">Hybrid Average Score</div>
              </div>
              
              <div className="text-slate-400">→</div>
              
              <div className="flex-1 w-full bg-brand-50 p-4 rounded border border-brand-200 text-brand-800">
                <Database size={24} className="mx-auto mb-2" />
                <div>Top K Historical Conversations</div>
              </div>
            </div>
          </div>
        </section>

        {/* Metrics Section */}
        {rm ? (
          <section>
            <h2 className="text-xl font-semibold text-slate-800 mb-4">Retrieval Performance</h2>
            <p className="text-sm text-slate-500 mb-4 italic">Measured via "Intent-match proxy" - does the retrieved historical response share the same underlying intent as the query?</p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <MetricCard title="Intent-match @1" value={rm.intent_match_at_1} />
              <MetricCard title="Intent-match @3" value={rm.intent_match_at_3} />
              <MetricCard title="Intent-match @5" value={rm.intent_match_at_5} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex justify-between items-center">
                <div className="text-sm font-medium text-slate-600">Average Hybrid Similarity</div>
                <div className="text-lg font-bold text-slate-800">{rm.average_similarity?.toFixed(3)}</div>
              </div>
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex justify-between items-center">
                <div className="text-sm font-medium text-slate-600">Median Hybrid Similarity</div>
                <div className="text-lg font-bold text-slate-800">{rm.median_similarity?.toFixed(3)}</div>
              </div>
            </div>
          </section>
        ) : (
          <div className="p-4 bg-amber-50 text-amber-800 rounded border border-amber-200">
            Retrieval metrics not available in results.
          </div>
        )}

      </div>
    </div>
  );
};

const MetricCard = ({ title, value }: { title: string, value: number }) => (
  <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm text-center">
    <div className="text-sm font-medium text-slate-500 mb-2">{title}</div>
    <div className="text-3xl font-bold text-brand-600">{(value * 100).toFixed(1)}%</div>
  </div>
);
