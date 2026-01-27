'use client';

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface City {
    id: string;
    lat: number;
    lng: number;
    label: string;
    abbr: string;
}

interface LeafletMapProps {
    cities: City[];
    selectedTimezone: string;
    onTimezoneChange: (timezone: string) => void;
}

export default function LeafletMap({ cities, selectedTimezone, onTimezoneChange }: LeafletMapProps) {
    const mapRef = useRef<L.Map | null>(null);
    const mapContainerRef = useRef<HTMLDivElement>(null);
    const markersRef = useRef<L.CircleMarker[]>([]);

    useEffect(() => {
        if (!mapContainerRef.current || mapRef.current) return;

        // Initialize map
        const map = L.map(mapContainerRef.current, {
            center: [20, 0],
            zoom: 1.5,
            minZoom: 1,
            maxZoom: 5,
            zoomControl: false,
            attributionControl: false,
            scrollWheelZoom: false,
            dragging: true,
            doubleClickZoom: false,
        });

        // Dark tile layer (CartoDB Dark Matter)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            subdomains: 'abcd',
        }).addTo(map);

        // Add markers for each city
        cities.forEach((city) => {
            const isSelected = city.id === selectedTimezone;
            
            const marker = L.circleMarker([city.lat, city.lng], {
                radius: isSelected ? 10 : 6,
                fillColor: isSelected ? '#a855f7' : '#64748b',
                color: isSelected ? '#c084fc' : '#475569',
                weight: isSelected ? 3 : 1,
                opacity: 1,
                fillOpacity: 0.9,
                className: isSelected ? 'selected-marker' : '',
            });

            // Add tooltip
            marker.bindTooltip(city.label, {
                permanent: isSelected,
                direction: 'top',
                className: `timezone-tooltip ${isSelected ? 'selected' : ''}`,
                offset: [0, -10],
            });

            marker.on('click', () => {
                onTimezoneChange(city.id);
            });

            marker.addTo(map);
            markersRef.current.push(marker);
        });

        mapRef.current = map;

        return () => {
            map.remove();
            mapRef.current = null;
            markersRef.current = [];
        };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Intentionally run once on mount. Cities, onTimezoneChange, and selectedTimezone are used but shouldn't trigger re-initialization.
    }, []);

    // Update marker styles when selection changes
    useEffect(() => {
        if (!mapRef.current) return;

        markersRef.current.forEach((marker, index) => {
            const city = cities[index];
            const isSelected = city.id === selectedTimezone;

            marker.setStyle({
                radius: isSelected ? 10 : 6,
                fillColor: isSelected ? '#a855f7' : '#64748b',
                color: isSelected ? '#c084fc' : '#475569',
                weight: isSelected ? 3 : 1,
            });

            // Update tooltip
            marker.unbindTooltip();
            marker.bindTooltip(city.label, {
                permanent: isSelected,
                direction: 'top',
                className: `timezone-tooltip ${isSelected ? 'selected' : ''}`,
                offset: [0, -10],
            });

            // Pan to selected city
            if (isSelected) {
                mapRef.current?.panTo([city.lat, city.lng], { animate: true, duration: 0.5 });
            }
        });
    }, [selectedTimezone, cities]);

    return (
        <>
            <style jsx global>{`
                .timezone-tooltip {
                    background: rgba(15, 23, 42, 0.9) !important;
                    border: 1px solid rgba(100, 116, 139, 0.5) !important;
                    color: #e2e8f0 !important;
                    font-size: 11px !important;
                    font-weight: 500 !important;
                    padding: 4px 8px !important;
                    border-radius: 6px !important;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
                }
                .timezone-tooltip.selected {
                    background: rgba(139, 92, 246, 0.9) !important;
                    border-color: rgba(168, 85, 247, 0.8) !important;
                    color: white !important;
                    font-weight: 600 !important;
                }
                .timezone-tooltip::before {
                    border-top-color: rgba(15, 23, 42, 0.9) !important;
                }
                .selected-marker {
                    animation: pulse 2s infinite;
                }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.7; }
                }
                .leaflet-container {
                    background: #0f172a !important;
                }
            `}</style>
            <div 
                ref={mapContainerRef} 
                className="w-full h-64 rounded-lg overflow-hidden"
                style={{ background: '#0f172a' }}
            />
        </>
    );
}
