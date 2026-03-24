// app/system/layout.tsx
// This layout exists because Next.js requires it for the /system route
// But we don't want to add another sidebar since root layout already has it
export default function SystemLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
