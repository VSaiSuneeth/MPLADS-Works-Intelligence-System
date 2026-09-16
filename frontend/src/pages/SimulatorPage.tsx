import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { listSimulationProjectsApi, runSimulationApi, getSimulationBaseProjectApi } from '../api/client';
import { SimulationProjectItem, SimulationResponse } from '../types';
import { RiskBadge } from '../components/common/RiskBadge';
import {
  SlidersHorizontal,
  Play,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  Clock,
  Building2,
  Calendar,
  Sparkles,
  RefreshCw,
} from 'lucide-react';

export const SimulatorPage: React.FC = () => {
  const [mode, setMode] = useState<'EXISTING' | 'NEW'>('EXISTING');
  const [selectedWorkId, setSelectedWorkId] = useState<string>('');
  
  // Form parameters
  const [title, setTitle] = useState<string>('Simulated Project Proposal');
  const [category, setCategory] = useState<string>('Water Supply & Sanitation');
  const [projectCost, setProjectCost] = useState<number>(1500000);
  const [expenditureAmount, setExpenditureAmount] = useState<number>(1350000);
  const [completionPct, setCompletionPct] = useState<number>(15);
  const [sanctionDate, setSanctionDate] = useState<string>('2023-02-15');
  const [expectedCompletionDate, setExpectedCompletionDate] = useState<string>('2024-12-31');
  const [currentStatus, setCurrentStatus] = useState<string>('EXECUTION');

  const [simulationResult, setSimulationResult] = useState<SimulationResponse | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simError, setSimError] = useState<string | null>(null);

  // Load authorized projects for dropdown
  const { data: projectsData, isLoading: isLoadingProjects } = useQuery({
    queryKey: ['simulation-projects'],
    queryFn: async () => {
      const res = await listSimulationProjectsApi();
      return res.data;
    },
  });

  const projects: SimulationProjectItem[] = projectsData?.items || [];

  // When a project is selected from dropdown, pre-fill form parameters
  const handleSelectProject = async (workId: string) => {
    setSelectedWorkId(workId);
    if (!workId) return;

    try {
      const res = await getSimulationBaseProjectApi(workId);
      const proj = res.data;
      setTitle(proj.title);
      setCategory(proj.category || 'Water Supply & Sanitation');
      setProjectCost(proj.projectCost);
      setExpenditureAmount(proj.expenditureAmount);
      setCompletionPct(proj.completionPct);
      if (proj.sanctionDate) setSanctionDate(proj.sanctionDate);
      if (proj.expectedCompletionDate) setExpectedCompletionDate(proj.expectedCompletionDate);
      if (proj.currentStatus) setCurrentStatus(proj.currentStatus);

      // Auto-trigger simulation on load
      runSim({
        workId: proj.workId,
        title: proj.title,
        category: proj.category,
        projectCost: proj.projectCost,
        expenditureAmount: proj.expenditureAmount,
        completionPct: proj.completionPct,
        sanctionDate: proj.sanctionDate,
        expectedCompletionDate: proj.expectedCompletionDate,
        currentStatus: proj.currentStatus,
      });
    } catch (err: any) {
      console.error('Failed to load base project params', err);
    }
  };

  // Run simulation API
  const runSim = async (overrideParams?: any) => {
    setIsSimulating(true);
    setSimError(null);
    try {
      const payload = overrideParams || {
        workId: mode === 'EXISTING' ? selectedWorkId || undefined : undefined,
        title,
        category,
        projectCost: Number(projectCost) || 0,
        expenditureAmount: Number(expenditureAmount) || 0,
        completionPct: Number(completionPct) || 0,
        sanctionDate: sanctionDate || undefined,
        expectedCompletionDate: expectedCompletionDate || undefined,
        currentStatus,
      };

      const res = await runSimulationApi(payload);
      setSimulationResult(res.data);
    } catch (err: any) {
      setSimError(err?.response?.data?.detail?.error?.message || 'Simulation execution failed.');
    } finally {
      setIsSimulating(false);
    }
  };

  // Load first project on mount if available
  useEffect(() => {
    if (projects.length > 0 && !selectedWorkId && mode === 'EXISTING') {
      handleSelectProject(projects[0].workId);
    }
  }, [projects]);

  // Demo Preset Buttons for Judges
  const applyPreset = (presetType: 'DELAY_SPIKE' | 'EXPENDITURE_SPIKE' | 'BUDGET_REDUCTION') => {
    if (presetType === 'DELAY_SPIKE') {
      // Extend target completion date by 1 year while progress stays low
      setExpectedCompletionDate('2023-06-30');
      setCompletionPct(10);
      runSim({
        workId: mode === 'EXISTING' ? selectedWorkId || undefined : undefined,
        title,
        category,
        projectCost: Number(projectCost),
        expenditureAmount: Number(expenditureAmount),
        completionPct: 10,
        sanctionDate,
        expectedCompletionDate: '2023-06-30',
        currentStatus: 'EXECUTION',
      });
    } else if (presetType === 'EXPENDITURE_SPIKE') {
      // Increase expenditure to 95% of sanction while progress is only 15%
      const newExp = Math.round(projectCost * 0.95);
      setExpenditureAmount(newExp);
      setCompletionPct(15);
      runSim({
        workId: mode === 'EXISTING' ? selectedWorkId || undefined : undefined,
        title,
        category,
        projectCost: Number(projectCost),
        expenditureAmount: newExp,
        completionPct: 15,
        sanctionDate,
        expectedCompletionDate,
        currentStatus: 'EXECUTION',
      });
    } else if (presetType === 'BUDGET_REDUCTION') {
      // Reduce sanctioned cost below current expenditure causing budget overrun
      const newCost = Math.max(500000, Math.round(expenditureAmount * 0.75));
      setProjectCost(newCost);
      runSim({
        workId: mode === 'EXISTING' ? selectedWorkId || undefined : undefined,
        title,
        category,
        projectCost: newCost,
        expenditureAmount: Number(expenditureAmount),
        completionPct: Number(completionPct),
        sanctionDate,
        expectedCompletionDate,
        currentStatus: 'EXECUTION',
      });
    }
  };

  const curr = simulationResult?.currentScenario;
  const sim = simulationResult?.simulatedScenario;
  const delta = simulationResult?.impactDelta;

  const expenditureRatioPct = projectCost > 0 ? ((expenditureAmount / projectCost) * 100).toFixed(1) : '0.0';

  return (
    <div className="space-[#10] space-y-6 font-sans">
      {/* Header Banner */}
      <div className="bg-[#0A2540] text-white p-5 rounded-xs border-b-4 border-b-[#0B3D6E] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <SlidersHorizontal className="w-5 h-5 text-amber-400" />
            <h1 className="text-lg font-serif font-bold tracking-tight text-white">
              AI "What-If" Project Impact Simulator
            </h1>
            <span className="text-[10px] bg-amber-500/20 border border-amber-400/40 text-amber-300 px-2 py-0.5 rounded-xs font-mono font-bold uppercase">
              PREDICTIVE GOVERNANCE MODULE
            </span>
          </div>
          <p className="text-xs text-slate-300">
            Simulate parameter adjustments (sanction cost, disbursement, physical completion, target date) to project financial risk, delay risk, and overall project risk before formal approval.
          </p>
        </div>
      </div>

      {/* Mode Selector & Preset Buttons */}
      <div className="gov-card p-4 space-y-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-3">
          {/* Mode Tabs */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                setMode('EXISTING');
                if (projects.length > 0) handleSelectProject(projects[0].workId);
              }}
              className={`px-3 py-1.5 text-xs font-bold rounded-xs transition ${
                mode === 'EXISTING'
                  ? 'bg-[#0B3D6E] text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              Simulate Existing Sanctioned Work
            </button>
            <button
              onClick={() => {
                setMode('NEW');
                setSelectedWorkId('');
                setTitle('New Community Center Proposal');
                setCategory('Community Facilities');
                setProjectCost(2000000);
                setExpenditureAmount(500000);
                setCompletionPct(10);
                setSanctionDate('2024-01-01');
                setExpectedCompletionDate('2025-06-30');
              }}
              className={`px-3 py-1.5 text-xs font-bold rounded-xs transition ${
                mode === 'NEW'
                  ? 'bg-[#0B3D6E] text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              Simulate New Project Proposal (Blank)
            </button>
          </div>

          {/* Preset Buttons for Judge Demo */}
          <div className="flex items-center space-x-2 flex-wrap">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Demo Presets:</span>
            <button
              onClick={() => applyPreset('EXPENDITURE_SPIKE')}
              className="px-2.5 py-1 bg-red-50 text-red-800 border border-red-200 hover:bg-red-100 text-[11px] font-semibold rounded-xs transition flex items-center space-x-1"
            >
              <AlertTriangle className="w-3 h-3 text-red-600" />
              <span>Premature Spend Spike</span>
            </button>
            <button
              onClick={() => applyPreset('DELAY_SPIKE')}
              className="px-2.5 py-1 bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 text-[11px] font-semibold rounded-xs transition flex items-center space-x-1"
            >
              <Clock className="w-3 h-3 text-amber-600" />
              <span>Timeline Delay Slippage</span>
            </button>
            <button
              onClick={() => applyPreset('BUDGET_REDUCTION')}
              className="px-2.5 py-1 bg-indigo-50 text-indigo-800 border border-indigo-200 hover:bg-indigo-100 text-[11px] font-semibold rounded-xs transition flex items-center space-x-1"
            >
              <DollarSign className="w-3 h-3 text-indigo-600" />
              <span>Budget Cost Overrun</span>
            </button>
          </div>
        </div>

        {/* Existing Work Select Dropdown */}
        {mode === 'EXISTING' && (
          <div className="flex items-center space-x-3">
            <Building2 className="w-4 h-4 text-[#0B3D6E] shrink-0" />
            <span className="text-xs font-bold text-slate-700">Select Project:</span>
            <select
              value={selectedWorkId}
              onChange={(e) => handleSelectProject(e.target.value)}
              className="gov-input text-xs py-1.5 flex-1 max-w-xl font-medium"
              disabled={isLoadingProjects}
            >
              <option value="">-- Choose Sanctioned Work --</option>
              {projects.map((p) => (
                <option key={p.workId} value={p.workId}>
                  [{p.externalId}] {p.title} (₹{(p.projectCost / 100000).toFixed(1)} Lakhs - {p.category})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Main Grid: Parameter Form (Left) & Simulation Output (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Editable Parameters Form */}
        <div className="lg:col-span-5 space-y-4">
          <div className="gov-card p-5 space-y-4">
            <div className="border-b border-gray-200 pb-2 flex items-center justify-between">
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide flex items-center space-x-1.5">
                <SlidersHorizontal className="w-4 h-4 text-[#0B3D6E]" />
                <span>Simulation Input Parameters</span>
              </h2>
              <span className="text-[10px] font-mono text-slate-500 uppercase">Interactive Form</span>
            </div>

            {/* Title & Category */}
            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-bold text-slate-700 mb-1">Project Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="gov-input text-xs py-1.5 w-full font-medium"
                  placeholder="Enter project name..."
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-700 mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="gov-input text-xs py-1.5 w-full font-medium"
                >
                  <option value="Water Supply & Sanitation">Water Supply & Sanitation</option>
                  <option value="Education Infrastructure">Education Infrastructure</option>
                  <option value="Roads & Bridges">Roads & Bridges</option>
                  <option value="Health & Family Welfare">Health & Family Welfare</option>
                  <option value="Community Facilities">Community Facilities</option>
                </select>
              </div>

              {/* Sanction Cost (₹) */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-[11px] font-bold text-slate-700">Sanctioned Project Cost (₹)</label>
                  <span className="text-[11px] font-mono font-bold text-[#0B3D6E]">
                    ₹{Number(projectCost).toLocaleString('en-IN')}
                  </span>
                </div>
                <input
                  type="number"
                  step="50000"
                  value={projectCost}
                  onChange={(e) => setProjectCost(Number(e.target.value))}
                  className="gov-input text-xs py-1.5 w-full font-mono font-bold"
                />
              </div>

              {/* Expenditure Amount (₹) */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-[11px] font-bold text-slate-700">Expenditure / Disbursement (₹)</label>
                  <span className="text-[11px] font-mono font-bold text-amber-900">
                    Ratio: {expenditureRatioPct}%
                  </span>
                </div>
                <input
                  type="number"
                  step="25000"
                  value={expenditureAmount}
                  onChange={(e) => setExpenditureAmount(Number(e.target.value))}
                  className="gov-input text-xs py-1.5 w-full font-mono font-bold"
                />
              </div>

              {/* Physical Completion % Range Slider */}
              <div className="bg-slate-50 p-3 border border-gray-200 rounded-xs space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-[11px] font-bold text-slate-800">Physical Progress Percentage</label>
                  <span className="text-xs font-mono font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-xs border border-emerald-300">
                    {completionPct}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={completionPct}
                  onChange={(e) => setCompletionPct(Number(e.target.value))}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#0B3D6E]"
                />
                <div className="flex justify-between text-[10px] text-slate-600 font-mono">
                  <span>0% (Not Started)</span>
                  <span>50% (Halfway)</span>
                  <span>100% (Completed)</span>
                </div>
              </div>

              {/* Target Dates */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-bold text-slate-700 mb-1">Sanction Date</label>
                  <input
                    type="date"
                    value={sanctionDate}
                    onChange={(e) => setSanctionDate(e.target.value)}
                    className="gov-input text-xs py-1.5 w-full font-mono"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate-700 mb-1">Expected Completion Date</label>
                  <input
                    type="date"
                    value={expectedCompletionDate}
                    onChange={(e) => setExpectedCompletionDate(e.target.value)}
                    className="gov-input text-xs py-1.5 w-full font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Submit Action Button */}
            <button
              onClick={() => runSim()}
              disabled={isSimulating}
              className="gov-btn-primary w-full py-2.5 text-xs font-bold flex items-center justify-center space-x-2 shadow-sm uppercase tracking-wide"
            >
              {isSimulating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>Computing Predictive Risk...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 text-white fill-white" />
                  <span>Run What-If Impact Simulation</span>
                </>
              )}
            </button>

            {simError && (
              <div className="p-3 bg-red-50 border border-red-200 text-xs text-red-800 rounded-xs flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-red-600" />
                <span>{simError}</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Simulation Comparison & Predicted Impact */}
        <div className="lg:col-span-7 space-y-4">
          {simulationResult && curr && sim && delta ? (
            <>
              {/* Impact Summary Banner */}
              <div
                className={`p-4 rounded-xs border shadow-xs space-y-2 ${
                  delta.isRiskIncreased
                    ? 'bg-red-50 border-red-300 text-red-950'
                    : 'bg-emerald-50 border-emerald-300 text-emerald-950'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {delta.isRiskIncreased ? (
                      <TrendingUp className="w-5 h-5 text-red-700 shrink-0" />
                    ) : (
                      <TrendingDown className="w-5 h-5 text-emerald-700 shrink-0" />
                    )}
                    <span className="text-xs font-bold uppercase tracking-wider">
                      Predicted Risk Impact Summary
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 font-mono text-xs font-bold">
                    <span className="bg-white/80 border px-2.5 py-0.5 rounded-xs">
                      Delta: {delta.overallScoreDelta >= 0 ? `+${delta.overallScoreDelta}` : delta.overallScoreDelta} pts
                    </span>
                    <span className="bg-white/80 border px-2.5 py-0.5 rounded-xs">
                      Band: {delta.priorityBandChange}
                    </span>
                  </div>
                </div>

                <p className="text-xs leading-relaxed text-slate-800 font-medium">
                  {delta.recommendedAction}
                </p>
              </div>

              {/* Side-by-Side Comparison Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Current Baseline Card */}
                <div className="gov-card p-4 space-y-3 bg-slate-50/50">
                  <div className="flex items-center justify-between border-b border-gray-200 pb-2">
                    <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                      Current Baseline Scenario
                    </span>
                    <RiskBadge priority={curr.priorityBand} score={curr.overallScore} size="sm" />
                  </div>

                  <div className="space-y-2.5 text-xs">
                    <div>
                      <div className="flex justify-between text-[11px] font-medium text-slate-600 mb-1">
                        <span>Financial Risk Score</span>
                        <span className="font-mono font-bold text-slate-900">{curr.financialRiskScore}/100 ({curr.financialRiskSeverity})</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-[#0B3D6E] h-2 rounded-full"
                          style={{ width: `${Math.min(100, curr.financialRiskScore)}%` }}
                        ></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-[11px] font-medium text-slate-600 mb-1">
                        <span>Delay Risk Score</span>
                        <span className="font-mono font-bold text-slate-900">{curr.delayRiskScore}/100 ({curr.delayRiskSeverity})</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-amber-600 h-2 rounded-full"
                          style={{ width: `${Math.min(100, curr.delayRiskScore)}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-gray-200 grid grid-cols-2 gap-2 text-[11px] font-mono">
                      <div className="bg-white p-2 border rounded-xs">
                        <span className="text-[10px] text-slate-600 block">Disbursement</span>
                        <span className="font-bold text-slate-800">{curr.expenditureRatioPct}%</span>
                      </div>
                      <div className="bg-white p-2 border rounded-xs">
                        <span className="text-[10px] text-slate-600 block">Physical Progress</span>
                        <span className="font-bold text-slate-800">{curr.completionPct}%</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Simulated Scenario Card */}
                <div className="gov-card p-4 space-y-3 bg-blue-50/30 border-blue-200">
                  <div className="flex items-center justify-between border-b border-blue-200 pb-2">
                    <span className="text-xs font-bold text-[#0B3D6E] uppercase tracking-wide flex items-center space-x-1">
                      <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                      <span>Simulated Scenario</span>
                    </span>
                    <RiskBadge priority={sim.priorityBand} score={sim.overallScore} size="sm" />
                  </div>

                  <div className="space-y-2.5 text-xs">
                    <div>
                      <div className="flex justify-between text-[11px] font-medium text-slate-600 mb-1">
                        <span>Financial Risk Score</span>
                        <span className="font-mono font-bold text-slate-900">{sim.financialRiskScore}/100 ({sim.financialRiskSeverity})</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-[#0B3D6E] h-2 rounded-full"
                          style={{ width: `${Math.min(100, sim.financialRiskScore)}%` }}
                        ></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-[11px] font-medium text-slate-600 mb-1">
                        <span>Delay Risk Score</span>
                        <span className="font-mono font-bold text-slate-900">{sim.delayRiskScore}/100 ({sim.delayRiskSeverity})</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-amber-600 h-2 rounded-full"
                          style={{ width: `${Math.min(100, sim.delayRiskScore)}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-blue-200 grid grid-cols-2 gap-2 text-[11px] font-mono">
                      <div className="bg-white p-2 border border-blue-200 rounded-xs">
                        <span className="text-[10px] text-slate-600 block">Disbursement</span>
                        <span className="font-bold text-slate-800">{sim.expenditureRatioPct}%</span>
                      </div>
                      <div className="bg-white p-2 border border-blue-200 rounded-xs">
                        <span className="text-[10px] text-slate-600 block">Physical Progress</span>
                        <span className="font-bold text-slate-800">{sim.completionPct}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Risk Comparison Indicators Bar */}
              <div className="gov-card p-5 space-y-4">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide border-b border-gray-200 pb-2">
                  Comparative Risk Indicators (Current vs Simulated)
                </h3>

                <div className="space-y-3 text-xs font-sans">
                  {/* Financial Risk Indicator */}
                  <div className="space-y-1">
                    <div className="flex justify-between items-center text-[11px]">
                      <span className="font-bold text-slate-700">Financial Risk Comparison</span>
                      <span className="font-mono text-slate-600">
                        {curr.financialRiskScore} pts → <strong className="text-slate-900">{sim.financialRiskScore} pts</strong> ({delta.financialRiskDelta >= 0 ? `+${delta.financialRiskDelta}` : delta.financialRiskDelta})
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="h-3 bg-slate-200 rounded-xs overflow-hidden">
                        <div className="bg-slate-600 h-full" style={{ width: `${curr.financialRiskScore}%` }}></div>
                      </div>
                      <div className="h-3 bg-slate-200 rounded-xs overflow-hidden">
                        <div className="bg-[#0B3D6E] h-full" style={{ width: `${sim.financialRiskScore}%` }}></div>
                      </div>
                    </div>
                  </div>

                  {/* Delay Risk Indicator */}
                  <div className="space-y-1">
                    <div className="flex justify-between items-center text-[11px]">
                      <span className="font-bold text-slate-700">Delay Risk Comparison</span>
                      <span className="font-mono text-slate-600">
                        {curr.delayRiskScore} pts → <strong className="text-slate-900">{sim.delayRiskScore} pts</strong> ({delta.delayRiskDelta >= 0 ? `+${delta.delayRiskDelta}` : delta.delayRiskDelta})
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="h-3 bg-slate-200 rounded-xs overflow-hidden">
                        <div className="bg-amber-500 h-full" style={{ width: `${curr.delayRiskScore}%` }}></div>
                      </div>
                      <div className="h-3 bg-slate-200 rounded-xs overflow-hidden">
                        <div className="bg-amber-700 h-full" style={{ width: `${sim.delayRiskScore}%` }}></div>
                      </div>
                    </div>
                  </div>

                  {/* Overall Composite Risk Indicator */}
                  <div className="space-y-1 pt-1">
                    <div className="flex justify-between items-center text-[11px]">
                      <span className="font-bold text-slate-800 uppercase">Overall Composite Risk Score</span>
                      <span className="font-mono text-slate-900 font-bold">
                        {curr.overallScore} pts → {sim.overallScore} pts
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="h-4 bg-slate-200 rounded-xs overflow-hidden">
                        <div className="bg-slate-700 h-full flex items-center justify-end pr-1 text-[9px] font-mono text-white font-bold" style={{ width: `${curr.overallScore}%` }}>
                          {curr.overallScore}
                        </div>
                      </div>
                      <div className="h-4 bg-slate-200 rounded-xs overflow-hidden">
                        <div className="bg-red-700 h-full flex items-center justify-end pr-1 text-[9px] font-mono text-white font-bold" style={{ width: `${sim.overallScore}%` }}>
                          {sim.overallScore}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Key Risk Drivers List */}
              <div className="gov-card p-5 space-y-3">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide border-b border-gray-200 pb-2">
                  Explainable Key Risk Drivers & Signals
                </h3>

                <ul className="space-y-2 text-xs text-slate-700 font-sans">
                  {delta.keyDrivers.map((driver, idx) => (
                    <li key={idx} className="flex items-start space-x-2 bg-slate-50 p-2.5 border border-gray-200 rounded-xs">
                      <span className="text-[#0B3D6E] font-bold shrink-0">•</span>
                      <span className="leading-snug">{driver}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          ) : (
            <div className="gov-card p-12 text-center text-slate-500 space-y-3">
              <SlidersHorizontal className="w-8 h-8 text-slate-400 mx-auto" />
              <p className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Ready to Run What-If Impact Simulation
              </p>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Adjust project parameters on the left or select a preset scenario to view predicted risk level changes.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
