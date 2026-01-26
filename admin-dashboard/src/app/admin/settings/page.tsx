'use client';

import { useTimezone, TIMEZONE_OPTIONS } from '@/lib/timezone-context';
import { useFormattedDate } from '@/hooks/use-formatted-date';
import { useState, useEffect } from 'react';
import { Clock, Globe, Settings } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import TimezoneMap from '@/components/timezone-map';

export default function SettingsPage() {
    const { settings, setTimezone, setUse24Hour, autoDetectTimezone } = useTimezone();
    const { formatDate, formatTimeOnly, getTimezoneAbbr } = useFormattedDate();
    const [currentTime, setCurrentTime] = useState(new Date());

    // Update current time every second for live preview
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    const selectedTz = TIMEZONE_OPTIONS.find(opt => opt.value === settings.timezone);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-500/20">
                    <Clock className="h-6 w-6 text-purple-400" />
                </div>
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Time Display Preferences</h2>
                    <p className="text-muted-foreground">
                        Configure how dates and times are displayed throughout the dashboard.
                    </p>
                </div>
            </div>

            {/* World Map Card */}
            <Card className="border-purple-500/30 bg-gradient-to-br from-purple-950/30 to-transparent">
                <CardContent className="pt-6">
                    {/* Interactive Leaflet Map */}
                    <div className="relative mb-4">
                        <TimezoneMap 
                            selectedTimezone={settings.timezone}
                            onTimezoneChange={setTimezone}
                        />
                        
                        {/* Timezone info bar overlay */}
                        <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between z-[1000]">
                            <div className="flex items-center gap-2 bg-slate-900/90 backdrop-blur px-4 py-2 rounded-full border border-slate-700/50">
                                <Globe className="h-4 w-4 text-purple-400" />
                                <span className="text-sm font-medium text-white">
                                    {selectedTz?.label || settings.timezone}
                                </span>
                                <span className="text-xs text-slate-400">
                                    {selectedTz?.offset}
                                </span>
                            </div>
                            <Button 
                                variant="outline" 
                                size="sm"
                                onClick={autoDetectTimezone}
                                className="border-purple-500/50 hover:bg-purple-500/20 bg-slate-900/80 backdrop-blur"
                            >
                                <Globe className="h-3.5 w-3.5 mr-1.5" />
                                Auto-detect
                            </Button>
                        </div>
                    </div>

                    {/* Timezone Selector */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <Label htmlFor="timezone" className="text-base">Select Timezone</Label>
                            <select 
                                id="timezone"
                                value={settings.timezone} 
                                onChange={(e) => setTimezone(e.target.value)}
                                className="w-64 h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                            >
                                {TIMEZONE_OPTIONS.map((tz) => (
                                    <option key={tz.value} value={tz.value}>
                                        {tz.label} ({tz.offset})
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* 24-hour toggle */}
                        <div className="flex items-center justify-between py-4 border-t border-border/50">
                            <div>
                                <Label htmlFor="24hour" className="text-base">Use 24-hour format</Label>
                                <p className="text-sm text-muted-foreground">
                                    Display time in 24-hour format instead of AM/PM
                                </p>
                            </div>
                            <Switch
                                id="24hour"
                                checked={settings.use24Hour}
                                onCheckedChange={setUse24Hour}
                            />
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Format Preview Cards */}
            <div className="grid gap-4 md:grid-cols-3">
                <Card className="text-center">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            12-hour Format
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold">
                            {formatTimeOnly(currentTime).replace(/:\d{2}(?=\s|$)/, '')}
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                            Standard 12-hour display with AM/PM indicators
                        </p>
                    </CardContent>
                </Card>

                <Card className="text-center border-purple-500/50 bg-purple-500/5">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-purple-400">
                            24-hour Format
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-purple-300">
                            {new Date(currentTime).toLocaleTimeString('en-GB', { 
                                hour: '2-digit', 
                                minute: '2-digit',
                                timeZone: settings.timezone 
                            })}
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                            Military or 24-hour clock display
                        </p>
                    </CardContent>
                </Card>

                <Card className="text-center">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            Styled Format
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold flex items-center justify-center gap-2">
                            <span>
                                {new Date(currentTime).toLocaleTimeString('en-GB', { 
                                    hour: '2-digit', 
                                    minute: '2-digit',
                                    timeZone: settings.timezone 
                                })}
                            </span>
                            <span className="text-sm px-2 py-1 bg-muted rounded">
                                {new Date(currentTime).toLocaleDateString('en-US', { 
                                    weekday: 'short',
                                    day: 'numeric',
                                    month: 'short',
                                    timeZone: settings.timezone 
                                })}
                            </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                            Combined time, day, and date with modern styling
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Info Note */}
            <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/50 border border-border/50">
                <Settings className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                    <p className="text-sm text-muted-foreground">
                        All system timestamps are stored in UTC and converted for display based on your preferences. 
                        Changes are automatically saved and will apply across all pages.
                    </p>
                </div>
            </div>

            {/* User Management Section */}
            <div className="pt-10 border-t border-border/50">
                <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 rounded-lg bg-yellow-500/20">
                        <Settings className="h-6 w-6 text-yellow-400" />
                    </div>
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">User Management</h2>
                        <p className="text-muted-foreground">
                            Approve new users and manage access roles.
                        </p>
                    </div>
                </div>

                <UserList />
            </div>
        </div>
    );
}

