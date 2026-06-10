# Code Review Report

**Generated**: 2026-03-30T10:14:36.951402  
**File**: `D:\Rezonic_Agentic\apps\phoenix-kernel\code_worker.py`  
**Language**: python  
**Size**: 62,457 bytes (1,734 lines)  
**Health Score**: 0.0/100  
**SHA-256**: `5c46e49a826eb2e7ca64dd1becc3e25d…`

## Summary

| Metric | Value |
|--------|-------|
| Total Issues | 69 |
| Critical | 0 |
| Errors | 7 |
| Warnings | 39 |
| Info | 23 |
| Fixes Applied | 1 |
| Fixes Skipped | 0 |

## Strengths

- ✅ Dataclass usage — clean data modeling
- ✅ Abstract base classes — proper interface design
- ✅ Error handling present
- ✅ Type annotation awareness
- ✅ Test code present
- ✅ Environment-based configuration
- ✅ Resilience patterns (circuit breaker / rate limiter)

## Issues

### Documentation (23)

- ℹ️ **Line 121**: Function 'emoji' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 130**: Function 'weight' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 150**: Function '__str__' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 223**: Function 'error_count' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 230**: Function 'warning_count' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 400**: Function 'analyze' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 526**: Function 'analyze' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 585**: Function 'analyze' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 641**: Function 'analyze' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 694**: Function 'analyze' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 767**: Function 'analyze' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 826**: Function 'analyze' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 880**: Function 'analyze' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 934**: Function 'analyze' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 1036**: Function 'generate_fixes' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 1063**: Function 'generate_fixes' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 1095**: Function 'generate_fixes' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 1142**: Function 'generate_fixes' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 1225**: Function '__init__' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 1046**: Function 'apply' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 1073**: Function 'apply' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 1105**: Function 'apply' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes
- ℹ️ **Line 1154**: Function 'apply' lacks a docstring
  - 💡 Add docstring: purpose, args, returns.
  - Confidence: 85% | Auto-fixable: Yes

### Duplication (28)

- ⚠️ **Line 195**: Lines 195–198 duplicate lines 156–159
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 524**: Lines 524–527 duplicate lines 398–401
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 528**: Lines 528–531 duplicate lines 402–405
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 573**: Lines 573–576 duplicate lines 542–545
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 583**: Lines 583–586 duplicate lines 398–401
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 587**: Lines 587–590 duplicate lines 402–405
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 618**: Lines 618–621 duplicate lines 602–605
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 640**: Lines 640–643 duplicate lines 399–402
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 692**: Lines 692–695 duplicate lines 398–401
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 696**: Lines 696–699 duplicate lines 402–405
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 765**: Lines 765–768 duplicate lines 639–642
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 769**: Lines 769–772 duplicate lines 402–405
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 821**: Lines 821–824 duplicate lines 636–639
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 825**: Lines 825–828 duplicate lines 399–402
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 849**: Lines 849–852 duplicate lines 837–840
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 868**: Lines 868–871 duplicate lines 856–859
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 878**: Lines 878–881 duplicate lines 398–401
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 882**: Lines 882–885 duplicate lines 402–405
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 909**: Lines 909–912 duplicate lines 893–896
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 918**: Lines 918–921 duplicate lines 796–799
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 927**: Lines 927–930 duplicate lines 636–639
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 933**: Lines 933–936 duplicate lines 399–402
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 1062**: Lines 1062–1065 duplicate lines 1035–1038
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 1094**: Lines 1094–1097 duplicate lines 1035–1038
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 1116**: Lines 1116–1119 duplicate lines 1110–1113
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 1141**: Lines 1141–1144 duplicate lines 1035–1038
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 1179**: Lines 1179–1182 duplicate lines 548–551
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 1186**: Lines 1186–1189 duplicate lines 1167–1170
  - 💡 Extract into a shared function or constant.
  - Confidence: 70% | Auto-fixable: No

### Import Order (11)

