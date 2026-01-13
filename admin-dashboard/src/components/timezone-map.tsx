'use client';

import dynamic from 'next/dynamic';
import { useTimezone, TIMEZONE_OPTIONS } from '@/lib/timezone-context';

// Lazy load Leaflet map to avoid SSR issues
const LeafletMap = dynamic(() => import('@/components/leaflet-map'), { 
    ssr: false,
    loading: () => (
        <div className="w-full h-64 bg-slate-900 rounded-lg flex items-center justify-center">
            <div className="animate-pulse text-slate-500">Loading map...</div>
        </div>
    )
});

interface TimezoneMapProps {
    onTimezoneChange: (timezone: string) => void;
    selectedTimezone: string;
}

// City coordinates for each timezone
export const TIMEZONE_CITIES = [
    { id: 'America/Los_Angeles', lat: 34.0522, lng: -118.2437, label: 'Los Angeles', abbr: 'LA' },
    { id: 'America/New_York', lat: 40.7128, lng: -74.0060, label: 'New York', abbr: 'NY' },
    { id: 'UTC', lat: 51.5074, lng: 0.0, label: 'UTC', abbr: 'UTC' },
    { id: 'Europe/London', lat: 51.5074, lng: -0.1278, label: 'London', abbr: 'LON' },
    { id: 'Asia/Shanghai', lat: 31.2304, lng: 121.4737, label: 'Shanghai', abbr: 'SH' },
    { id: 'Asia/Tokyo', lat: 35.6762, lng: 139.6503, label: 'Tokyo', abbr: 'TYO' },
    { id: 'Asia/Singapore', lat: 1.3521, lng: 103.8198, label: 'Singapore', abbr: 'SG' },
    { id: 'Asia/Bangkok', lat: 13.7563, lng: 100.5018, label: 'Bangkok', abbr: 'BKK' },
];

export default function TimezoneMap({ onTimezoneChange, selectedTimezone }: TimezoneMapProps) {
    return (
        <LeafletMap 
            cities={TIMEZONE_CITIES}
            selectedTimezone={selectedTimezone}
            onTimezoneChange={onTimezoneChange}
        />
    );
}
