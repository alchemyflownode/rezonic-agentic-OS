// D:\Rezonic_Agentic\apps\phoenix-frontend\utils\extractCodeFromContent.ts

export interface ExtractedContent {
  code: string | null;
  language: string;
  text: string;
  hasCode: boolean;
}

export const extractCodeFromContent = (content: string): ExtractedContent => {
  // Match triple backtick code blocks: ```lang\ncode```
  const codeBlockMatch = content.match(/```(\w+)?\n([\s\S]*?)```/);
  
  if (codeBlockMatch) {
    const language = codeBlockMatch[1] || "python";
    const code = codeBlockMatch[2].trim();
    const text = content.replace(codeBlockMatch[0], "").trim();
    
    return { code, language, text, hasCode: true };
  }
  
  // Match inline code patterns from streaming responses
  const streamingCodeMatch = content.match(/Generated Code[:\s]*\n```(\w+)?\n([\s\S]*?)```/i);
  if (streamingCodeMatch) {
    const language = streamingCodeMatch[1] || "python";
    const code = streamingCodeMatch[2].trim();
    const text = content.replace(streamingCodeMatch[0], "").trim();
    
    return { code, language, text, hasCode: true };
  }
  
  return { code: null, language: "text", text: content, hasCode: false };
};
