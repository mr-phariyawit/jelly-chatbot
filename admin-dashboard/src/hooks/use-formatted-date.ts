'use client';

import { useCallback } from 'react';
import { format as dateFnsFormat } from 'date-fns';
import { toZonedTime, format as formatTz } from 'date-fns-tz';
import { useTimezone } from '@/lib/timezone-context';

export function useFormattedDate() {
    const { settings } = useTimezone();

    const formatDate = useCallback((date: Date | string, customFormat?: string) => {
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        
        // Convert to target timezone
        const zonedDate = toZonedTime(dateObj, settings.timezone);
        
        // Build format string based on settings
        let formatStr = customFormat;
        
        if (!formatStr) {
            // Default format based on user preferences
            const dateFormatMap = {
                'DD/MM/YYYY': 'dd/MM/yyyy',
                'MM/DD/YYYY': 'MM/dd/yyyy',
                'YYYY-MM-DD': 'yyyy-MM-dd',
            };
            
            const timeFormat = settings.use24Hour ? 'HH:mm' : 'hh:mm a';
            formatStr = `${dateFormatMap[settings.dateFormat]} ${timeFormat}`;
        }
        
        return formatTz(zonedDate, formatStr, { timeZone: settings.timezone });
    }, [settings]);

    const formatDateOnly = useCallback((date: Date | string) => {
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        const zonedDate = toZonedTime(dateObj, settings.timezone);
        
        const dateFormatMap = {
            'DD/MM/YYYY': 'dd/MM/yyyy',
            'MM/DD/YYYY': 'MM/dd/yyyy',
            'YYYY-MM-DD': 'yyyy-MM-dd',
        };
        
        return formatTz(zonedDate, dateFormatMap[settings.dateFormat], { timeZone: settings.timezone });
    }, [settings]);

    const formatTimeOnly = useCallback((date: Date | string) => {
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        const zonedDate = toZonedTime(dateObj, settings.timezone);
        
        const timeFormat = settings.use24Hour ? 'HH:mm:ss' : 'hh:mm:ss a';
        return formatTz(zonedDate, timeFormat, { timeZone: settings.timezone });
    }, [settings]);

    const formatRelative = useCallback((date: Date | string) => {
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        const zonedDate = toZonedTime(dateObj, settings.timezone);
        
        // PP = readable date, p = time
        const dateFormatMap = {
            'DD/MM/YYYY': 'dd MMM yyyy',
            'MM/DD/YYYY': 'MMM dd, yyyy',
            'YYYY-MM-DD': 'yyyy-MM-dd',
        };
        
        const timeFormat = settings.use24Hour ? 'HH:mm' : 'h:mm a';
        return formatTz(zonedDate, `${dateFormatMap[settings.dateFormat]}, ${timeFormat}`, { timeZone: settings.timezone });
    }, [settings]);

    const getTimezoneAbbr = useCallback(() => {
        const now = new Date();
        const zonedDate = toZonedTime(now, settings.timezone);
        return formatTz(zonedDate, 'zzz', { timeZone: settings.timezone });
    }, [settings]);

    return {
        formatDate,
        formatDateOnly,
        formatTimeOnly,
        formatRelative,
        getTimezoneAbbr,
        timezone: settings.timezone,
        use24Hour: settings.use24Hour,
    };
}
