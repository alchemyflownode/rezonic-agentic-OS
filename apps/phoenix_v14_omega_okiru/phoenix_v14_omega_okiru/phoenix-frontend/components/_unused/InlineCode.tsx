// frontend/components/InlineCode.tsx
export const InlineCode: React.FC<{ children: string }> = ({ children }) => {
  return (
    <code
      className="px-1.5 py-0.5 rounded text-[12px] font-mono"
      style={{
        backgroundColor: '#24283b',
        color: '#9ece6a',
        border: '1px solid #292e42',
        fontFamily: '"JetBrains Mono", monospace',
      }}
    >
      {children}
    </code>
  );
};