- ⚠️ **Line 51**: Import 'platform' at line 51 is far from top-level imports
  - 💡 Move to top of file with other imports, or wrap in a function for conditional import.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 52**: Import 're' at line 52 is far from top-level imports
  - 💡 Move to top of file with other imports, or wrap in a function for conditional import.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 53**: Import 'shutil' at line 53 is far from top-level imports
  - 💡 Move to top of file with other imports, or wrap in a function for conditional import.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 54**: Import 'subprocess' at line 54 is far from top-level imports
  - 💡 Move to top of file with other imports, or wrap in a function for conditional import.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 55**: Import 'sys' at line 55 is far from top-level imports
  - 💡 Move to top of file with other imports, or wrap in a function for conditional import.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 56**: Import 'textwrap' at line 56 is far from top-level imports
  - 💡 Move to top of file with other imports, or wrap in a function for conditional import.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 57**: Import 'abc' at line 57 is far from top-level imports
  - 💡 Move to top of file with other imports, or wrap in a function for conditional import.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 58**: Import 'dataclasses' at line 58 is far from top-level imports
  - 💡 Move to top of file with other imports, or wrap in a function for conditional import.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 59**: Import 'enum' at line 59 is far from top-level imports
  - 💡 Move to top of file with other imports, or wrap in a function for conditional import.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 60**: Import 'pathlib' at line 60 is far from top-level imports
  - 💡 Move to top of file with other imports, or wrap in a function for conditional import.
  - Confidence: 70% | Auto-fixable: No
- ⚠️ **Line 61**: Import 'typing' at line 61 is far from top-level imports
  - 💡 Move to top of file with other imports, or wrap in a function for conditional import.
  - Confidence: 70% | Auto-fixable: No

### Security (7)

- ❌ **Line 90**: Unsafe call: eval()
  - 💡 Use ast.literal_eval() or a safe parser
  - Confidence: 90% | Auto-fixable: No
- ❌ **Line 92**: Unsafe call: exec()
  - 💡 Avoid exec(); use structured dispatch
  - Confidence: 90% | Auto-fixable: No
- ❌ **Line 93**: Unsafe call: exec()
  - 💡 Avoid exec(); use structured dispatch
  - Confidence: 90% | Auto-fixable: No
- ❌ **Line 94**: Unsafe call: pickle.load()
  - 💡 Use json or msgpack for serialization
  - Confidence: 90% | Auto-fixable: No
- ❌ **Line 96**: Unsafe call: yaml.load()
  - 💡 Use yaml.safe_load() instead
  - Confidence: 90% | Auto-fixable: No
- ❌ **Line 98**: Unsafe call: __import__()
  - 💡 Use importlib.import_module()
  - Confidence: 90% | Auto-fixable: No
- ❌ **Line 100**: Unsafe call: os.system()
  - 💡 Use subprocess.run() with shell=False
  - Confidence: 90% | Auto-fixable: No

## Fixes Applied

- 🔧 [Documentation] Insert 23 placeholder docstrings (conf=85%)

## Unified Diff

