import { useParams } from "react-router-dom";

export function CustomerDetailPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">Customer Detail</h1>
      <p className="text-muted-foreground">
        Customer <span className="font-mono text-foreground">{id}</span> — full
        profile coming in the next slice.
      </p>
    </div>
  );
}
