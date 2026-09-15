import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { RiskQueueItem } from '../types';
import { useAuth } from '../context/AuthContext';
import { QueueFilterBar } from '../components/queue/QueueFilterBar';
import { WorkTable } from '../components/queue/WorkTable';
import { AlertTriangle } from 'lucide-react';

interface RiskQueueResponse {
  items: RiskQueueItem[];
  page: number;
  pageSize: number;
  total: number;
}

export const WorkQueuePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { selectedJurisdictionId } = useAuth();

  const [search, setSearch] = useState('');
  const [priority, setPriority] = useState(searchParams.get('priority') || 'ALL');
  const [stage, setStage] = useState('');
  const [category, setCategory] = useState('');
  const [page, setPage] = useState(1);

  // Sync URL search params
  useEffect(() => {
    const urlPriority = searchParams.get('priority');
    if (urlPriority) {
      setPriority(urlPriority);
    }
  }, [searchParams]);

  const { data, isLoading, error, refetch } = useQuery<RiskQueueResponse>({
    queryKey: ['risk-queue', selectedJurisdictionId, priority, stage, category, search, page],
    queryFn: async () => {
      let url = `/risk/queue?page=${page}&pageSize=25`;
      if (selectedJurisdictionId) url += `&jurisdictionId=${selectedJurisdictionId}`;
      if (priority && priority !== 'ALL') url += `&priority=${priority}`;
      if (stage) url += `&stage=${stage}`;
      if (category) url += `&category=${category}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;

      const res = await apiClient.get<RiskQueueResponse>(url);
      return res.data;
    },
  });

  const handleReset = () => {
    setSearch('');
    setPriority('ALL');
    setStage('');
    setCategory('');
    setPage(1);
    setSearchParams({});
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Header */}
      <div className="border-b border-gray-300 pb-3">
        <h1 className="text-xl font-serif font-bold text-[#0A2540] tracking-tight flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-[#0B3D6E]" />
          Prioritized Operational Risk Queue
        </h1>
        <p className="text-xs text-slate-600">
          Sanctioned works ranked by composite risk score for targeted physical inspection and audit
        </p>
      </div>

      {/* Filter Bar */}
      <QueueFilterBar
        search={search}
        onSearchChange={(val) => {
          setSearch(val);
          setPage(1);
        }}
        selectedPriority={priority}
        onPriorityChange={(p) => {
          setPriority(p);
          setPage(1);
          setSearchParams(p === 'ALL' ? {} : { priority: p });
        }}
        selectedStage={stage}
        onStageChange={(s) => {
          setStage(s);
          setPage(1);
        }}
        selectedCategory={category}
        onCategoryChange={(cat: string) => {
          setCategory(cat);
          setPage(1);
        }}
        onReset={handleReset}
      />

      {/* Table Content */}
      {isLoading ? (
        <div className="h-64 bg-white border border-gray-300 rounded-xs animate-pulse"></div>
      ) : error || !data ? (
        <div className="gov-card p-8 text-center text-red-700 space-y-2">
          <AlertTriangle className="w-8 h-8 mx-auto" />
          <p className="font-bold text-xs">Failed to load risk queue dataset.</p>
        </div>
      ) : (
        <WorkTable
          items={data.items}
          page={data.page}
          pageSize={data.pageSize}
          total={data.total}
          onPageChange={(newPage) => setPage(newPage)}
        />
      )}
    </div>
  );
};
