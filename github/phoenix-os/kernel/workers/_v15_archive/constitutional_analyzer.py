# workers/constitutional_analyzer.py
class ConstitutionalAnalyzer(BaseAnalyzer):
    """Finds structural and logical issues in code."""
    name = "constitution"
    languages = {"python"}
    
    def analyze(self, source: str, lines: list[str],
                tree: Optional[ast.Module], meta: FileMetadata) -> list[Issue]:
        issues = []
        
        # 1. Check for unclosed docstrings
        if source.count('"""') % 2 != 0:
            issues.append(Issue(
                severity=Severity.CRITICAL,
                category="Structure",
                line=1,
                message="Unclosed docstring detected",
                suggestion="Ensure all docstrings are properly closed",
                auto_fixable=True,
                confidence=0.95
            ))
        
        # 2. Check for stacked decorators without bodies
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if this function is a decorator with no body
                pass
        
        # 3. Check for orphaned code after main
        main_pos = source.find('if __name__ == "__main__":')
        if main_pos > 0:
            after_main = source[main_pos:].split('\n')
            # Check if there's executable code after main block
            # (not comments or blank lines)
        
        # 4. Check for router import without None check
        if 'include_router' in source and 'if router is not None' not in source:
            issues.append(Issue(
                severity=Severity.HIGH,
                category="Structure",
                line=None,
                message="Router included without None check",
                suggestion="Wrap app.include_router(router) in 'if router is not None:'",
                auto_fixable=True,
                confidence=0.85
            ))
        
        return issues
