"use client";

import { X, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";

interface UploadProgressProps {
    filename: string;
    total: number;
    loaded: number;
    percent: number;
    speed: number;
    eta: number;
    onCancel?: () => void;
}

function formatBytes(bytes: number): string {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function formatSpeed(bytesPerSec: number): string {
    return formatBytes(bytesPerSec) + "/s";
}

function formatEta(seconds: number): string {
    if (seconds <= 0 || !isFinite(seconds)) return "calculating...";
    if (seconds < 60) return `~${Math.round(seconds)}s remaining`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `~${minutes}m ${secs}s remaining`;
}

export function UploadProgress({
    filename,
    total,
    loaded,
    percent,
    speed,
    eta,
    onCancel,
}: UploadProgressProps) {
    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-card border border-border rounded-lg p-6 w-full max-w-md shadow-xl">
                {/* File Icon & Name */}
                <div className="flex items-center gap-3 mb-4">
                    <FileText className="h-10 w-10 text-yellow-500" />
                    <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{filename}</p>
                        <p className="text-sm text-muted-foreground">
                            {formatBytes(loaded)} / {formatBytes(total)}
                        </p>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="relative h-6 bg-muted rounded-full overflow-hidden mb-3">
                    <div
                        className="absolute inset-y-0 left-0 bg-gradient-to-r from-yellow-500 to-yellow-400 transition-all duration-300"
                        style={{ width: `${percent}%` }}
                    >
                        {/* Animated stripes */}
                        <div className="absolute inset-0 bg-[linear-gradient(45deg,rgba(255,255,255,0.15)_25%,transparent_25%,transparent_50%,rgba(255,255,255,0.15)_50%,rgba(255,255,255,0.15)_75%,transparent_75%)] bg-[length:1rem_1rem] animate-[stripes_1s_linear_infinite]" />
                    </div>
                    <span className="absolute inset-0 flex items-center justify-center text-sm font-medium">
                        {percent}%
                    </span>
                </div>

                {/* Speed & ETA */}
                <div className="flex justify-between text-sm text-muted-foreground mb-4">
                    <span>{formatSpeed(speed)}</span>
                    <span>{formatEta(eta)}</span>
                </div>

                {/* Cancel Button */}
                {onCancel && (
                    <div className="flex justify-center">
                        <Button
                            variant="destructive"
                            size="sm"
                            onClick={onCancel}
                            className="gap-2"
                        >
                            <X className="h-4 w-4" />
                            Cancel Upload
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );
}
