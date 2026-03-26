"use client";

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CodeBlock } from './CodeBlock';
import { SearchResults } from './SearchResults';
import { DataDisplay } from './DataDisplay';

interface MessageRendererProps {
  content: string;
  loading?: boolean;
}

export const MessageRenderer = ({ content, loading = false }: MessageRendererProps) => {
  // Check if it's search results (starts with "Search Results:")
  if (content.startsWith('Search Results:')) {
    try {
      const lines = content.split('\n').slice(1);
      const results = lines
        .map(line => {
          const match = line.match(/• (.*?)(?:\n|$)/);
          if (!match) return null;
          
          const text = match[1];
          const urlMatch = text.match(/https?:\/\/[^\s]+/);
          const url = urlMatch ? urlMatch[0] : '#';
          const title = text.replace(url, '').replace(/[•\s]+$/, '');
          
          return {
            title: title || text,
            url: url,
            content: text
          };
        })
        .filter(Boolean);
      
      return <SearchResults results={results} />;
    } catch (e) {
      return <DataDisplay data={content} />;
    }
  }
  
  // Check if it's JSON
  try {
    const json = JSON.parse(content);
    if (typeof json === 'object' && json !== null) {
      return <DataDisplay data={json} expandLevel={1} />;
    }
    throw new Error('Not a JSON object');
  } catch {
    // Regular markdown content
    return (
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]} 
        className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-transparent prose-pre:p-0"
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            const code = String(children).replace(/\n$/, '');
            return !inline && match ? (
              <CodeBlock language={match[1]} code={code} />
            ) : (
              <code className="bg-black/30 px-1.5 py-0.5 rounded text-cyan-300 text-xs" {...props}>
                {children}
              </code>
            );
          }
        }}
      >
        {content || (loading ? '⏳ Thinking...' : '')}
      </ReactMarkdown>
    );
  }
};