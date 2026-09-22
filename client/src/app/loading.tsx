import { Skeleton } from "@/components/ui/skeleton";

export default function RootLoading() {
  return (
    <div className="container mx-auto max-w-7xl px-4 sm:px-8 py-12 space-y-8 animate-in fade-in-50">
      <div className="space-y-4 max-w-2xl mx-auto text-center">
        <Skeleton className="h-8 w-48 mx-auto rounded-full" />
        <Skeleton className="h-12 w-3/4 mx-auto rounded-lg" />
        <Skeleton className="h-6 w-1/2 mx-auto rounded-md" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-8">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-xl border p-6 space-y-4">
            <Skeleton className="h-10 w-10 rounded-lg" />
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        ))}
      </div>
    </div>
  );
}

