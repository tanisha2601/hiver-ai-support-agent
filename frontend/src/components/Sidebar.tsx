import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, List, BarChart2, ShieldAlert, Search, Settings, Server } from 'lucide-react';
import { getHealth } from '../services/api';

export const Sidebar: React.FC = () => {
  const [health, setHealth] = useState<string>('checking');

  useEffect(() => {
    getHealth().then(() => setHealth('online')).catch(() => setHealth('offline'));
  }, []);

  const navItems = [
    { to: '/', icon: <LayoutDashboard size={20} />, label: 'Overview' },
    { to: '/agent', icon: <MessageSquare size={20} />, label: 'Support Agent' },
    { to: '/conversations', icon: <List size={20} />, label: 'Conversations' },
    { to: '/evaluation', icon: <BarChart2 size={20} />, label: 'Evaluation' },
    { to: '/retrieval', icon: <Search size={20} />, label: 'Retrieval' },
    { to: '/analytics', icon: <BarChart2 size={20} />, label: 'Analytics' },
    { to: '/failures', icon: <ShieldAlert size={20} />, label: 'Failures' },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col h-screen fixed left-0 top-0">
      <div className="p-6 border-b border-slate-800">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Server size={24} className="text-brand-500" />
          HIVER AI SUPPORT
        </h1>
      </div>
      
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                isActive ? 'bg-brand-600 text-white' : 'hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 mb-4 px-3">
          <div className={`w-2.5 h-2.5 rounded-full ${health === 'online' ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm">Agent {health}</span>
        </div>
        <NavLink to="/system" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-800 hover:text-white transition-colors">
          <Settings size={20} />
          System Settings
        </NavLink>
      </div>
    </aside>
  );
};