```diff
--- code_worker.py (original)
+++ code_worker.py (fixed)
@@ -119,6 +119,7 @@
 

     @property

     def emoji(self) -> str:

+        """TODO: Document emoji()."""

         return {

             Severity.INFO: "ℹ️",

             Severity.WARNING: "⚠️",

@@ -128,6 +129,7 @@
 

     @property

     def weight(self) -> int:

+        """TODO: Document weight()."""

         return {

             Severity.INFO: 1,

             Severity.WARNING: 2,

@@ -148,6 +150,7 @@
     confidence: float = 1.0

 

     def __str__(self) -> str:

+        """TODO: Document __str__()."""

         loc = f"L{self.line}" if self.line else "—"

         return (

             f"{self.severity.emoji} [{self.category}] "

@@ -221,6 +224,7 @@
 

     @property

     def error_count(self) -> int:

+        """TODO: Document error_count()."""

         return sum(

             1 for i in self.issues

             if i.severity in (Severity.ERROR, Severity.CRITICAL)

@@ -228,6 +232,7 @@
 

     @property

     def warning_count(self) -> int:

+        """TODO: Document warning_count()."""

         return sum(1 for i in self.issues if i.severity == Severity.WARNING)

 

     @property

@@ -401,6 +406,7 @@
         self, source: str, lines: list[str],

         tree: Optional[ast.Module], meta: FileMetadata,

     ) -> list[Issue]:

+        """TODO: Document analyze()."""

         issues: list[Issue] = []

         if not tree:

             return issues

@@ -527,6 +533,7 @@
         self, source: str, lines: list[str],

         tree: Optional[ast.Module], meta: FileMetadata,

     ) -> list[Issue]:

+        """TODO: Document analyze()."""

         issues: list[Issue] = []

         if not tree:

             return issues

@@ -586,6 +593,7 @@
         self, source: str, lines: list[str],

         tree: Optional[ast.Module], meta: FileMetadata,

     ) -> list[Issue]:

+        """TODO: Document analyze()."""

         issues: list[Issue] = []

         if not tree:

             return issues

@@ -642,6 +650,7 @@
         self, source: str, lines: list[str],

         tree: Optional[ast.Module], meta: FileMetadata,

     ) -> list[Issue]:

+        """TODO: Document analyze()."""

         issues: list[Issue] = []

 

         # Hardcoded secrets

@@ -695,6 +704,7 @@
         self, source: str, lines: list[str],

         tree: Optional[ast.Module], meta: FileMetadata,

     ) -> list[Issue]:

+        """TODO: Document analyze()."""

         issues: list[Issue] = []

         if not tree:

             return issues

@@ -768,6 +778,7 @@
         self, source: str, lines: list[str],

         tree: Optional[ast.Module], meta: FileMetadata,

     ) -> list[Issue]:

+        """TODO: Document analyze()."""

         issues: list[Issue] = []

         if not tree:

             return issues

@@ -827,6 +838,7 @@
         self, source: str, lines: list[str],

         tree: Optional[ast.Module], meta: FileMetadata,

     ) -> list[Issue]:

+        """TODO: Document analyze()."""

         issues: list[Issue] = []

         long_lines = 0

 

@@ -881,6 +893,7 @@
         self, source: str, lines: list[str],

         tree: Optional[ast.Module], meta: FileMetadata,

     ) -> list[Issue]:

+        """TODO: Document analyze()."""

         issues: list[Issue] = []

         if not tree:

             return issues

@@ -935,6 +948,7 @@
         self, source: str, lines: list[str],

         tree: Optional[ast.Module], meta: FileMetadata,

     ) -> list[Issue]:

+        """TODO: Document analyze()."""

         issues: list[Issue] = []

         stripped = [l.strip() for l in lines]

 

@@ -1036,6 +1050,7 @@
     def generate_fixes(

         self, source: str, issues: list[Issue], meta: FileMetadata,

     ) -> list[Fix]:

+        """TODO: Document generate_fixes()."""

         ws_issues = [

             i for i in issues

             if i.category == "Style" and "Trailing whitespace" in i.message

@@ -1044,6 +1059,7 @@
             return []

 

         def apply(src: str) -> str:

+            """TODO: Document apply()."""

             return "\n".join(line.rstrip() for line in src.split("\n"))

 

         return [Fix(

@@ -1063,6 +1079,7 @@
     def generate_fixes(

         self, source: str, issues: list[Issue], meta: FileMetadata,

     ) -> list[Fix]:

+        """TODO: Document generate_fixes()."""

         bare = [

             i for i in issues

             if i.category == "Error Handling" and "Bare" in i.message

@@ -1071,6 +1088,7 @@
             return []

 

         def apply(src: str) -> str:

+            """TODO: Document apply()."""

             return re.sub(

                 r"^(\s*)except\s*:\s*$",

                 r"\1except Exception:",

@@ -1095,6 +1113,7 @@
     def generate_fixes(

         self, source: str, issues: list[Issue], meta: FileMetadata,

     ) -> list[Fix]:

+        """TODO: Document generate_fixes()."""

         secret_issues = [

             i for i in issues

             if i.category == "Security" and "secret" in i.message.lower()

@@ -1103,6 +1122,7 @@
             return []

 

         def apply(src: str) -> str:

+            """TODO: Document apply()."""

             result = src

             result = re.sub(

                 r"""(api[_-]?key\s*=\s*)(['"])([^'"]{10,})\2""",

@@ -1142,6 +1162,7 @@
     def generate_fixes(

         self, source: str, issues: list[Issue], meta: FileMetadata,

     ) -> list[Fix]:

+        """TODO: Document generate_fixes()."""

         doc_issues = [

             i for i in issues

             if (i.category == "Documentation"

@@ -1152,6 +1173,7 @@
             return []

 

         def apply(src: str) -> str:

+            """TODO: Document apply()."""

             try:

                 tree = ast.parse(src)

             except SyntaxError:

@@ -1228,6 +1250,7 @@
         dry_run: bool = False,

         verbose: bool = False,

     ):

+        """TODO: Document __init__()."""

         self.fix_confidence = fix_confidence

         self.dry_run = dry_run

         self.verbose = verbose

```
