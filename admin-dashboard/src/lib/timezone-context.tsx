'use client';

import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';

export interface TimezoneSettings {
    timezone: string;
    use24Hour: boolean;
    dateFormat: 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD';
}

interface TimezoneContextType {
    settings: TimezoneSettings;
    setTimezone: (tz: string) => void;
    setUse24Hour: (use24: boolean) => void;
    setDateFormat: (format: TimezoneSettings['dateFormat']) => void;
    autoDetectTimezone: () => void;
}

const defaultSettings: TimezoneSettings = {
    timezone: 'Asia/Bangkok',
    use24Hour: false,
    dateFormat: 'DD/MM/YYYY',
};

const STORAGE_KEY = 'papa-chatbot-timezone-settings';

const TimezoneContext = createContext<TimezoneContextType | undefined>(undefined);

export const TIMEZONE_OPTIONS = [
    { value: 'Asia/Bangkok', label: 'Bangkok (ICT)', offset: 'GMT+7' },
    { value: 'Asia/Singapore', label: 'Singapore (SGT)', offset: 'GMT+8' },
    { value: 'Asia/Tokyo', label: 'Tokyo (JST)', offset: 'GMT+9' },
    { value: 'Asia/Shanghai', label: 'Shanghai (CST)', offset: 'GMT+8' },
    { value: 'UTC', label: 'UTC', offset: 'GMT+0' },
    { value: 'Europe/London', label: 'London (GMT/BST)', offset: 'GMT+0/+1' },
    { value: 'America/New_York', label: 'New York (EST/EDT)', offset: 'GMT-5/-4' },
    { value: 'America/Los_Angeles', label: 'Los Angeles (PST/PDT)', offset: 'GMT-8/-7' },
];

export function TimezoneProvider({ children }: { children: ReactNode }) {
    // Load from localStorage on mount using lazy initial state
    const [settings, setSettings] = useState<TimezoneSettings>(() => {
        if (typeof window === 'undefined') return defaultSettings;
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                return { ...defaultSettings, ...parsed };
            } catch (e) {
                console.error('Failed to parse timezone settings:', e);
            }
        }
        return defaultSettings;
    });
    // Use ref instead of state for hydration tracking to avoid setState in effect
    const isHydrated = useRef(false);

    // Set hydrated flag after mount and sync to localStorage
    useEffect(() => {
        isHydrated.current = true;
    }, []);

    // Save to localStorage on change
    useEffect(() => {
        if (isHydrated.current) {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
        }
    }, [settings]);

    const setTimezone = (tz: string) => {
        setSettings(prev => ({ ...prev, timezone: tz }));
    };

    const setUse24Hour = (use24: boolean) => {
        setSettings(prev => ({ ...prev, use24Hour: use24 }));
    };

    const setDateFormat = (format: TimezoneSettings['dateFormat']) => {
        setSettings(prev => ({ ...prev, dateFormat: format }));
    };

    const autoDetectTimezone = () => {
        const detected = Intl.DateTimeFormat().resolvedOptions().timeZone;
        // Check if it's in our list, otherwise default to UTC
        const found = TIMEZONE_OPTIONS.find(opt => opt.value === detected);
        setTimezone(found ? detected : 'UTC');
    };

    return (
        <TimezoneContext.Provider 
            value={{ 
                settings, 
                setTimezone, 
                setUse24Hour, 
                setDateFormat, 
                autoDetectTimezone 
            }}
        >
            {children}
        </TimezoneContext.Provider>
    );
}

export function useTimezone() {
    const context = useContext(TimezoneContext);
    if (context === undefined) {
        throw new Error('useTimezone must be used within a TimezoneProvider');
    }
    return context;
}
