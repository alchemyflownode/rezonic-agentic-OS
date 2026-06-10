"""
Code Review Skill for Phoenix Coworker

Reviews code changes and provides feedback.
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class CodeIssue:
    """A code issue found during review"""
    severity: str  # error, warning, info
    line: int
    message: str
    suggestion: str


class CodeReviewSkill:
    """
    Skill for reviewing code.
    
    Supports:
    - Git diff review
    - File review
    - Static analysis integration
    """
    
    def __init__(self, kernel=None):
        self.kernel = kernel
    
    async def review_git_changes(self, repo_path: Path = None) -> Dict:
        """
        Review recent git changes.
        
        Args:
            repo_path: Path to git repository
        
        Returns:
            Review result
        """
        repo = Path(repo_path).expanduser().resolve() if repo_path else Path.cwd()
        
        # Get git diff
        diff = await self._get_git_diff(repo)
        
        if not diff:
            return {"success": True, "message": "No changes to review", "issues": []}
        
        # Review with brain
        review = await self._review_with_brain(diff)
        
        # Run static analysis if available
        static_issues = await self._run_static_analysis(repo)
        
        # Save review
        await self._save_review(repo, diff, review, static_issues)
        
        return {
            "success": True,
            "files_changed": len(self._extract_changed_files(diff)),
            "review": review,
            "static_issues": static_issues,
            "total_issues": len(static_issues)
        }
    
    async def review_file(self, file_path: Path) -> Dict:
        """
        Review a single file.
        
        Args:
            file_path: Path to file
        
        Returns:
            Review result
        """
        path = Path(file_path).expanduser().resolve()
        
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        # Read file
        try:
            content = path.read_text()
        except Exception as e:
            return {"success": False, "error": f"Cannot read file: {e}"}
        
        # Review with brain
        review = await self._review_with_brain(content, str(path))
        
        return {
            "success": True,
            "file": str(path),
            "review": review
        }
    
    async def _get_git_diff(self, repo: Path) -> str:
        """Get git diff for repository"""
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD~1"],
                cwd=repo,
                capture_output=True,
                text=True
            )
            return result.stdout
        except Exception as e:
            print(f"Could not get git diff: {e}")
            return ""
    
    def _extract_changed_files(self, diff: str) -> List[str]:
        """Extract list of changed files from diff"""
        files = []
        for line in diff.split('\n'):
            if line.startswith('diff --git'):
                parts = line.split()
                if len(parts) >= 4:
                    files.append(parts[-1])
        return files
    
    async def _review_with_brain(self, code: str, filename: str = "") -> str:
        """Review code using brain worker"""
        if self.kernel and hasattr(self.kernel, 'get_worker'):
            brain = self.kernel.get_worker('brain')
            if brain:
                # Truncate if too long
                truncated = code[:6000] if len(code) > 6000 else code
                
                prompt = f"""Review the following code changes for:
1. Bugs or logical errors
2. Security issues
3. Performance concerns
4. Code style improvements
5. Best practices

{filename}
```
{truncated}
```

Provide specific, actionable feedback."""
                
                result = await brain.process(prompt, {})
                return result.get('response', 'Could not review code')
        
        return "Brain worker not available for code review"
    
    async def _run_static_analysis(self, repo: Path) -> List[Dict]:
        """Run static analysis tools"""
        issues = []
        
        # Try pylint for Python
        try:
            result = subprocess.run(
                ["pylint", "--output-format=json", str(repo)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                import json
                pylint_issues = json.loads(result.stdout)
                for issue in pylint_issues:
                    issues.append({
                        "tool": "pylint",
                        "severity": issue.get("type", "warning"),
                        "line": issue.get("line", 0),
                        "message": issue.get("message", ""),
                        "symbol": issue.get("symbol", "")
                    })
        except:
            pass
        
        # Try flake8
        try:
            result = subprocess.run(
                ["flake8", "--format=%(row)d:%(col)d:%(code)s:%(text)s", str(repo)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        issues.append({
                            "tool": "flake8",
                            "severity": "warning",
                            "line": int(parts[0]),
                            "code": parts[2],
                            "message": parts[3]
                        })
        except:
            pass
        
        return issues
    
    async def _save_review(self, repo: Path, diff: str, review: str, issues: List[Dict]):
        """Save review to notes"""
        notes_dir = Path.home() / "Documents" / "Notes" / "CodeReviews"
        notes_dir.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d_%H%M")
        review_file = notes_dir / f"code_review_{date_str}.md"
        
        content = f"""# Code Review - {repo.name}

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Repository:** {repo}

## AI Review

{review}

## Static Analysis Issues ({len(issues)})

"""
        for issue in issues:
            content += f"- **{issue.get('tool', 'unknown')}** (Line {issue.get('line', 'N/A')}): {issue.get('message', '')}\n"
        
        content += "\n---\n*Generated by Phoenix Coworker*\n"
        
        review_file.write_text(content)


# Convenience function
async def review_git_changes(repo_path: str = None) -> Dict:
    """Quick function to review git changes"""
    skill = CodeReviewSkill()
    return await skill.review_git_changes(Path(repo_path) if repo_path else None)
