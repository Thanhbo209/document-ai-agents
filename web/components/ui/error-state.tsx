type ErrorStateProps = {
  message: string;
  action?: React.ReactNode;
};

export function ErrorState({ message, action }: ErrorStateProps) {
  return (
    <div className="rounded-2xl bg-destructive/10 px-4 py-4 ring-1 ring-destructive/20">
      <p className="text-sm font-medium text-destructive">{message}</p>
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}
