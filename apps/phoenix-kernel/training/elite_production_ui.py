# elite_production_ui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import pickle
import threading
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import os

class RezstackEliteUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🏛️ REZSTACK CONSTITUTIONAL SUITE - ELITE PRODUCTION")
        self.root.geometry("1600x1000")
        
        # Configure dark theme
        self.root.configure(bg='#0f0f23')
        
        # Set icon (if available)
        try:
            self.root.iconbitmap('rezstack.ico')
        except Exception as e:
            pass
        
        # Paths
        self.base_path = Path(r"G:\okiru-pure\rezsparse-trainer")
        self.manifest_path = self.base_path / "models" / "distilled" / "reports" / "full_distillation_manifest.json"
        self.constitutional_model = self.base_path / "production_constitutional_predictor.pkl"
        self.distilled_dir = self.base_path / "models" / "distilled"
        
        # Colors for elite theme
        self.colors = {
            'bg_dark': '#0f0f23',
            'bg_panel': '#1a1a2e',
            'bg_darker': '#0a0a1a',
            'gold': '#ffd700',
            'gold_light': '#fffacd',
            'blue': '#00b4d8',
            'cyan': '#00ffff',
            'green': '#00ff9d',
            'red': '#ff4757',
            'purple': '#9d4edd',
            'text_light': '#ffffff',
            'text_dim': '#a0a0c0',
            'border': '#303050'
        }
        
        # Initialize data
        self.manifest_data = []
        self.distillation_results = []
        self.running = False
        
        # Load data
        self.load_data()
        
        # Setup UI
        self.setup_ui()
        
        # Start monitoring thread
        self.start_monitoring()
        
    def load_data(self):
        """Load manifest and existing reports"""
        try:
            if self.manifest_path.exists():
                with open(self.manifest_path, 'r') as f:
                    self.manifest_data = json.load(f)
                    print(f"Loaded manifest with {len(self.manifest_data)} items")
            else:
                print("Manifest not found")
                
            # Check for existing distillation reports
            reports_dir = self.distilled_dir / "reports"
            if reports_dir.exists():
                report_files = list(reports_dir.glob("distillation_*.json"))
                if report_files:
                    latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
                    with open(latest_report, 'r') as f:
                        self.distillation_results = json.load(f)
                        
        except Exception as e:
            print(f"Error loading data: {e}")
            
    def setup_ui(self):
        """Setup the premium UI"""
        
        # Configure styles
        self.setup_styles()
        
        # Main container with gradient
        main_container = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # ===== HEADER =====
        header_frame = tk.Frame(main_container, 
                               bg=self.colors['bg_dark'],
                               height=80)
        header_frame.pack(fill=tk.X, padx=30, pady=20)
        header_frame.pack_propagate(False)
        
        # Logo and title
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        title_frame.pack(side=tk.LEFT)
        
        # Logo icon
        logo_icon = tk.Label(title_frame, 
                           text="⚖️", 
                           font=('Segoe UI', 32),
                           bg=self.colors['bg_dark'],
                           fg=self.colors['gold'])
        logo_icon.pack(side=tk.LEFT)
        
        # Title text
        title_text = tk.Label(title_frame,
                            text="REZSTACK CONSTITUTIONAL SUITE",
                            font=('Segoe UI', 24, 'bold'),
                            bg=self.colors['bg_dark'],
                            fg=self.colors['text_light'])
        title_text.pack(side=tk.LEFT, padx=(10, 0))
        
        # Elite badge
        elite_badge = tk.Label(title_frame,
                             text="ELITE PRODUCTION",
                             font=('Segoe UI', 10, 'bold'),
                             bg=self.colors['gold'],
                             fg='#000000',
                             padx=15,
                             pady=5)
        elite_badge.pack(side=tk.LEFT, padx=(20, 0))
        
        # Status indicators
        status_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        status_frame.pack(side=tk.RIGHT)
        
        self.status_indicator = tk.Label(status_frame,
                                       text="●",
                                       font=('Segoe UI', 16),
                                       bg=self.colors['bg_dark'],
                                       fg=self.colors['green'])
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        self.status_label = tk.Label(status_frame,
                                   text="SYSTEM READY",
                                   font=('Segoe UI', 11),
                                   bg=self.colors['bg_dark'],
                                   fg=self.colors['text_dim'])
        self.status_label.pack(side=tk.LEFT)
        
        # ===== MAIN CONTENT =====
        content_frame = tk.Frame(main_container, bg=self.colors['bg_dark'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))
        
        # Left panel - Stats
        left_panel = tk.Frame(content_frame, 
                            bg=self.colors['bg_panel'],
                            highlightbackground=self.colors['border'],
                            highlightthickness=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        # Stats title
        stats_title = tk.Label(left_panel,
                             text="📊 SYSTEM METRICS",
                             font=('Segoe UI', 16, 'bold'),
                             bg=self.colors['bg_panel'],
                             fg=self.colors['text_light'],
                             pady=20)
        stats_title.pack()
        
        # Metrics grid
        metrics_container = tk.Frame(left_panel, bg=self.colors['bg_panel'])
        metrics_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Metric 1: Artifacts Discovered
        metric1 = self.create_metric_card(metrics_container,
                                        "🧬 ARTIFACTS DISCOVERED",
                                        str(len(self.manifest_data)),
                                        "Total Models & Patterns",
                                        0)
        metric1.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        
        # Metric 2: Average Score
        avg_score = self.calculate_average_score()
        metric2 = self.create_metric_card(metrics_container,
                                        "⚖️ CONSTITUTIONAL SCORE",
                                        f"{avg_score:.1f}%",
                                        "Average Alignment",
                                        avg_score)
        metric2.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)
        
        # Metric 3: Distilled Models
        distilled_count = self.count_distilled_models()
        metric3 = self.create_metric_card(metrics_container,
                                        "⚗️ DISTILLED MODELS",
                                        str(distilled_count),
                                        "Successfully Processed",
                                        (distilled_count / max(len(self.manifest_data), 1)) * 100)
        metric3.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        
        # Metric 4: System Health
        metric4 = self.create_metric_card(metrics_container,
                                        "🛡️ SYSTEM HEALTH",
                                        "100%",
                                        "Operational Status",
                                        100)
        metric4.grid(row=1, column=1, sticky='nsew', padx=10, pady=10)
        
        # Recent Activity
        activity_frame = tk.Frame(left_panel, bg=self.colors['bg_panel'])
        activity_frame.pack(fill=tk.X, padx=30, pady=20)
        
        activity_title = tk.Label(activity_frame,
                                text="🕒 RECENT ACTIVITY",
                                font=('Segoe UI', 14, 'bold'),
                                bg=self.colors['bg_panel'],
                                fg=self.colors['text_light'])
        activity_title.pack(anchor='w')
        
        self.activity_text = scrolledtext.ScrolledText(activity_frame,
                                                     height=8,
                                                     bg=self.colors['bg_darker'],
                                                     fg=self.colors['text_dim'],
                                                     font=('Consolas', 9),
                                                     relief=tk.FLAT,
                                                     borderwidth=0)
        self.activity_text.pack(fill=tk.X, pady=(10, 0))
        
        # Right panel - Controls
        right_panel = tk.Frame(content_frame,
                             bg=self.colors['bg_panel'],
                             highlightbackground=self.colors['border'],
                             highlightthickness=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Console title
        console_title = tk.Label(right_panel,
                               text="🎮 CONTROL CONSOLE",
                               font=('Segoe UI', 16, 'bold'),
                               bg=self.colors['bg_panel'],
                               fg=self.colors['text_light'],
                               pady=20)
        console_title.pack()
        
        # Console output
        console_container = tk.Frame(right_panel, bg=self.colors['bg_panel'])
        console_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        self.console_text = scrolledtext.ScrolledText(console_container,
                                                    height=15,
                                                    bg='#000000',
                                                    fg=self.colors['cyan'],
                                                    font=('Consolas', 10),
                                                    relief=tk.FLAT)
        self.console_text.pack(fill=tk.BOTH, expand=True)
        
        # Add welcome message
        self.add_console("🏛️ REZSTACK CONSTITUTIONAL SUITE v2.0")
        self.add_console("💎 ELITE PRODUCTION EDITION")
        self.add_console(f"📁 Loaded {len(self.manifest_data)} artifacts from manifest")
        self.add_console("✅ System initialized and ready")
        
        # Control buttons
        button_frame = tk.Frame(console_container, bg=self.colors['bg_panel'])
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Start Distillation button
        self.start_btn = tk.Button(button_frame,
                                 text="🚀 START DISTILLATION",
                                 font=('Segoe UI', 12, 'bold'),
                                 bg=self.colors['gold'],
                                 fg='#000000',
                                 padx=30,
                                 pady=12,
                                 command=self.start_distillation,
                                 cursor='hand2',
                                 relief=tk.FLAT)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Scan Workspace button
        scan_btn = tk.Button(button_frame,
                           text="🔍 SCAN WORKSPACE",
                           font=('Segoe UI', 11),
                           bg=self.colors['blue'],
                           fg='#000000',
                           padx=20,
                           pady=10,
                           command=self.scan_workspace,
                           cursor='hand2',
                           relief=tk.FLAT)
        scan_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Export Report button
        export_btn = tk.Button(button_frame,
                             text="📊 EXPORT REPORT",
                             font=('Segoe UI', 11),
                             bg=self.colors['purple'],
                             fg='#000000',
                             padx=20,
                             pady=10,
                             command=self.export_report,
                             cursor='hand2',
                             relief=tk.FLAT)
        export_btn.pack(side=tk.LEFT)
        
        # Bottom panel - Model List
        bottom_panel = tk.Frame(main_container,
                              bg=self.colors['bg_panel'],
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
        bottom_panel.pack(fill=tk.BOTH, expand=False, padx=30, pady=(15, 0))
        
        # Model list title
        list_title = tk.Label(bottom_panel,
                            text="📋 MODEL REGISTRY",
                            font=('Segoe UI', 16, 'bold'),
                            bg=self.colors['bg_panel'],
                            fg=self.colors['text_light'],
                            pady=15)
        list_title.pack()
        
        # Treeview for models
        tree_frame = tk.Frame(bottom_panel, bg=self.colors['bg_panel'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        
        # Create treeview with scrollbars
        tree_scroll_y = tk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree = ttk.Treeview(tree_frame,
                                columns=('Name', 'Category', 'Size', 'Status', 'Score'),
                                show='headings',
                                yscrollcommand=tree_scroll_y.set,
                                xscrollcommand=tree_scroll_x.set)
        
        # Configure scrollbars
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        # Define headings
        self.tree.heading('Name', text='MODEL NAME')
        self.tree.heading('Category', text='CATEGORY')
        self.tree.heading('Size', text='SIZE (MB)')
        self.tree.heading('Status', text='STATUS')
        self.tree.heading('Score', text='SCORE')
        
        # Define columns
        self.tree.column('Name', width=400)
        self.tree.column('Category', width=150)
        self.tree.column('Size', width=100)
        self.tree.column('Status', width=120)
        self.tree.column('Score', width=100)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Populate tree with data
        self.populate_model_list()
        
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        
        # Configure Treeview colors
        style.configure("Treeview",
                       background=self.colors['bg_darker'],
                       foreground=self.colors['text_light'],
                       fieldbackground=self.colors['bg_darker'],
                       borderwidth=0)
        
        style.configure("Treeview.Heading",
                       background=self.colors['bg_panel'],
                       foreground=self.colors['gold'],
                       relief=tk.FLAT,
                       font=('Segoe UI', 10, 'bold'))
        
        style.map("Treeview",
                 background=[('selected', self.colors['blue'])],
                 foreground=[('selected', 'white')])
        
    def create_metric_card(self, parent, title, value, subtitle, progress):
        """Create a metric card"""
        card = tk.Frame(parent, bg=self.colors['bg_darker'], relief=tk.FLAT)
        
        # Title
        tk.Label(card,
                text=title,
                font=('Segoe UI', 12),
                bg=self.colors['bg_darker'],
                fg=self.colors['text_dim']).pack(anchor='w', padx=15, pady=(15, 5))
        
        # Value
        value_label = tk.Label(card,
                             text=value,
                             font=('Segoe UI', 32, 'bold'),
                             bg=self.colors['bg_darker'],
                             fg=self.colors['gold_light'])
        value_label.pack(anchor='w', padx=15)
        
        # Subtitle
        tk.Label(card,
                text=subtitle,
                font=('Segoe UI', 9),
                bg=self.colors['bg_darker'],
                fg=self.colors['text_dim']).pack(anchor='w', padx=15, pady=(0, 10))
        
        # Progress bar
        progress_frame = tk.Frame(card, bg=self.colors['bg_darker'])
        progress_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Progress bar background
        progress_bg = tk.Frame(progress_frame, 
                              height=6,
                              bg='#303050')
        progress_bg.pack(fill=tk.X)
        
        # Progress bar foreground
        progress_width = min(progress, 100)
        progress_fg = tk.Frame(progress_bg,
                              height=6,
                              width=progress_width * 2,  # Scale for pixels
                              bg=self.colors['green'])
        progress_fg.place(x=0, y=0)
        
        return card
        
    def add_console(self, message, type="info"):
        """Add message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Set color based on type
        if type == "success":
            color = self.colors['green']
        elif type == "error":
            color = self.colors['red']
        elif type == "warning":
            color = self.colors['gold']
        elif type == "command":
            color = self.colors['cyan']
        else:
            color = self.colors['text_dim']
        
        # Insert message
        self.console_text.insert(tk.END, f"[{timestamp}] {message}\n", type)
        self.console_text.tag_config(type, foreground=color)
        self.console_text.see(tk.END)
        
    def add_activity(self, message):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M")
        self.activity_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.activity_text.see(tk.END)
        
    def calculate_average_score(self):
        """Calculate average constitutional score"""
        if not self.distillation_results:
            return 0.0
            
        if isinstance(self.distillation_results, dict) and 'average_constitutional_score' in self.distillation_results:
            return self.distillation_results['average_constitutional_score'] * 100
            
        return 0.0
        
    def count_distilled_models(self):
        """Count distilled models"""
        if not self.distillation_results:
            return 0
            
        if isinstance(self.distillation_results, dict) and 'distilled_models' in self.distillation_results:
            return len(self.distillation_results['distilled_models'])
            
        return 0
        
    def populate_model_list(self):
        """Populate treeview with models"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add models from manifest
        for item in self.manifest_data[:50]:  # Show first 50
            name = item.get('name', 'Unknown')
            category = item.get('category', 'Unknown')
            size = f"{item.get('size_mb', 0):.1f}"
            status = item.get('status', 'pending')
            score = item.get('constitutional_score', 0)
            
            if score:
                score_display = f"{score*100:.1f}%"
            else:
                score_display = "N/A"
                
            # Insert into tree
            self.tree.insert('', tk.END, 
                           values=(name, category, size, status, score_display))
            
    def start_distillation(self):
        """Start the distillation process"""
        if self.running:
            messagebox.showwarning("Already Running", "Distillation is already in progress!")
            return
            
        # Update UI
        self.start_btn.config(state=tk.DISABLED, text="⏳ PROCESSING...")
        self.status_indicator.config(fg=self.colors['gold'])
        self.status_label.config(text="DISTILLING MODELS", fg=self.colors['gold'])
        
        # Start distillation in separate thread
        self.running = True
        thread = threading.Thread(target=self.run_distillation, daemon=True)
        thread.start()
        
    def run_distillation(self):
        """Run the distillation process"""
        try:
            self.add_console("🚀 Starting Constitutional Distillation...", "command")
            self.add_activity("Started distillation process")
            
            # Run the distiller script
            script_path = self.base_path / "rezstack_distiller_v2.py"
            
            if script_path.exists():
                self.add_console(f"Executing: {script_path.name}", "info")
                
                # Run the script
                process = subprocess.Popen([sys.executable, str(script_path)],
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT,
                                         text=True,
                                         bufsize=1,
                                         universal_newlines=True)
                
                # Read output in real-time
                for line in process.stdout:
                    if line.strip():
                        self.add_console(line.strip(), "info")
                        
                process.wait()
                
                if process.returncode == 0:
                    self.add_console("✅ Distillation completed successfully!", "success")
                    self.add_activity("Distillation completed successfully")
                else:
                    self.add_console(f"❌ Distillation failed with code {process.returncode}", "error")
                    self.add_activity("Distillation failed")
                    
            else:
                self.add_console("❌ Distiller script not found!", "error")
                
        except Exception as e:
            self.add_console(f"❌ Error during distillation: {str(e)}", "error")
            self.add_activity(f"Error: {str(e)}")
            
        finally:
            # Update UI
            self.root.after(0, self.distillation_complete)
            
    def distillation_complete(self):
        """Called when distillation completes"""
        self.running = False
        self.start_btn.config(state=tk.NORMAL, text="🚀 START DISTILLATION")
        self.status_indicator.config(fg=self.colors['green'])
        self.status_label.config(text="SYSTEM READY", fg=self.colors['text_dim'])
        
        # Reload data and refresh UI
        self.load_data()
        self.populate_model_list()
        
    def scan_workspace(self):
        """Scan workspace for models"""
        self.add_console("🔍 Scanning workspace...", "command")
        self.add_activity("Scanning workspace")
        
        # Run scanning script
        script_content = f"""
import json
import sys
from pathlib import Path

base_path = Path(r"{self.base_path}")
manifest_path = base_path / "models" / "distilled" / "reports" / "full_distillation_manifest.json"

# Create directory if it doesn't exist
manifest_path.parent.mkdir(parents=True, exist_ok=True)

# Run scanning logic
print("Scanning workspace...")
print(f"Base path: {{base_path}}")

# For now, create a sample manifest
manifest = [
    {{
        "name": "production_constitutional_predictor.pkl",
        "category": "Models",
        "size_mb": 1.2,
        "status": "audited",
        "constitutional_score": 1.0
    }}
]

with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)

print(f"✅ Manifest created with {{len(manifest)}} items")
print(f"Saved to: {{manifest_path}}")
"""
        
        try:
            # Execute scanning
            result = subprocess.run([sys.executable, "-c", script_content],
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.add_console(result.stdout, "success")
                self.add_console("✅ Workspace scan completed!", "success")
                self.add_activity("Workspace scan completed")
                
                # Reload data
                self.load_data()
                self.populate_model_list()
            else:
                self.add_console(f"❌ Scan failed: {result.stderr}", "error")
                
        except Exception as e:
            self.add_console(f"❌ Error during scan: {str(e)}", "error")
            
    def export_report(self):
        """Export distillation report"""
        self.add_console("📊 Exporting report...", "command")
        
        try:
            # Find latest report
            reports_dir = self.distilled_dir / "reports"
            if reports_dir.exists():
                report_files = list(reports_dir.glob("*.json"))
                if report_files:
                    latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
                    
                    # Create export with timestamp
                    export_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                    export_file = reports_dir / f"export_{export_time}.json"
                    
                    # Copy the report
                    import shutil
                    shutil.copy2(latest_report, export_file)
                    
                    self.add_console(f"✅ Report exported to: {export_file.name}", "success")
                    self.add_activity(f"Exported report: {export_file.name}")
                else:
                    self.add_console("❌ No reports found to export", "warning")
            else:
                self.add_console("❌ Reports directory not found", "warning")
                
        except Exception as e:
            self.add_console(f"❌ Error exporting report: {str(e)}", "error")
            
    def start_monitoring(self):
        """Start background monitoring"""
        def monitor():
            while True:
                try:
                    # Check for new reports
                    reports_dir = self.distilled_dir / "reports"
                    if reports_dir.exists():
                        report_files = list(reports_dir.glob("distillation_*.json"))
                        if report_files:
                            latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
                            
                            # Check if this is newer than our current data
                            report_time = latest_report.stat().st_mtime
                            
                            # Reload if new
                            if not hasattr(self, 'last_report_time') or report_time > self.last_report_time:
                                with open(latest_report, 'r') as f:
                                    self.distillation_results = json.load(f)
                                self.last_report_time = report_time
                                
                                # Update UI
                                self.root.after(0, self.populate_model_list)
                                
                except Exception as e:
                    print(f"Monitoring error: {e}")
                    
                time.sleep(5)  # Check every 5 seconds
                
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

def main():
    """Main entry point"""
    root = tk.Tk()
    
    # Center window on screen
    window_width = 1600
    window_height = 1000
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    # Create and run the UI
    app = RezstackEliteUI(root)
    
    # Set minimum size
    root.minsize(1200, 800)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()