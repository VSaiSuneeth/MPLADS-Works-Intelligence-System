import React from 'react';
import { Search, X } from 'lucide-react';

interface QueueFilterBarProps {
  search: string;
  onSearchChange: (val: string) => void;
  selectedPriority: string;
  onPriorityChange: (priority: string) => void;
  selectedStage: string;
  onStageChange: (stage: string) => void;
  selectedCategory: string;
  onCategoryChange: (cat: string) => void;
  onReset: () => void;
}

export const QueueFilterBar: React.FC<QueueFilterBarProps> = ({
  search,
  onSearchChange,
  selectedPriority,
  onPriorityChange,
  selectedStage,
  onStageChange,
  selectedCategory,
  onCategoryChange,
  onReset,
}) => {
  const priorities = [
    { key: 'ALL', label: 'ALL WORKS' },
    { key: 'CRITICAL', label: 'CRITICAL RISK' },
    { key: 'HIGH', label: 'HIGH PRIORITY' },
    { key: 'MEDIUM', label: 'MEDIUM PRIORITY' },
    { key: 'LOW', label: 'LOW PRIORITY' },
  ];

  const stages = [
    { key: '', label: 'All Execution Stages' },
    { key: 'EXECUTION', label: 'In Execution' },
    { key: 'COMPLETED', label: 'Completed' },
    { key: 'SANCTIONED', label: 'Sanctioned' },
  ];

  const categories = [
    { key: '', label: 'All Work Categories' },
    { key: 'Water Supply & Sanitation', label: 'Water Supply & Sanitation' },
    { key: 'Roads & Bridges', label: 'Roads & Bridges' },
    { key: 'Community Infrastructure', label: 'Community Infrastructure' },
    { key: 'Education & Libraries', label: 'Education & Libraries' },
    { key: 'Healthcare Facilities', label: 'Healthcare Facilities' },
    { key: 'Renewable Energy', label: 'Renewable Energy' },
  ];

  const hasActiveFilters = search || selectedPriority !== 'ALL' || selectedStage || selectedCategory;

  return (
    <div className="gov-card p-4 space-y-3">
      {/* Priority Tabs */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1 border-b border-gray-200">
        {priorities.map((p) => {
          const isActive = selectedPriority === p.key;
          return (
            <button
              key={p.key}
              onClick={() => onPriorityChange(p.key)}
              className={`px-3 py-1.5 rounded-xs text-xs font-bold whitespace-nowrap tracking-wider transition ${
                isActive
                  ? 'bg-[#0B3D6E] text-white border border-[#0B3D6E]'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-gray-300'
              }`}
            >
              {p.label}
            </button>
          );
        })}
      </div>

      {/* Filter Inputs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-1">
        {/* Search Field */}
        <div className="relative md:col-span-2">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Filter by Work Title, Work ID, Agency, or Location..."
            className="gov-input pl-9"
          />
        </div>

        {/* Stage Select */}
        <div>
          <select
            value={selectedStage}
            onChange={(e) => onStageChange(e.target.value)}
            className="gov-input font-medium"
          >
            {stages.map((s) => (
              <option key={s.key} value={s.key}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {/* Category Select */}
        <div>
          <select
            value={selectedCategory}
            onChange={(e) => onCategoryChange(e.target.value)}
            className="gov-input font-medium"
          >
            {categories.map((c) => (
              <option key={c.key} value={c.key}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {hasActiveFilters && (
        <div className="flex justify-end pt-1">
          <button
            onClick={onReset}
            className="text-xs text-slate-600 hover:text-slate-900 font-bold flex items-center gap-1"
          >
            <X className="w-3.5 h-3.5" />
            <span>Reset Search & Filters</span>
          </button>
        </div>
      )}
    </div>
  );
};
