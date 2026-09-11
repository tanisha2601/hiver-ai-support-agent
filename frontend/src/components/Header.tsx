import React from 'react';

interface HeaderProps {
  title: string;
  description: string;
}

export const Header: React.FC<HeaderProps> = ({ title, description }) => {
  return (
    <header className="bg-white border-b border-gray-200 px-8 py-5 flex justify-between items-center sticky top-0 z-10">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">{title}</h1>
        <p className="text-sm text-gray-500 mt-1">{description}</p>
      </div>
      <div className="flex items-center gap-3">
        <span className="bg-brand-50 text-brand-700 text-xs font-medium px-2.5 py-1 rounded border border-brand-200">
          STAGING ENV
        </span>
      </div>
    </header>
  );
};
