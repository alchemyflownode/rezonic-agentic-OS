"""
Organize Files Skill for Phoenix Coworker

Automatically organizes files in directories by type.
"""

import shutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class FileCategory:
    """A file category with extensions and destination"""
    name: str
    extensions: List[str]
    destination: Path


class OrganizeFilesSkill:
    """
    Skill for organizing files by type.
    
    Automatically sorts files into categorized folders.
    """
    
    DEFAULT_CATEGORIES = [
        FileCategory("Documents", 
                    [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt"],
                    None),
        FileCategory("Images",
                    [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
                    None),
        FileCategory("Videos",
                    [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"],
                    None),
        FileCategory("Audio",
                    [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
                    None),
        FileCategory("Archives",
                    [".zip", ".tar", ".gz", ".bz2", ".7z", ".rar", ".xz"],
                    None),
        FileCategory("Code",
                    [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", 
                     ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala"],
                    None),
        FileCategory("Data",
                    [".json", ".xml", ".csv", ".yaml", ".yml", ".sql", ".db"],
                    None),
        FileCategory("Executables",
                    [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".appimage"],
                    None),
    ]
    
    def __init__(self, kernel=None):
        self.kernel = kernel
        self.categories = self._init_categories()
    
    def _init_categories(self) -> List[FileCategory]:
        """Initialize categories with proper destinations"""
        categories = []
        for cat in self.DEFAULT_CATEGORIES:
            dest = None
            if cat.name == "Documents":
                dest = Path.home() / "Documents" / "Organized" / "Documents"
            elif cat.name == "Images":
                dest = Path.home() / "Pictures" / "Organized"
            elif cat.name == "Videos":
                dest = Path.home() / "Videos" / "Organized"
            elif cat.name == "Audio":
                dest = Path.home() / "Music" / "Organized"
            elif cat.name == "Archives":
                dest = Path.home() / "Downloads" / "Archives"
            elif cat.name == "Code":
                dest = Path.home() / "Documents" / "Code" / "Snippets"
            elif cat.name == "Data":
                dest = Path.home() / "Documents" / "Data"
            elif cat.name == "Executables":
                dest = Path.home() / "Downloads" / "Installers"
            
            if dest:
                categories.append(FileCategory(cat.name, cat.extensions, dest))
        
        return categories
    
    async def organize(
        self,
        source_dir: Path,
        dry_run: bool = False,
        recursive: bool = False
    ) -> Dict:
        """
        Organize files in a directory.
        
        Args:
            source_dir: Directory to organize
            dry_run: If True, only show what would be done
            recursive: If True, organize subdirectories too
        
        Returns:
            Organization result
        """
        source = Path(source_dir).expanduser().resolve()
        
        if not source.exists():
            return {"success": False, "error": f"Directory not found: {source}"}
        
        if not source.is_dir():
            return {"success": False, "error": f"Not a directory: {source}"}
        
        # Collect files
        if recursive:
            files = [f for f in source.rglob("*") if f.is_file()]
        else:
            files = [f for f in source.iterdir() if f.is_file()]
        
        if not files:
            return {"success": True, "message": "No files to organize", "moved": 0}
        
        # Categorize files
        categorized = self._categorize_files(files)
        
        # Move files
        moved = 0
        errors = []
        
        for category, file_list in categorized.items():
            if category == "Other":
                continue
            
            cat_info = next((c for c in self.categories if c.name == category), None)
            if not cat_info:
                continue
            
            dest_dir = cat_info.destination
            
            if not dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)
            
            for file_path in file_list:
                try:
                    dest = dest_dir / file_path.name
                    
                    # Handle duplicates
                    counter = 1
                    while dest.exists() and not dry_run:
                        stem = file_path.stem
                        suffix = file_path.suffix
                        dest = dest_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    if dry_run:
                        print(f"Would move: {file_path.name} -> {dest}")
                    else:
                        shutil.move(str(file_path), str(dest))
                    
                    moved += 1
                
                except Exception as e:
                    errors.append(f"{file_path.name}: {e}")
        
        return {
            "success": True,
            "message": f"Organized {moved} files" + (" (dry run)" if dry_run else ""),
            "moved": moved,
            "categories": {k: len(v) for k, v in categorized.items() if v},
            "errors": errors if errors else None
        }
    
    def _categorize_files(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Categorize files by type"""
        categorized = {cat.name: [] for cat in self.categories}
        categorized["Other"] = []
        
        for file_path in files:
            suffix = file_path.suffix.lower()
            categorized_flag = False
            
            for category in self.categories:
                if suffix in category.extensions:
                    categorized[category.name].append(file_path)
                    categorized_flag = True
                    break
            
            if not categorized_flag:
                categorized["Other"].append(file_path)
        
        return categorized
    
    async def clean_empty_dirs(self, source_dir: Path, dry_run: bool = False) -> Dict:
        """
        Remove empty directories.
        
        Args:
            source_dir: Directory to clean
            dry_run: If True, only show what would be done
        
        Returns:
            Cleanup result
        """
        source = Path(source_dir).expanduser().resolve()
        
        removed = 0
        
        for dir_path in sorted(source.rglob("*"), reverse=True):
            if dir_path.is_dir():
                try:
                    if not any(dir_path.iterdir()):
                        if dry_run:
                            print(f"Would remove empty dir: {dir_path}")
                        else:
                            dir_path.rmdir()
                        removed += 1
                except Exception as e:
                    print(f"Could not remove {dir_path}: {e}")
        
        return {
            "success": True,
            "message": f"Removed {removed} empty directories" + (" (dry run)" if dry_run else ""),
            "removed": removed
        }


# Convenience function
async def organize_downloads(dry_run: bool = False) -> Dict:
    """Quick function to organize Downloads folder"""
    skill = OrganizeFilesSkill()
    downloads = Path.home() / "Downloads"
    return await skill.organize(downloads, dry_run=dry_run)
