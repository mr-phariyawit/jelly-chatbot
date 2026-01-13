'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';

export function BotCardSkeleton() {
    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <Skeleton className="h-6 w-32" />
                    <Skeleton className="h-8 w-8 rounded" />
                </div>
                <Skeleton className="h-4 w-48 mt-2" />
            </CardHeader>
            <CardContent>
                <div className="flex flex-col gap-3">
                    <div className="flex justify-between">
                        <Skeleton className="h-4 w-16" />
                        <Skeleton className="h-5 w-14 rounded-full" />
                    </div>
                    <div className="flex justify-between">
                        <Skeleton className="h-4 w-20" />
                        <Skeleton className="h-4 w-6" />
                    </div>
                    <div className="flex justify-between">
                        <Skeleton className="h-4 w-12" />
                        <Skeleton className="h-4 w-6" />
                    </div>
                    <Skeleton className="h-3 w-full mt-2" />
                </div>
            </CardContent>
            <CardFooter>
                <Skeleton className="h-9 w-full" />
            </CardFooter>
        </Card>
    );
}

export function BotsPageSkeleton() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <Skeleton className="h-9 w-24" />
                    <Skeleton className="h-4 w-64 mt-2" />
                </div>
                <Skeleton className="h-10 w-28" />
            </div>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {[1, 2, 3].map((i) => (
                    <BotCardSkeleton key={i} />
                ))}
            </div>
        </div>
    );
}
