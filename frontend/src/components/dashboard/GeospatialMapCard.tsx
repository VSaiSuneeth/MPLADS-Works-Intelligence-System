import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, ExternalLink, Globe } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface MapWork {
  workId: string;
  externalId: string;
  title: string;
  category: string;
  latitude?: number | null;
  longitude?: number | null;
  score: number;
  priority: string;
  sanctionAmount?: number | null;
  districtName?: string;
}

interface GeospatialMapCardProps {
  works: MapWork[];
}

export const GeospatialMapCard: React.FC<GeospatialMapCardProps> = ({ works }) => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const navigate = useNavigate();

  // Filter works with valid latitude and longitude
  const mappedWorks = works.filter(
    (w) => w.latitude !== null && w.latitude !== undefined &&
           w.longitude !== null && w.longitude !== undefined &&
           !isNaN(Number(w.latitude)) && !isNaN(Number(w.longitude))
  );

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Initialize Leaflet Map if not created
    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [22.5937, 78.9629], // Center of India
        zoom: 5,
        zoomControl: true,
        scrollWheelZoom: false,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18,
      }).addTo(map);

      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;

    // Clear existing markers
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker) {
        map.removeLayer(layer);
      }
    });

    if (mappedWorks.length === 0) return;

    const bounds = L.latLngBounds([]);

    mappedWorks.forEach((w) => {
      const lat = Number(w.latitude);
      const lng = Number(w.longitude);

      bounds.extend([lat, lng]);

      // Color coding by risk level
      let color = '#15803D'; // Low (Green)
      if (w.priority === 'CRITICAL' || w.score >= 80) color = '#991B1B'; // Critical (Red)
      else if (w.priority === 'HIGH' || w.score >= 60) color = '#C2410C'; // High (Orange)
      else if (w.priority === 'MEDIUM' || w.score >= 30) color = '#B45309'; // Medium (Amber)

      // SVG DivIcon pin
      const iconHtml = `
        <div style="
          background-color: ${color};
          width: 28px;
          height: 28px;
          border-radius: 50%;
          border: 2px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 11px;
          font-family: monospace;
        ">
          ${Math.round(w.score)}
        </div>
      `;

      const customIcon = L.divIcon({
        html: iconHtml,
        className: 'custom-map-pin',
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const marker = L.marker([lat, lng], { icon: customIcon }).addTo(map);

      // Popup Content
      const popupDiv = document.createElement('div');
      popupDiv.className = 'p-1 font-sans text-xs space-y-1.5 max-w-[220px]';
      popupDiv.innerHTML = `
        <div class="font-bold text-slate-900 border-b border-gray-200 pb-1">
          <span class="text-[10px] font-mono font-bold text-blue-700 uppercase block">${w.externalId}</span>
          ${w.title}
        </div>
        <div class="text-[11px] text-slate-600 space-y-0.5">
          <div><strong>Category:</strong> ${w.category}</div>
          <div><strong>District:</strong> ${w.districtName || 'National Scope'}</div>
          <div><strong>Risk Band:</strong> <span style="color: ${color}; font-weight: bold;">${w.priority} (${w.score.toFixed(1)} pts)</span></div>
        </div>
        <button id="view-work-${w.workId}" class="w-full mt-2 px-2 py-1 bg-[#0A2540] hover:bg-[#0B3D6E] text-white text-[11px] font-medium rounded-sm flex items-center justify-center space-x-1 cursor-pointer">
          <span>View Work Detail</span>
        </button>
      `;

      marker.bindPopup(popupDiv);

      marker.on('popupopen', () => {
        const btn = document.getElementById(`view-work-${w.workId}`);
        if (btn) {
          btn.onclick = () => {
            navigate(`/works/${w.workId}`);
          };
        }
      });
    });

    if (mappedWorks.length > 0) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
    }
  }, [mappedWorks, navigate]);

  return (
    <div className="gov-card p-5 space-y-4 font-sans">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-gray-200 pb-3 gap-2">
        <div>
          <h2 className="text-sm font-bold text-[#0A2540] uppercase tracking-wide flex items-center space-x-2">
            <Globe className="w-4 h-4 text-blue-700 shrink-0" />
            <span>Geospatial Risk Distribution</span>
          </h2>
          <p className="text-xs text-slate-500">
            Interactive map displaying site location risk bands for monitored works
          </p>
        </div>
        <div className="flex items-center space-x-3 text-[11px]">
          <span className="font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded-sm border border-slate-200">
            Mapped: {mappedWorks.length} / {works.length} Works
          </span>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono bg-slate-50 p-2 rounded-sm border border-slate-200">
        <span className="text-slate-500 font-bold uppercase text-[10px]">Risk Legend:</span>
        <div className="flex items-center space-x-1">
          <span className="w-2.5 h-2.5 rounded-full bg-[#991B1B]"></span>
          <span className="text-[#991B1B] font-bold">Critical (≥80)</span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="w-2.5 h-2.5 rounded-full bg-[#C2410C]"></span>
          <span className="text-[#C2410C] font-bold">High (60-79)</span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="w-2.5 h-2.5 rounded-full bg-[#B45309]"></span>
          <span className="text-[#B45309] font-bold">Medium (30-59)</span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="w-2.5 h-2.5 rounded-full bg-[#15803D]"></span>
          <span className="text-[#15803D] font-bold">Low (&lt;30)</span>
        </div>
      </div>

      {/* Map Container */}
      <div className="relative w-full h-[360px] rounded-sm border border-gray-300 overflow-hidden bg-slate-100">
        <div ref={mapContainerRef} className="w-full h-full z-10" />

        {mappedWorks.length === 0 && (
          <div className="absolute inset-0 z-20 bg-white/90 flex flex-col items-center justify-center p-4 text-center space-y-2">
            <MapPin className="w-8 h-8 text-slate-400" />
            <p className="text-xs font-bold text-slate-700">No Geographic Coordinates Available</p>
            <p className="text-[11px] text-slate-500 max-w-sm">
              The current filter selection contains works without explicit latitude and longitude metadata.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
