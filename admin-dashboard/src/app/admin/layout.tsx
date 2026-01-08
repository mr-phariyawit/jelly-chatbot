import { AdminSidebar } from '@/components/admin-sidebar';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen w-full overflow-hidden">
        <AdminSidebar />
        <main className="flex-1 overflow-y-auto bg-muted/10">
            <div className="container mx-auto p-6 max-w-6xl">
                {children}
            </div>
        </main>
    </div>
  );
}