function UserList() {
    const [users, setUsers] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            const apiUrl = 'https://session-api-1088865818405.us-central1.run.app';
            const res = await fetch(`${apiUrl}/users`);
            if (res.ok) {
                const data = await res.json();
                setUsers(data);
            }
        } catch (error) {
            console.error('Failed to fetch users:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const toggleApproval = async (userId: string, currentStatus: boolean) => {
        try {
            const apiUrl = 'https://session-api-1088865818405.us-central1.run.app';
            const res = await fetch(`${apiUrl}/users/${userId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_approved: !currentStatus })
            });
            if (res.ok) {
                setUsers(users.map(u => u.id === userId ? { ...u, is_approved: !currentStatus } : u));
            }
        } catch (error) {
            console.error('Failed to update user approval:', error);
        }
    };

    if (isLoading) {
        return <div className="p-8 text-center text-muted-foreground italic">Loading users...</div>;
    }

    return (
        <Card className="border-yellow-500/20">
            <CardHeader>
                <CardTitle>Registered Admins</CardTitle>
                <CardDescription>Only approved users can access the dashboard.</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {users.length === 0 ? (
                        <p className="text-center py-4 text-muted-foreground">No users found.</p>
                    ) : (
                        users.map((user) => (
                            <div key={user.id} className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border/50">
                                <div className="flex items-center gap-4">
                                    <div className="h-10 w-10 rounded-full bg-yellow-500/10 flex items-center justify-center text-yellow-500 font-bold border border-yellow-500/20">
                                        {user.name?.[0]?.toUpperCase() || user.email[0].toUpperCase()}
                                    </div>
                                    <div>
                                        <div className="font-medium text-white">{user.name || 'Unknown'}</div>
                                        <div className="text-xs text-muted-foreground">{user.email}</div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-8">
                                    <div className="text-right">
                                        <div className={`text-xs px-2 py-0.5 rounded-full inline-block ${
                                            user.role === 'super-admin' 
                                                ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30' 
                                                : user.is_approved 
                                                    ? 'bg-green-500/10 text-green-400 border border-green-500/30' 
                                                    : 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/30'
                                        }`}>
                                            {user.role === 'super-admin' ? 'Super Admin' : user.is_approved ? 'Active' : 'Pending'}
                                        </div>
                                        <div className="text-[10px] text-muted-foreground mt-1">Role: {user.role}</div>
                                    </div>
                                    <Switch
                                        checked={user.is_approved}
                                        disabled={user.role === 'super-admin'}
                                        onCheckedChange={() => toggleApproval(user.id, user.is_approved)}
                                    />
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
