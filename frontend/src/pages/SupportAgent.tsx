import { useState } from 'react';
import { Header } from '../components/Header';
import { runAgent } from '../services/api';
import type { AgentResult } from '../types/api';
import { Send, CheckCircle, AlertTriangle, Info, RefreshCw, Layers, Zap, MessageSquare } from 'lucide-react';

export const SupportAgent: React.FC = () => {
  const [message, setMessage] = useState('');
  const [context, setContext] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!message.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await runAgent({ message, context });
      setResult(res);
    } catch (err) {
      setError('Failed to reach backend API. Ensure the FastAPI server is running.');
    } finally {
      setLoading(false);
    }
  };

  const getEscalationColor = (decision: string) => {
    if (decision === 'AUTO_HANDLE') return 'text-green-600 bg-green-50 border-green-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50">
      <Header title="Support Agent" description="Analyze, ground, and route customer requests." />
      
      <div className="flex-1 overflow-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full max-w-7xl mx-auto">
          
          {/* LEFT PANEL: Input */}
          <div className="flex flex-col gap-4">
            <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex-1 flex flex-col">
              <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                <MessageSquareIcon /> Customer Conversation
              </h2>
              
              <div className="space-y-4 flex-1">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Customer Message</label>
                  <textarea 
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Where is my package? It was supposed to arrive yesterday."
                    className="w-full h-32 p-3 border border-slate-300 rounded-md focus:ring-brand-500 focus:border-brand-500 outline-none resize-none"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Previous Context (Optional)</label>
                  <textarea 
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    placeholder="User placed order #1234 on Monday..."
                    className="w-full h-24 p-3 border border-slate-300 rounded-md focus:ring-brand-500 focus:border-brand-500 outline-none resize-none text-slate-600 text-sm"
                  />
                </div>
              </div>
              
              <button 
                onClick={handleAnalyze}
                disabled={loading || !message.trim()}
                className="mt-4 w-full bg-brand-600 hover:bg-brand-700 text-white font-medium py-2.5 px-4 rounded-md transition-colors flex justify-center items-center gap-2 disabled:opacity-50"
              >
                {loading ? <RefreshCw className="animate-spin" size={18} /> : <Send size={18} />}
                {loading ? 'Analyzing...' : 'Analyze Request'}
              </button>
              
              {error && (
                <div className="mt-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded text-sm">
                  {error}
                </div>
              )}
            </div>
          </div>
          
          {/* CENTER PANEL: Response */}
          <div className="flex flex-col gap-4">
            <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex-1 flex flex-col">
              <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                <Zap className="text-brand-500" size={20} /> Suggested Response
              </h2>
              
              {!result && !loading && (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-lg p-6 text-center">
                  <MessageSquareIcon size={48} className="mb-4 opacity-50" />
                  <p>No customer request analyzed yet.</p>
                  <p className="text-sm mt-1">Enter a message to see the AI response.</p>
                </div>
              )}
              
              {loading && (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
                  <RefreshCw className="animate-spin text-brand-500 mb-4" size={32} />
                  <p className="font-medium animate-pulse">Running AI Pipeline...</p>
                  <div className="text-sm mt-2 text-slate-400 space-y-1 text-center">
                    <p>Classifying intent...</p>
                    <p>Finding historical evidence...</p>
                    <p>Generating response...</p>
                  </div>
                </div>
              )}
              
              {result && !loading && (
                <div className="flex-1 flex flex-col">
                  <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 flex-1 text-slate-800 whitespace-pre-wrap">
                    {result.response}
                  </div>
                  
                  <div className="mt-6 border-t border-slate-100 pt-4">
                    <h3 className="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
                      <Layers size={16} /> Historical Support Evidence
                    </h3>
                    <div className="space-y-3">
                      {result.retrieved_examples.slice(0, 2).map((ex, i) => (
                        <div key={i} className="bg-slate-50 border border-slate-200 rounded p-3 text-sm">
                          <div className="text-slate-500 mb-1 font-medium">Historical Customer:</div>
                          <div className="mb-2 italic text-slate-700">"{ex.historical_customer_text}"</div>
                          <div className="text-slate-500 mb-1 font-medium flex justify-between">
                            <span>AmazonHelp Response:</span>
                            <span className="text-xs text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded border border-brand-100">
                              Sim: {ex.similarity_score.toFixed(2)}
                            </span>
                          </div>
                          <div className="text-slate-800">{ex.historical_brand_response}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* RIGHT PANEL: Decision Intel */}
          <div className="flex flex-col gap-4">
            <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex-1">
              <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                <Info size={20} className="text-blue-500" /> AI Decision Intelligence
              </h2>
              
              {!result && !loading && (
                <div className="text-slate-400 text-center py-10">
                  Run analysis to view pipeline metrics.
                </div>
              )}
              
              {result && !loading && (
                <div className="space-y-6">
                  {/* Pipeline Viz */}
                  <div className="space-y-0 relative before:absolute before:inset-0 before:ml-4 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-linear-to-b before:from-transparent before:via-slate-200 before:to-transparent">
                    
                    <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active pb-6">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full border border-white bg-slate-100 text-slate-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                        <CheckCircle size={16} className="text-brand-500" />
                      </div>
                      <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-3 rounded border border-slate-200 bg-white shadow-sm">
                        <div className="font-semibold text-xs tracking-wider uppercase mb-1 text-slate-500">Intent</div>
                        <div className="flex items-center gap-2 text-sm">
                          <span className="font-medium text-slate-800">{result.intent}</span>
                          <span className="text-xs text-slate-500">· {(result.intent_confidence * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>

                    <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active pb-6">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full border border-white bg-slate-100 text-slate-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                        <CheckCircle size={16} className="text-brand-500" />
                      </div>
                      <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-3 rounded border border-slate-200 bg-white shadow-sm">
                        <div className="font-semibold text-xs tracking-wider uppercase mb-1 text-slate-500">Retrieval</div>
                        <div className="flex items-center gap-2 text-sm">
                          <span className="font-medium text-slate-800">{result.retrieved_examples?.length || 0} examples</span>
                          <span className="text-xs text-slate-500">
                            · {result.retrieved_examples?.length ? result.retrieved_examples[0].similarity_score.toFixed(2) : '0.00'} best sim
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active pb-6">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full border border-white bg-slate-100 text-slate-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                        <CheckCircle size={16} className="text-brand-500" />
                      </div>
                      <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-3 rounded border border-slate-200 bg-white shadow-sm">
                        <div className="font-semibold text-xs tracking-wider uppercase mb-1 text-slate-500">Grounding</div>
                        <div className="text-sm">
                          <span className={`px-1.5 py-0.5 rounded font-medium ${
                            result.grounding_status === 'STRONG' ? 'bg-green-100 text-green-700' : 
                            result.grounding_status === 'MODERATE' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {result.grounding_status}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active pb-6">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full border border-white bg-slate-100 text-slate-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                        <CheckCircle size={16} className="text-brand-500" />
                      </div>
                      <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-3 rounded border border-slate-200 bg-white shadow-sm">
                        <div className="font-semibold text-xs tracking-wider uppercase mb-1 text-slate-500">Response</div>
                        <div className="text-sm font-medium text-slate-800">Generated</div>
                      </div>
                    </div>

                    <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full border border-white bg-slate-100 text-slate-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                        {result.decision === 'AUTO_HANDLE' ? <CheckCircle size={16} className="text-green-500" /> : <AlertTriangle size={16} className="text-amber-500" />}
                      </div>
                      <div className={`w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-3 rounded border shadow-sm ${getEscalationColor(result.decision)}`}>
                        <div className="font-semibold text-xs tracking-wider uppercase mb-1">Decision: {result.decision}</div>
                        <div className="text-xs opacity-90 line-clamp-2">
                          {result.decision_reason}
                        </div>
                      </div>
                    </div>

                  </div>
                </div>
              )}
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
};

const MessageSquareIcon = ({ className, size = 20 }: { className?: string, size?: number }) => (
  <MessageSquare size={size} className={className} />
);
