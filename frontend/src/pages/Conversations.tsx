import { useEffect, useState } from 'react';
import { Header } from '../components/Header';
import { getConversations } from '../services/api';
import { Database, Zap, FileText } from 'lucide-react';

export const Conversations: React.FC = () => {
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    getConversations().then(setConversations).catch(console.error);
  }, []);

  const selected = conversations.find(c => c.tweet_id === selectedId);

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-hidden">
      <Header title="Evaluation Conversations" description="Review offline predictions from the evaluation set." />
      
      <div className="flex flex-1 overflow-hidden">
        {/* List */}
        <div className="w-1/3 border-r border-slate-200 bg-white overflow-y-auto">
          {conversations.map((c, i) => (
            <div 
              key={c.tweet_id || i}
              onClick={() => setSelectedId(c.tweet_id)}
              className={`p-4 border-b border-slate-100 cursor-pointer transition-colors ${
                selectedId === c.tweet_id ? 'bg-brand-50 border-l-4 border-l-brand-500' : 'hover:bg-slate-50 border-l-4 border-l-transparent'
              }`}
            >
              <div className="flex justify-between items-start mb-1">
                <span className="text-xs font-semibold text-slate-500">{c.predicted_intent}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                  c.escalation_decision === 'AUTO_HANDLE' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {c.escalation_decision}
                </span>
              </div>
              <p className="text-sm text-slate-800 line-clamp-2">{c.customer_text}</p>
            </div>
          ))}
        </div>
        
        {/* Detail */}
        <div className="w-2/3 bg-slate-50 p-6 overflow-y-auto">
          {selected ? (
            <div className="max-w-3xl mx-auto space-y-6 pb-12">
              
              <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-wider bg-slate-200 px-3 py-1.5 rounded-full w-fit">
                <Database size={14} /> Offline Evaluation Conversation
              </div>

              <div className="bg-white p-5 rounded border border-slate-200 shadow-sm">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-2"><FileText size={16}/> Customer Message</h3>
                <p className="text-slate-800">{selected.customer_text}</p>
                {selected.needs_context && (
                  <div className="mt-3 pt-3 border-t border-slate-100 text-sm text-amber-700 bg-amber-50 p-2 rounded">
                    <strong>Note:</strong> Context missing or ambiguous.
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded border border-slate-200 shadow-sm">
                  <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider">Intent Details</div>
                  <div className="space-y-2 mt-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">True:</span>
                      <span className="font-medium">{selected.true_intent}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Predicted:</span>
                      <span className={`font-medium ${selected.true_intent === selected.predicted_intent ? 'text-green-600' : 'text-red-600'}`}>
                        {selected.predicted_intent}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Confidence:</span>
                      <span className="font-medium">{(selected.intent_confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-4 rounded border border-slate-200 shadow-sm">
                  <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider">Grounding & Decision</div>
                  <div className="space-y-2 mt-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Grounding:</span>
                      <span className="font-medium">{selected.grounding_status}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Decision:</span>
                      <span className={`px-1.5 py-0.5 rounded text-xs font-bold ${
                        selected.escalation_decision === 'AUTO_HANDLE' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {selected.escalation_decision}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {selected.escalation_reason && selected.escalation_decision !== 'AUTO_HANDLE' && (
                <div className="bg-red-50 p-4 rounded border border-red-200 text-red-800 text-sm">
                  <strong>Escalation Reason:</strong> {selected.escalation_reason}
                </div>
              )}

              <div className="bg-white p-5 rounded border border-slate-200 shadow-sm">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-2"><Zap size={16}/> AI Response</h3>
                <p className="text-slate-800 whitespace-pre-wrap text-sm">{selected.generated_response}</p>
              </div>

            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-400">
              Select a conversation to view details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
