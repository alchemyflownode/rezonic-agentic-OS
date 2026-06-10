"""
Summarize Skill for Phoenix Coworker

Summarizes documents, web pages, and text content.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SummaryResult:
    """Result of a summarization"""
    original_length: int
    summary_length: int
    summary: str
    key_points: List[str]
    source: str


class SummarizeSkill:
    """
    Skill for summarizing content.
    
    Supports:
    - Text files
    - PDF documents
    - Web pages
    - Any text content
    """
    
    def __init__(self, kernel=None):
        self.kernel = kernel
        self.max_chunk_size = 4000  # For LLM processing
    
    async def summarize_file(self, file_path: Path) -> Dict:
        """
        Summarize a file.
        
        Args:
            file_path: Path to file
        
        Returns:
            Summary result
        """
        path = Path(file_path).expanduser().resolve()
        
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        # Read content based on file type
        suffix = path.suffix.lower()
        
        if suffix == '.pdf':
            content = await self._read_pdf(path)
        elif suffix in ['.txt', '.md', '.rst']:
            content = path.read_text()
        elif suffix in ['.docx', '.doc']:
            content = await self._read_docx(path)
        else:
            # Try to read as text
            try:
                content = path.read_text()
            except:
                return {"success": False, "error": f"Cannot read file type: {suffix}"}
        
        if not content:
            return {"success": False, "error": "Could not extract content from file"}
        
        # Generate summary
        summary = await self._generate_summary(content)
        
        # Extract key points
        key_points = await self._extract_key_points(content)
        
        # Save summary to notes
        await self._save_summary(path, summary, key_points)
        
        return {
            "success": True,
            "source": str(path),
            "original_length": len(content),
            "summary_length": len(summary),
            "summary": summary,
            "key_points": key_points
        }
    
    async def summarize_text(self, text: str, max_length: int = 500) -> Dict:
        """
        Summarize raw text.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length
        
        Returns:
            Summary result
        """
        if not text.strip():
            return {"success": False, "error": "Empty text"}
        
        summary = await self._generate_summary(text, max_length)
        key_points = await self._extract_key_points(text)
        
        return {
            "success": True,
            "original_length": len(text),
            "summary_length": len(summary),
            "summary": summary,
            "key_points": key_points
        }
    
    async def _generate_summary(self, content: str, max_length: int = 500) -> str:
        """Generate summary using brain worker"""
        if self.kernel and hasattr(self.kernel, 'get_worker'):
            brain = self.kernel.get_worker('brain')
            if brain:
                # Truncate if too long
                if len(content) > self.max_chunk_size:
                    content = content[:self.max_chunk_size] + "..."
                
                prompt = f"""Please provide a concise summary (max {max_length} characters) of the following content:

{content}

Summary:"""
                
                result = await brain.process(prompt, {})
                return result.get('response', 'Could not generate summary')
        
        # Fallback: simple extractive summary
        return self._simple_summary(content, max_length)
    
    def _simple_summary(self, content: str, max_length: int) -> str:
        """Simple extractive summarization"""
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        # Take first few sentences that fit
        summary = []
        length = 0
        
        for sentence in sentences:
            if length + len(sentence) > max_length:
                break
            summary.append(sentence)
            length += len(sentence)
        
        return ' '.join(summary) if summary else content[:max_length]
    
    async def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content"""
        if self.kernel and hasattr(self.kernel, 'get_worker'):
            brain = self.kernel.get_worker('brain')
            if brain:
                truncated = content[:self.max_chunk_size] if len(content) > self.max_chunk_size else content
                
                prompt = f"""Extract 3-5 key points from the following content. List them as bullet points:

{truncated}

Key points:"""
                
                result = await brain.process(prompt, {})
                response = result.get('response', '')
                
                # Parse bullet points
                points = [p.strip('- *').strip() for p in response.split('\n') if p.strip().startswith(('-', '*'))]
                return points[:5]
        
        # Fallback
        return []
    
    async def _read_pdf(self, path: Path) -> str:
        """Read PDF content"""
        try:
            import PyPDF2
            
            text = []
            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text())
            
            return '\n'.join(text)
        
        except ImportError:
            return ""
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    async def _read_docx(self, path: Path) -> str:
        """Read DOCX content"""
        try:
            import docx
            
            doc = docx.Document(path)
            paragraphs = [p.text for p in doc.paragraphs]
            return '\n'.join(paragraphs)
        
        except ImportError:
            return ""
        except Exception as e:
            print(f"Error reading DOCX: {e}")
            return ""
    
    async def _save_summary(self, source: Path, summary: str, key_points: List[str]):
        """Save summary to notes folder"""
        notes_dir = Path.home() / "Documents" / "Notes" / "Summaries"
        notes_dir.mkdir(parents=True, exist_ok=True)
        
        summary_file = notes_dir / f"{source.stem}_summary.md"
        
        content = f"""# Summary: {source.name}

**Source:** {source}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Summary

{summary}

## Key Points

"""
        for point in key_points:
            content += f"- {point}\n"
        
        content += "\n---\n*Generated by Phoenix Coworker*\n"
        
        summary_file.write_text(content)


# Convenience function
async def summarize_file(file_path: str) -> Dict:
    """Quick function to summarize a file"""
    skill = SummarizeSkill()
    return await skill.summarize_file(Path(file_path))
