'use client';

import { useState, useEffect } from 'react';
import { Wifi, WifiOff, AlertCircle, CheckCircle2, ShieldCheck } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface ApiStatusIndicatorProps {
  isCollapsed?: boolean;
}

export function ApiStatusIndicator({ isCollapsed }: ApiStatusIndicatorProps) {
  const [status, setStatus] = useState<'checking' | 'online' | 'offline' | 'cors_error'>('checking');
  const [version, setVersion] = useState<string | null>(null);

  useEffect(() => {
    const checkApi = async () => {
      const apiUrl = "https://session-api-1088865818405.us-central1.run.app";
      // const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://session-api-687023036300.us-central1.run.app";
      try {
        const start = Date.now();
        const res = await fetch(`${apiUrl}/health`, { 
          method: 'GET',
          mode: 'cors',
          cache: 'no-store'
        });
        
        if (res.ok) {
          setStatus('online');
          // Try to get version from a known header or just set to OK
          setVersion('1.2.2'); // Current known version
        } else {
          setStatus('offline');
        }
      } catch (e: any) {
        console.error('API Check Failed:', e);
        if (e.message.includes('Failed to fetch') || e.message.includes('CORS')) {
          setStatus('cors_error');
        } else {
          setStatus('offline');
        }
      }
    };

    checkApi();
    const interval = setInterval(checkApi, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (isCollapsed) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex justify-center">
              {status === 'online' ? (
                <Wifi className="h-4 w-4 text-emerald-500" />
              ) : status === 'cors_error' ? (
                <ShieldCheck className="h-4 w-4 text-amber-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-rose-500" />
              )}
            </div>
          </TooltipTrigger>
          <TooltipContent side="right">
            {status === 'online' ? `System Online (v${version})` : 
             status === 'cors_error' ? 'Security Policy Block (CORS)' : 'System Offline'}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <div className={cn(
      "flex flex-col gap-2 p-3 rounded-lg border text-xs transition-colors",
      status === 'online' ? "bg-emerald-50/50 border-emerald-100 dark:bg-emerald-950/10 dark:border-emerald-900/30" :
      status === 'cors_error' ? "bg-amber-50/50 border-amber-100 dark:bg-amber-950/10 dark:border-amber-900/30" :
      "bg-rose-50/50 border-rose-100 dark:bg-rose-950/10 dark:border-rose-900/30"
    )}>
      <div className="flex items-center justify-between">
        <span className="font-medium text-muted-foreground uppercase tracking-wider">System Link</span>
        {status === 'online' ? (
          <CheckCircle2 className="h-3 w-3 text-emerald-500" />
        ) : (
          <AlertCircle className="h-3 w-3 text-rose-500" />
        )}
      </div>
      
      <div className="flex items-center gap-2">
        <div className={cn(
          "h-2 w-2 rounded-full",
          status === 'online' ? "bg-emerald-500 animate-pulse" :
          status === 'cors_error' ? "bg-amber-500" : "bg-rose-500"
        )} />
        <span className="font-semibold">
          {status === 'checking' ? 'Connecting...' :
           status === 'online' ? 'System Stable' :
           status === 'cors_error' ? 'Connection Blocked' : 'System Unreachable'}
        </span>
      </div>

      {status === 'cors_error' && (
        <p className="text-[10px] text-amber-700 dark:text-amber-400 mt-1">
          Browser blocked access. Please clear cache or try private mode.
        </p>
      )}
      
      {status === 'online' && version && (
        <span className="text-[10px] text-muted-foreground">Version {version}</span>
      )}
    </div>
  );
}
