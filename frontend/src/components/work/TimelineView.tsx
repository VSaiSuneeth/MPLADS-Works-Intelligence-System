import React from 'react';
import { LifecycleEvent } from '../../types';
import { CheckCircle2, Clock, AlertCircle, Calendar, CreditCard, Hammer, FileCheck } from 'lucide-react';

interface TimelineViewProps {
  events: LifecycleEvent[];
}

export const TimelineView: React.FC<TimelineViewProps> = ({ events }) => {
  const getEventIcon = (type: string, isMissing: boolean) => {
    if (isMissing) return AlertCircle;
    switch (type) {
      case 'RECOMMENDATION':
        return Calendar;
      case 'SANCTION':
        return FileCheck;
      case 'AGENCY_ASSIGNMENT':
        return Hammer;
      case 'PROGRESS_UPDATE':
        return Clock;
      case 'PAYMENT_DISBURSED':
        return CreditCard;
      case 'COMPLETION':
        return CheckCircle2;
      default:
        return CheckCircle2;
    }
  };

  return (
    <div className="gov-card p-5 space-y-5">
      <div className="border-b border-gray-200 pb-3">
        <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
          Work Lifecycle Milestone Timeline
        </h2>
        <p className="text-xs text-slate-500">
          Chronological milestone progression and unrecorded event markers
        </p>
      </div>

      <div className="relative pl-7 space-y-5 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-300">
        {events.map((evt) => {
          const Icon = getEventIcon(evt.eventType, evt.isMissing);

          return (
            <div key={evt.id} className="relative flex items-start space-x-3 group">
              {/* Timeline Marker Dot */}
              <div
                className={`absolute -left-7 top-0.5 w-6 h-6 rounded-full flex items-center justify-center border text-xs shrink-0 ${
                  evt.isMissing
                    ? 'bg-amber-500 border-amber-600 text-white shadow-xs'
                    : evt.eventType === 'COMPLETION'
                    ? 'bg-[#15803D] border-[#166534] text-white shadow-xs'
                    : 'bg-[#0B3D6E] border-[#0A2540] text-white shadow-xs'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
              </div>

              {/* Event Content Box */}
              <div
                className={`flex-1 p-3.5 rounded-xs border ${
                  evt.isMissing
                    ? 'bg-amber-50 border-amber-300 text-amber-950 border-dashed'
                    : 'bg-white border-gray-300 text-slate-900 shadow-xs'
                }`}
              >
                <div className="flex items-center justify-between flex-wrap gap-2 mb-1 border-b border-gray-200 pb-1.5">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-xs font-bold uppercase tracking-wider ${
                        evt.isMissing ? 'text-amber-900' : 'text-slate-900'
                      }`}
                    >
                      {evt.eventType.replace(/_/g, ' ')}
                    </span>
                    {evt.status && (
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-xs font-mono uppercase ${
                          evt.isMissing
                            ? 'bg-amber-200 text-amber-900 border border-amber-300'
                            : 'bg-slate-100 text-slate-800 border border-gray-300'
                        }`}
                      >
                        {evt.status}
                      </span>
                    )}
                  </div>

                  <span className="text-xs font-mono font-bold text-slate-700">
                    {evt.eventDate ? (
                      (() => {
                        if (!evt.eventDate || evt.eventDate === 'Date Not Recorded') return 'Date Not Recorded';
                        try {
                          const isoStr = evt.eventDate.includes(' ') && !evt.eventDate.includes('T') ? evt.eventDate.replace(' ', 'T') : evt.eventDate;
                          const d = new Date(isoStr);
                          return isNaN(d.getTime()) ? evt.eventDate : d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
                        } catch {
                          return evt.eventDate;
                        }
                      })()
                    ) : 'Date Not Recorded'}
                  </span>
                </div>

                <p className="text-xs text-slate-800 font-medium leading-relaxed">{evt.description}</p>

                {evt.amount && (
                  <div className="mt-1.5 text-xs font-mono font-bold text-[#15803D]">
                    Amount Disbursed: ₹{evt.amount.toLocaleString('en-IN')}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
