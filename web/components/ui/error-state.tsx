type ErrorStateProps = {
  message: string;
};

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <div className="rounded-2xl bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive ring-1 ring-destructive/20">
      {message}
    </div>
  );
}
