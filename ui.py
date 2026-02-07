import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import sys
from pathlib import Path

# Try to import pipeline components
try:
    from pipeline import PrivacyScanner
    from llm import LlamaCppClient
    from encode_documents import DocumentEncoder
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all required files are present: pipeline.py, llm.py, glm_ocr.py, get_files.py, encode_documents.py")
    sys.exit(1)

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PrivacyScannerApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.geometry("2560x1440")
        self.app.title("TRACE: Privacy Scanner - Local Intelligence")
        
        # Scanner instance
        self.scanner = PrivacyScanner()
        self.document_encoder = None
        self.selected_folder = None
        self.is_scanning = False
        self.is_encoding = False
        self.scan_thread = None
        self.encode_thread = None
        self.stop_requested = False
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ctk.CTkFrame(self.app)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkLabel(
            main_frame,
            text="🔍 Privacy Scanner - Digital Footprint Discovery",
            font=("Arial", 28, "bold")
        )
        header.pack(pady=(10, 20))
        
        # Folder Selection Section
        folder_frame = ctk.CTkFrame(main_frame)
        folder_frame.pack(fill="x", padx=10, pady=10)
        
        folder_label = ctk.CTkLabel(
            folder_frame,
            text="Select Folder to Scan:",
            font=("Arial", 14, "bold")
        )
        folder_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Folder path display and button
        folder_input_frame = ctk.CTkFrame(folder_frame)
        folder_input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.folder_entry = ctk.CTkEntry(
            folder_input_frame,
            placeholder_text="No folder selected",
            font=("Arial", 12),
            state="readonly"
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            folder_input_frame,
            text="Browse",
            command=self.select_folder,
            width=100,
            font=("Arial", 12)
        )
        browse_btn.pack(side="right")
        
        # Options Section
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", padx=10, pady=10)
        
        options_label = ctk.CTkLabel(
            options_frame,
            text="Scan Options:",
            font=("Arial", 14, "bold")
        )
        options_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Recursive checkbox
        self.recursive_var = ctk.BooleanVar(value=False)
        recursive_check = ctk.CTkCheckBox(
            options_frame,
            text="Scan subdirectories recursively",
            variable=self.recursive_var,
            font=("Arial", 12)
        )
        recursive_check.pack(anchor="w", padx=20, pady=(0, 5))
        
        # Enable OCR checkbox
        self.enable_ocr_var = ctk.BooleanVar(value=True)
        ocr_check = ctk.CTkCheckBox(
            options_frame,
            text="Enable OCR on images (extract text from images)",
            variable=self.enable_ocr_var,
            font=("Arial", 12)
        )
        ocr_check.pack(anchor="w", padx=20, pady=(0, 5))
        
        # Enable encoding checkbox
        self.enable_encoding_var = ctk.BooleanVar(value=True)
        encoding_check = ctk.CTkCheckBox(
            options_frame,
            text="Encode documents to vector database (enables semantic search)",
            variable=self.enable_encoding_var,
            font=("Arial", 12)
        )
        encoding_check.pack(anchor="w", padx=20, pady=(0, 5))
        
        # Auto-detect sensitive files checkbox
        self.auto_detect_sensitive_var = ctk.BooleanVar(value=True)
        auto_detect_check = ctk.CTkCheckBox(
            options_frame,
            text="Auto-detect and show sensitive files after encoding",
            variable=self.auto_detect_sensitive_var,
            font=("Arial", 12)
        )
        auto_detect_check.pack(anchor="w", padx=20, pady=(0, 10))
        
        # LLM Server URL
        llm_url_frame = ctk.CTkFrame(options_frame)
        llm_url_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        llm_label = ctk.CTkLabel(
            llm_url_frame,
            text="LLM Server URL:",
            font=("Arial", 12)
        )
        llm_label.pack(side="left", padx=(10, 10))
        
        self.llm_url_entry = ctk.CTkEntry(
            llm_url_frame,
            placeholder_text="http://localhost:8080",
            font=("Arial", 12),
            width=300
        )
        self.llm_url_entry.insert(0, "http://localhost:8080")
        self.llm_url_entry.pack(side="left", padx=(0, 10))
        
        # Test Connection Button
        test_btn = ctk.CTkButton(
            llm_url_frame,
            text="Test Connection",
            command=self.test_llm_connection,
            width=130,
            font=("Arial", 11)
        )
        test_btn.pack(side="left", padx=(0, 10))
        
        # Output folder option
        output_folder_frame = ctk.CTkFrame(options_frame)
        output_folder_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        output_label = ctk.CTkLabel(
            output_folder_frame,
            text="Output Folder:",
            font=("Arial", 12)
        )
        output_label.pack(side="left", padx=(10, 10))
        
        self.output_folder_entry = ctk.CTkEntry(
            output_folder_frame,
            placeholder_text="ocr_result",
            font=("Arial", 12),
            width=300
        )
        self.output_folder_entry.insert(0, "ocr_result")
        self.output_folder_entry.pack(side="left", padx=(0, 10))
        
        # View Results Folder Button
        view_folder_btn = ctk.CTkButton(
            output_folder_frame,
            text="Open Folder",
            command=self.open_output_folder,
            width=100,
            font=("Arial", 11)
        )
        view_folder_btn.pack(side="left", padx=(0, 10))
        
        # Database path option
        db_path_frame = ctk.CTkFrame(options_frame)
        db_path_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        db_label = ctk.CTkLabel(
            db_path_frame,
            text="Vector DB Path:",
            font=("Arial", 12)
        )
        db_label.pack(side="left", padx=(10, 10))
        
        self.db_path_entry = ctk.CTkEntry(
            db_path_frame,
            placeholder_text="./chroma_db",
            font=("Arial", 12),
            width=300
        )
        self.db_path_entry.insert(0, "./chroma_db")
        self.db_path_entry.pack(side="left", padx=(0, 10))
        
        # Scan Buttons Frame
        scan_buttons_frame = ctk.CTkFrame(main_frame)
        scan_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        self.scan_btn = ctk.CTkButton(
            scan_buttons_frame,
            text="🚀 Start Privacy Scan",
            command=self.start_scan,
            font=("Arial", 16, "bold"),
            height=50,
            fg_color="#2B7A0B",
            hover_color="#1F5A08"
        )
        self.scan_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.stop_btn = ctk.CTkButton(
            scan_buttons_frame,
            text="⏹ Stop Scan",
            command=self.stop_scan,
            font=("Arial", 16, "bold"),
            height=50,
            width=150,
            fg_color="#8B0000",
            hover_color="#660000",
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=(5, 0))
        
        # Progress Section
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="x", padx=10, pady=10)
        
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to scan",
            font=("Arial", 12)
        )
        self.progress_label.pack(pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.progress_bar.set(0)
        
        # Quick Query Section
        query_frame = ctk.CTkFrame(main_frame)
        query_frame.pack(fill="x", padx=10, pady=10)
        
        query_label = ctk.CTkLabel(
            query_frame,
            text="Quick Query Database:",
            font=("Arial", 14, "bold")
        )
        query_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Query input row
        query_input_frame = ctk.CTkFrame(query_frame)
        query_input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.query_entry = ctk.CTkEntry(
            query_input_frame,
            placeholder_text="Enter search query (e.g., personal information, passwords, financial data...)",
            font=("Arial", 12),
            height=35
        )
        self.query_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Bind Enter key to search
        self.query_entry.bind("<Return>", lambda e: self.quick_query_database())
        
        # Number of results
        results_label = ctk.CTkLabel(
            query_input_frame,
            text="Results:",
            font=("Arial", 11)
        )
        results_label.pack(side="left", padx=(0, 5))
        
        self.n_results_var = ctk.StringVar(value="5")
        n_results_entry = ctk.CTkEntry(
            query_input_frame,
            textvariable=self.n_results_var,
            width=50,
            font=("Arial", 11)
        )
        n_results_entry.pack(side="left", padx=(0, 10))
        
        self.quick_search_btn = ctk.CTkButton(
            query_input_frame,
            text="🔍 Search",
            command=self.quick_query_database,
            width=120,
            font=("Arial", 12, "bold"),
            fg_color="#1a5490",
            hover_color="#0f3b6b"
        )
        self.quick_search_btn.pack(side="left")
        
        # Results Section
        results_label = ctk.CTkLabel(
            main_frame,
            text="Scan Results:",
            font=("Arial", 14, "bold")
        )
        results_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Results text box
        self.results_text = ctk.CTkTextbox(
            main_frame,
            font=("Consolas", 11),
            wrap="word"
        )
        self.results_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Action Buttons Row
        action_frame = ctk.CTkFrame(main_frame)
        action_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        clear_btn = ctk.CTkButton(
            action_frame,
            text="Clear Results",
            command=self.clear_results,
            width=150,
            font=("Arial", 12)
        )
        clear_btn.pack(side="left", padx=5)
        
        export_btn = ctk.CTkButton(
            action_frame,
            text="Export Results",
            command=self.export_results,
            width=150,
            font=("Arial", 12)
        )
        export_btn.pack(side="left", padx=5)
        
        view_ocr_btn = ctk.CTkButton(
            action_frame,
            text="View OCR Files",
            command=self.open_output_folder,
            width=150,
            font=("Arial", 12)
        )
        view_ocr_btn.pack(side="left", padx=5)
        
        # Encoding buttons (right side)
        encoding_action_frame = ctk.CTkFrame(main_frame)
        encoding_action_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        encoding_label = ctk.CTkLabel(
            encoding_action_frame,
            text="Vector Database Actions:",
            font=("Arial", 12, "bold")
        )
        encoding_label.pack(side="left", padx=5)
        
        self.encode_btn = ctk.CTkButton(
            encoding_action_frame,
            text="📚 Encode Documents",
            command=self.encode_documents,
            width=180,
            font=("Arial", 12),
            fg_color="#1a5490",
            hover_color="#0f3b6b"
        )
        self.encode_btn.pack(side="left", padx=5)
        
        search_btn = ctk.CTkButton(
            encoding_action_frame,
            text="🔍 Search Database",
            command=self.search_database,
            width=180,
            font=("Arial", 12)
        )
        search_btn.pack(side="left", padx=5)
        
        stats_btn = ctk.CTkButton(
            encoding_action_frame,
            text="📊 Database Stats",
            command=self.show_db_stats,
            width=150,
            font=("Arial", 12)
        )
        stats_btn.pack(side="left", padx=5)
        
        find_sensitive_btn = ctk.CTkButton(
            encoding_action_frame,
            text="🚨 Find Sensitive Docs",
            command=self.find_sensitive_documents,
            width=180,
            font=("Arial", 12),
            fg_color="#8B0000",
            hover_color="#660000"
        )
        find_sensitive_btn.pack(side="left", padx=5)
        
        # Status bar
        self.status_label = ctk.CTkLabel(
            self.app,
            text="Ready",
            font=("Arial", 10),
            anchor="w"
        )
        self.status_label.pack(side="bottom", fill="x", padx=20, pady=(0, 5))
    
    def test_llm_connection(self):
        """Test connection to LLM server"""
        llm_url = self.llm_url_entry.get().strip()
        if not llm_url:
            llm_url = "http://localhost:8080"
        
        self.status_label.configure(text="Testing LLM connection...")
        
        def test_connection():
            try:
                test_client = LlamaCppClient(base_url=llm_url)
                if test_client.check_server_status():
                    self.app.after(0, lambda: messagebox.showinfo(
                        "Connection Successful",
                        f"✅ LLM server is running at {llm_url}\n\nYou're ready to scan!"
                    ))
                    self.app.after(0, lambda: self.status_label.configure(text="LLM server connected ✓"))
                else:
                    self.app.after(0, lambda: messagebox.showerror(
                        "Connection Failed",
                        f"❌ Cannot connect to LLM server at {llm_url}\n\nPlease ensure llama.cpp server is running:\nllama-server -m models/your-model.gguf --port 8080"
                    ))
                    self.app.after(0, lambda: self.status_label.configure(text="LLM server not responding ✗"))
            except Exception as e:
                self.app.after(0, lambda: messagebox.showerror(
                    "Connection Error",
                    f"Error testing connection:\n{str(e)}"
                ))
                self.app.after(0, lambda: self.status_label.configure(text="Connection test failed"))
        
        threading.Thread(target=test_connection, daemon=True).start()
    
    def open_output_folder(self):
        """Open the output folder in file explorer"""
        output_folder = self.output_folder_entry.get().strip()
        if not output_folder:
            output_folder = "ocr_result"
        
        # Create folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Open in file explorer
        abs_path = os.path.abspath(output_folder)
        if os.name == 'nt':  # Windows
            os.startfile(abs_path)
        elif os.name == 'posix':  # macOS/Linux
            import subprocess
            subprocess.Popen(['xdg-open', abs_path])
        
        self.status_label.configure(text=f"Opened folder: {abs_path}")
    
    def select_folder(self):
        """Open folder selection dialog"""
        folder = filedialog.askdirectory(title="Select Folder to Scan")
        if folder:
            self.selected_folder = folder
            self.folder_entry.configure(state="normal")
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.folder_entry.configure(state="readonly")
            self.status_label.configure(text=f"Selected: {folder}")
    
    def start_scan(self):
        """Start the privacy scan in a separate thread"""
        if self.is_scanning:
            messagebox.showwarning("Scan in Progress", "A scan is already running!")
            return
        
        if not self.selected_folder:
            messagebox.showerror("No Folder Selected", "Please select a folder to scan first!")
            return
        
        if not os.path.exists(self.selected_folder):
            messagebox.showerror("Invalid Folder", "The selected folder does not exist!")
            return
        
        # Disable scan button, enable stop button
        self.is_scanning = True
        self.stop_requested = False
        self.scan_btn.configure(state="disabled", text="⏳ Scanning...")
        self.stop_btn.configure(state="normal")
        self.clear_results()
        
        # Update scanner with LLM URL and output folder
        llm_url = self.llm_url_entry.get().strip()
        if not llm_url:
            llm_url = "http://localhost:8080"
        
        output_folder = self.output_folder_entry.get().strip()
        if not output_folder:
            output_folder = "ocr_result"
        
        db_path = self.db_path_entry.get().strip()
        if not db_path:
            db_path = "./chroma_db"
        
        enable_encoding = self.enable_encoding_var.get()
        enable_ocr = self.enable_ocr_var.get()
        
        self.scanner = PrivacyScanner(
            llm_base_url=llm_url,
            output_folder=output_folder,
            enable_encoding=enable_encoding,
            enable_ocr=enable_ocr,
            db_path=db_path
        )
        
        # Start scan in separate thread
        self.scan_thread = threading.Thread(target=self.run_scan, daemon=True)
        self.scan_thread.start()
    
    def stop_scan(self):
        """Request to stop the current scan"""
        if self.is_scanning:
            self.stop_requested = True
            self.stop_btn.configure(state="disabled")
            self.status_label.configure(text="Stopping scan... (processing current image)")
            messagebox.showinfo("Stopping Scan", "Scan will stop after completing the current image.")
    
    def run_scan(self):
        """Execute the scan (runs in separate thread)"""
        try:
            recursive = self.recursive_var.get()
            
            # Create a wrapper progress callback that checks for stop request
            def progress_wrapper(current, total, message):
                if self.stop_requested:
                    raise InterruptedError("Scan stopped by user")
                self.update_progress(current, total, message)
            
            results = self.scanner.scan_folder(
                self.selected_folder,
                recursive=recursive,
                progress_callback=progress_wrapper
            )
            
            # Display results
            if not self.stop_requested:
                self.app.after(0, lambda: self.display_results(results))
                # Show popup for sensitive files
                sensitive_files = [r for r in results if r.get('risk_level') in ['critical', 'high', 'medium']]
                if sensitive_files:
                    self.app.after(0, lambda: self.show_results_popup(sensitive_files))

            else:
                self.app.after(0, lambda: self.display_partial_results(results))
            
        except InterruptedError:
            self.app.after(0, lambda: messagebox.showinfo("Scan Stopped", "Scan was stopped by user."))
            self.app.after(0, lambda: self.progress_label.configure(text="Scan stopped by user"))
        except Exception as e:
            self.app.after(0, lambda: messagebox.showerror("Scan Error", f"An error occurred:\n{str(e)}"))
            self.app.after(0, lambda: self.progress_label.configure(text=f"Error: {str(e)}"))
        finally:
            self.app.after(0, self.scan_complete)
    
    def update_progress(self, current, total, message):
        """Update progress bar and label"""
        progress = current / total if total > 0 else 0
        self.app.after(0, lambda: self.progress_bar.set(progress))
        self.app.after(0, lambda: self.progress_label.configure(text=message))
        self.app.after(0, lambda: self.status_label.configure(text=message))
    
    def display_results(self, results):
        """Display scan results in the text widget"""
        self.results_text.delete("1.0", "end")
        
        if not results:
            self.results_text.insert("1.0", "No files found or scan failed.\n")
            return
        
        # Summary
        total = len(results)
        images = sum(1 for r in results if r.get('file_type') != 'text/markdown')
        text_files = sum(1 for r in results if r.get('file_type') == 'text/markdown')
        critical = sum(1 for r in results if r.get('risk_level') == 'critical')
        high = sum(1 for r in results if r.get('risk_level') == 'high')
        medium = sum(1 for r in results if r.get('risk_level') == 'medium')
        low = sum(1 for r in results if r.get('risk_level') == 'low')
        none_found = sum(1 for r in results if r.get('risk_level') == 'none')
        
        summary = f"""
{'='*80}
PRIVACY SCAN SUMMARY
{'='*80}
Total Files Scanned: {total}
  Images: {images}
  Text/MD Files: {text_files}

Risk Distribution:
  Critical Risk: {critical}
  High Risk: {high}
  Medium Risk: {medium}
  Low Risk: {low}
  No Risk: {none_found}
{'='*80}

"""
        self.results_text.insert("end", summary)
        
        # Detailed results
        for idx, result in enumerate(results, 1):
            risk = result.get('risk_level', 'unknown').upper()
            filename = result.get('filename', 'Unknown')
            contains_sensitive = result.get('contains_sensitive_info', False)
            file_type = result.get('file_type', 'image')
            
            # Color code based on risk
            risk_emoji = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢',
                'NONE': '✅',
                'UNKNOWN': '❓',
                'ERROR': '❌'
            }.get(risk, '❓')
            
            # File type indicator
            type_emoji = '📄' if file_type == 'text/markdown' else '🖼️'
            
            detail = f"\n{idx}. {risk_emoji} {type_emoji} {filename}\n"
            detail += f"   Risk Level: {risk}\n"
            detail += f"   Type: {file_type.title()}\n"
            detail += f"   Contains Sensitive Info: {'Yes' if contains_sensitive else 'No'}\n"
            
            if result.get('detected_categories'):
                detail += f"   Categories: {', '.join(result.get('detected_categories'))}\n"
            
            if result.get('specific_findings'):
                detail += f"   Findings:\n"
                for finding in result.get('specific_findings', [])[:5]:  # Show up to 5
                    detail += f"      - {finding}\n"
                if len(result.get('specific_findings', [])) > 5:
                    detail += f"      ... and {len(result.get('specific_findings', [])) - 5} more\n"
            
            if result.get('recommendations'):
                detail += f"   Recommendations:\n"
                for rec in result.get('recommendations', []):  # Show all recommendations
                    detail += f"      - {rec}\n"
            
            # Display file path (handle both image_path and file_path)
            file_path = result.get('file_path') or result.get('image_path', 'N/A')
            detail += f"   File: {file_path}\n"
            detail += "-" * 80 + "\n"
            
            self.results_text.insert("end", detail)
        
        # Add critical actions summary for high-risk files
        high_risk_files = [r for r in results if r.get('risk_level') in ['critical', 'high']]
        
        if high_risk_files:
            self.results_text.insert("end", f"\n{'='*80}\n")
            self.results_text.insert("end", f"⚠️  CRITICAL ACTIONS REQUIRED\n")
            self.results_text.insert("end", f"{'='*80}\n\n")
            self.results_text.insert("end", f"{len(high_risk_files)} file(s) require immediate attention:\n\n")
            
            for idx, result in enumerate(high_risk_files, 1):
                filename = result.get('filename', 'Unknown')
                file_path = result.get('file_path') or result.get('image_path', 'N/A')
                risk = result.get('risk_level', 'unknown').upper()
                categories = result.get('detected_categories', [])
                
                risk_icon = '🔴' if risk == 'CRITICAL' else '🟠'
                
                self.results_text.insert("end", f"{idx}. {risk_icon} {filename}\n")
                self.results_text.insert("end", f"   Path: {file_path}\n")
                
                if categories:
                    self.results_text.insert("end", f"   Sensitive Data Types: {', '.join(categories)}\n")
                
                if result.get('recommendations'):
                    self.results_text.insert("end", f"\n   ACTION ITEMS:\n")
                    for rec_idx, rec in enumerate(result.get('recommendations', []), 1):
                        self.results_text.insert("end", f"   {rec_idx}. {rec}\n")
                
                self.results_text.insert("end", "\n" + "-" * 80 + "\n\n")
        
        self.results_text.insert("end", f"\n{'='*80}\n")
        self.results_text.insert("end", f"Scan completed at: {Path(self.scanner.output_folder).absolute()}\n")
    
    
    def show_results_popup(self, sensitive_files):
        """Show scan results in a popup window with file actions"""
        # Create popup window
        popup = ctk.CTkToplevel(self.app)
        popup.title(f"Sensitive Files Found - {len(sensitive_files)} file(s)")
        popup.geometry("1400x800")
        
        # Make it modal
        popup.grab_set()
        popup.focus()
        
        # Header
        header_frame = ctk.CTkFrame(popup, fg_color="#8B0000")
        header_frame.pack(fill="x", padx=0, pady=0)
        
        header_label = ctk.CTkLabel(
            header_frame,
            text=f"🚨 {len(sensitive_files)} SENSITIVE FILE(S) DETECTED",
            font=("Arial", 20, "bold"),
            text_color="white"
        )
        header_label.pack(pady=15)
        
        # Main content frame with scrollbar
        main_frame = ctk.CTkScrollableFrame(popup)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Display each sensitive file
        for idx, result in enumerate(sensitive_files, 1):
            self.create_file_card(main_frame, result, idx)
        
        # Close button at bottom
        close_btn = ctk.CTkButton(
            popup,
            text="Close",
            command=popup.destroy,
            width=200,
            height=40,
            font=("Arial", 14, "bold")
        )
        close_btn.pack(pady=10)
    
    def create_file_card(self, parent, result, idx):
        """Create a card for each sensitive file with path, recommendations, and actions"""
        filename = result.get('filename', 'Unknown')
        file_path = result.get('file_path') or result.get('image_path', 'N/A')
        risk_level = result.get('risk_level', 'low').upper()
        categories = result.get('detected_categories', [])
        recommendations = result.get('recommendations', [])
        
        # Risk color
        risk_colors = {
            'CRITICAL': '#8B0000',
            'HIGH': '#FF6347',
            'MEDIUM': '#FFA500',
            'LOW': '#90EE90'
        }
        risk_color = risk_colors.get(risk_level, '#808080')
        
        # Card frame
        card_frame = ctk.CTkFrame(parent, border_width=2, border_color=risk_color)
        card_frame.pack(fill="x", padx=10, pady=10)
        
        # Top section with risk indicator
        top_frame = ctk.CTkFrame(card_frame, fg_color=risk_color)
        top_frame.pack(fill="x", padx=0, pady=0)
        
        risk_label = ctk.CTkLabel(
            top_frame,
            text=f"{idx}. {risk_level} RISK - {filename}",
            font=("Arial", 14, "bold"),
            text_color="white"
        )
        risk_label.pack(pady=10, padx=10, anchor="w")
        
        # Content frame with 3 columns
        content_frame = ctk.CTkFrame(card_frame)
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Left column - File Path
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        path_label = ctk.CTkLabel(
            left_frame,
            text="📁 File Location:",
            font=("Arial", 12, "bold")
        )
        path_label.pack(anchor="w", pady=(5, 5))
        
        path_text = ctk.CTkTextbox(
            left_frame,
            height=80,
            font=("Consolas", 10),
            wrap="word"
        )
        path_text.pack(fill="both", expand=True, pady=(0, 5))
        path_text.insert("1.0", file_path)
        path_text.configure(state="disabled")
        
        if categories:
            cat_label = ctk.CTkLabel(
                left_frame,
                text="🏷️ Detected Categories:",
                font=("Arial", 11, "bold")
            )
            cat_label.pack(anchor="w", pady=(10, 5))
            
            cat_text = ctk.CTkTextbox(
                left_frame,
                height=60,
                font=("Arial", 10)
            )
            cat_text.pack(fill="both", expand=True)
            cat_text.insert("1.0", "\n".join([f"• {cat}" for cat in categories]))
            cat_text.configure(state="disabled")
        
        # Middle column - Recommendations
        middle_frame = ctk.CTkFrame(content_frame)
        middle_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        
        rec_label = ctk.CTkLabel(
            middle_frame,
            text="⚠️ RECOMMENDED ACTIONS:",
            font=("Arial", 12, "bold"),
            text_color="#FF6347"
        )
        rec_label.pack(anchor="w", pady=(5, 10))
        
        rec_text = ctk.CTkTextbox(
            middle_frame,
            font=("Arial", 11),
            wrap="word"
        )
        rec_text.pack(fill="both", expand=True)
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                rec_text.insert("end", f"{i}. {rec}\n\n")
        else:
            rec_text.insert("1.0", "No specific recommendations available.")
        
        rec_text.configure(state="disabled")
        
        # Right column - Action Buttons
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.grid(row=0, column=2, sticky="nsew")
        
        actions_label = ctk.CTkLabel(
            right_frame,
            text="🛠️ Actions:",
            font=("Arial", 12, "bold")
        )
        actions_label.pack(pady=(5, 15))
        
        # Delete button
        delete_btn = ctk.CTkButton(
            right_frame,
            text="🗑️ Delete File",
            command=lambda: self.delete_sensitive_file(file_path, card_frame),
            width=180,
            height=50,
            font=("Arial", 13, "bold"),
            fg_color="#8B0000",
            hover_color="#660000"
        )
        delete_btn.pack(pady=10)
        
        # Vault button (dummy)
        vault_btn = ctk.CTkButton(
            right_frame,
            text="🔒 Store in Vault",
            command=lambda: self.store_in_vault(file_path, filename),
            width=180,
            height=50,
            font=("Arial", 13, "bold"),
            fg_color="#1a5490",
            hover_color="#0f3b6b"
        )
        vault_btn.pack(pady=10)
        
        # Open file location button
        open_btn = ctk.CTkButton(
            right_frame,
            text="📂 Open Location",
            command=lambda: self.open_file_location(file_path),
            width=180,
            height=40,
            font=("Arial", 11)
        )
        open_btn.pack(pady=10)
        
        # Configure grid weights
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=2)
        content_frame.grid_columnconfigure(2, weight=1)
    
    def delete_sensitive_file(self, file_path, card_frame):
        """Delete a sensitive file after confirmation"""
        response = messagebox.askyesno(
            "Delete Sensitive File",
            f"Are you sure you want to permanently delete this file?\n\n{file_path}\n\nThis action cannot be undone!",
            icon="warning"
        )
        
        if response:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    messagebox.showinfo(
                        "File Deleted",
                        f"File successfully deleted:\n{file_path}"
                    )
                    # Grey out the card
                    card_frame.configure(fg_color="#2B2B2B", border_color="#555555")
                    # Update all children to show deleted state
                    for widget in card_frame.winfo_children():
                        if isinstance(widget, ctk.CTkFrame):
                            widget.configure(fg_color="#2B2B2B")
                else:
                    messagebox.showerror(
                        "File Not Found",
                        f"File not found:\n{file_path}"
                    )
            except Exception as e:
                messagebox.showerror(
                    "Delete Error",
                    f"Failed to delete file:\n{str(e)}"
                )
    
    def store_in_vault(self, file_path, filename):
        """Store file in encrypted vault (dummy implementation)"""
        messagebox.showinfo(
            "Store in Vault",
            f"📦 Vault Feature (Coming Soon)\n\nThis will encrypt and securely store:\n{filename}\n\nFeatures:\n• AES-256 encryption\n• Password protected vault\n• Secure deletion of original\n• Easy file retrieval"
        )
    
    def open_file_location(self, file_path):
        """Open the folder containing the file"""
        try:
            folder_path = os.path.dirname(file_path)
            if os.path.exists(folder_path):
                if os.name == 'nt':  # Windows
                    os.startfile(folder_path)
                elif os.name == 'posix':  # macOS/Linux
                    import subprocess
                    subprocess.Popen(['xdg-open', folder_path])
            else:
                messagebox.showerror(
                    "Folder Not Found",
                    f"Folder not found:\n{folder_path}"
                )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to open folder:\n{str(e)}"
            )

    
    def display_partial_results(self, results):
        """Display partial results when scan is stopped"""
        self.display_results(results)
        # Add note about partial results
        self.results_text.insert("1.0", "⚠️  PARTIAL RESULTS - Scan was stopped by user\n\n")
    
    def scan_complete(self):
        """Reset UI after scan completion"""
        self.is_scanning = False
        self.stop_requested = False
        self.scan_btn.configure(state="normal", text="🚀 Start Privacy Scan")
        self.stop_btn.configure(state="disabled")
        self.progress_bar.set(1.0)
        
        if not self.stop_requested:
            self.progress_label.configure(text="Scan complete!")
            self.status_label.configure(text="Scan complete - Ready for next scan")
            
            # Auto-detect sensitive files if encoding was enabled and auto-detect is on
            if self.enable_encoding_var.get() and self.auto_detect_sensitive_var.get():
                self.app.after(500, self.find_sensitive_documents)  # Small delay for UI update
        else:
            self.progress_label.configure(text="Scan stopped")
            self.status_label.configure(text="Scan stopped - Ready for next scan")
    
    def clear_results(self):
        """Clear the results text box"""
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", "Results will appear here after scanning...\n")
    
    def export_results(self):
        """Export results to a file"""
        content = self.results_text.get("1.0", "end")
        if not content.strip() or "Results will appear here" in content:
            messagebox.showinfo("No Results", "No results to export!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Results As"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Export Successful", f"Results exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export results:\n{str(e)}")
    
    def encode_documents(self):
        """Encode all txt/md files and OCR results to vector database"""
        if self.is_encoding:
            messagebox.showwarning("Encoding in Progress", "Document encoding is already running!")
            return
        
        if self.is_scanning:
            messagebox.showwarning("Scan in Progress", "Please wait for the scan to complete first!")
            return
        
        # Get configuration
        db_path = self.db_path_entry.get().strip()
        if not db_path:
            db_path = "./chroma_db"
        
        output_folder = self.output_folder_entry.get().strip()
        if not output_folder:
            output_folder = "ocr_result"
        
        # Get folder to scan
        folder = self.folder_entry.get().strip()
        if not folder:
            folder = "."
        
        # Confirm action
        response = messagebox.askyesno(
            "Encode Documents",
            "This will encode all .txt and .md files (from file lists) and OCR results to the vector database.\n\nContinue?"
        )
        
        if not response:
            return
        
        # Disable encode button
        self.is_encoding = True
        self.encode_btn.configure(state="disabled", text="⏳ Encoding...")
        self.clear_results()
        
        # Start encoding in separate thread
        self.encode_thread = threading.Thread(
            target=self.run_encoding,
            args=(db_path, output_folder, folder),
            daemon=True
        )
        self.encode_thread.start()
    
    def run_encoding(self, db_path, output_folder, scan_directory):
        """Execute document encoding (runs in separate thread)"""
        try:
            self.app.after(0, lambda: self.progress_label.configure(text="Initializing encoder..."))
            self.app.after(0, lambda: self.progress_bar.set(0.1))
            
            # Create encoder
            encoder = DocumentEncoder(
                file_lists_folder="temp",
                ocr_result_folder=output_folder,
                db_path=db_path,
                scan_directory=scan_directory
            )
            
            self.app.after(0, lambda: self.progress_label.configure(text="Encoding documents..."))
            self.app.after(0, lambda: self.progress_bar.set(0.3))
            
            # Encode all documents
            stats = encoder.encode_all_documents(
                use_chunking=True,
                include_ocr=True
            )
            
            self.app.after(0, lambda: self.progress_bar.set(1.0))
            
            # Display results
            result_text = f"""{'='*80}
DOCUMENT ENCODING COMPLETE
{'='*80}
Total files: {stats['total_files']}
Successfully encoded: {stats['successful']}
Failed: {stats['failed']}
OCR files: {stats.get('ocr_files', 0)}
Text/MD files: {stats.get('text_files', 0)}

Database location: {db_path}
Total documents in database: {encoder.collection.count()}
{'='*80}
"""
            
            self.app.after(0, lambda: self.results_text.delete("1.0", "end"))
            self.app.after(0, lambda: self.results_text.insert("1.0", result_text))
            self.app.after(0, lambda: self.progress_label.configure(text="Encoding complete!"))
            
            self.app.after(0, lambda: messagebox.showinfo(
                "Encoding Complete",
                f"Successfully encoded {stats['successful']} out of {stats['total_files']} files to the vector database!"
            ))
            
            # Auto-detect sensitive files if enabled
            if self.auto_detect_sensitive_var.get():
                self.app.after(0, lambda: self.progress_label.configure(text="Searching for sensitive files..."))
                self.app.after(0, lambda: self.progress_bar.set(0.5))
                # Trigger sensitive document search
                self.app.after(500, self.find_sensitive_documents)  # Small delay for UI update
            
        except Exception as e:
            self.app.after(0, lambda: messagebox.showerror(
                "Encoding Error",
                f"An error occurred during encoding:\n{str(e)}"
            ))
            self.app.after(0, lambda: self.progress_label.configure(text=f"Encoding failed: {str(e)}"))
        finally:
            self.app.after(0, self.encoding_complete)
    
    def encoding_complete(self):
        """Reset UI after encoding completion"""
        self.is_encoding = False
        self.encode_btn.configure(state="normal", text="📚 Encode Documents")
    
    def search_database(self):
        """Search the vector database"""
        db_path = self.db_path_entry.get().strip()
        if not db_path:
            db_path = "./chroma_db"
        
        # Check if database exists
        if not os.path.exists(db_path):
            messagebox.showwarning(
                "Database Not Found",
                f"Vector database not found at: {db_path}\n\nPlease encode documents first."
            )
            return
        
        # Create search dialog
        search_window = ctk.CTkToplevel(self.app)
        search_window.title("Search Vector Database")
        search_window.geometry("800x600")
        
        # Search input
        input_frame = ctk.CTkFrame(search_window)
        input_frame.pack(fill="x", padx=20, pady=20)
        
        search_label = ctk.CTkLabel(
            input_frame,
            text="Enter your search query:",
            font=("Arial", 14, "bold")
        )
        search_label.pack(pady=(0, 10))
        
        search_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="E.g., personal information, contact details, sensitive data...",
            font=("Arial", 12),
            width=600
        )
        search_entry.pack(pady=(0, 10))
        
        results_label = ctk.CTkLabel(
            input_frame,
            text="Number of results:",
            font=("Arial", 12)
        )
        results_label.pack(side="left", padx=(0, 10))
        
        n_results_var = ctk.IntVar(value=5)
        n_results_entry = ctk.CTkEntry(
            input_frame,
            textvariable=n_results_var,
            width=60,
            font=("Arial", 12)
        )
        n_results_entry.pack(side="left", padx=(0, 10))
        
        def perform_search():
            query = search_entry.get().strip()
            if not query:
                messagebox.showwarning("Empty Query", "Please enter a search query!")
                return
            
            try:
                n_results = n_results_var.get()
                encoder = DocumentEncoder(db_path=db_path)
                results = encoder.search_similar(query, n_results=n_results)
                
                # Display results
                search_results.delete("1.0", "end")
                
                if results and results['documents'] and results['documents'][0]:
                    search_results.insert("end", f"Search Results for: '{query}'\n{'='*80}\n\n")
                    
                    for idx, (doc, metadata, distance) in enumerate(zip(
                        results['documents'][0],
                        results['metadatas'][0],
                        results['distances'][0]
                    ), 1):
                        search_results.insert("end", f"{idx}. {metadata.get('filename', 'Unknown')}\n")
                        search_results.insert("end", f"   Similarity: {1 - distance:.4f}\n")
                        search_results.insert("end", f"   Source: {'OCR' if metadata.get('is_ocr') else 'Text/MD'}\n")
                        search_results.insert("end", f"   Preview: {doc[:300]}...\n")
                        search_results.insert("end", "-" * 80 + "\n\n")
                else:
                    search_results.insert("end", "No results found.")
                    
            except Exception as e:
                messagebox.showerror("Search Error", f"Error searching database:\n{str(e)}")
        
        search_btn = ctk.CTkButton(
            input_frame,
            text="🔍 Search",
            command=perform_search,
            font=("Arial", 12, "bold")
        )
        search_btn.pack(side="left")
        
        # Results display
        search_results = ctk.CTkTextbox(
            search_window,
            font=("Consolas", 11),
            wrap="word"
        )
        search_results.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        search_results.insert("1.0", "Enter a query and click Search to find relevant documents...")
    
    def show_db_stats(self):
        """Show database statistics"""
        db_path = self.db_path_entry.get().strip()
        if not db_path:
            db_path = "./chroma_db"
        
        if not os.path.exists(db_path):
            messagebox.showwarning(
                "Database Not Found",
                f"Vector database not found at: {db_path}\n\nPlease encode documents first."
            )
            return
        
        try:
            encoder = DocumentEncoder(db_path=db_path)
            stats = encoder.get_collection_stats()
            
            messagebox.showinfo(
                "Database Statistics",
                f"Vector Database Stats\n\nLocation: {db_path}\nCollection: documents\nTotal documents: {stats.get('count', 0)}\n\nEmbedding Model: google/embeddinggemma-300m"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error getting database stats:\n{str(e)}")
    
    def find_sensitive_documents(self):
        """Analyze documents with LLM to find sensitive/critical information (reads directly from files)"""
        # Check LLM server
        llm_url = self.llm_url_entry.get().strip()
        if not llm_url:
            llm_url = "http://localhost:8080"
        
        output_folder = self.output_folder_entry.get().strip()
        if not output_folder:
            output_folder = "ocr_result"
        
        self.clear_results()
        self.results_text.insert("1.0", "🔍 Analyzing documents for sensitive information...\n\n")
        self.progress_bar.set(0.1)
        
        # Run analysis in background thread
        def analyze_sensitive():
            try:
                self.app.after(0, lambda: self.progress_label.configure(text="Initializing LLM..."))
                
                # Initialize LLM client
                llm_client = LlamaCppClient(base_url=llm_url)
                
                if not llm_client.check_server_status():
                    self.app.after(0, lambda: messagebox.showerror(
                        "LLM Server Not Found",
                        f"LLM server is not running at {llm_url}\n\nPlease start llama.cpp server first."
                    ))
                    self.app.after(0, lambda: self.progress_bar.set(0))
                    return
                
                self.app.after(0, lambda: self.progress_label.configure(text="Collecting files to analyze..."))
                self.app.after(0, lambda: self.progress_bar.set(0.15))
                
                # Collect all files to analyze
                all_files = []
                
                # Get OCR files
                if os.path.exists(output_folder):
                    for filename in os.listdir(output_folder):
                        if filename.endswith('.txt') and filename.startswith('ocr_'):
                            file_path = os.path.join(output_folder, filename)
                            if os.path.isfile(file_path):
                                all_files.append((file_path, True))  # (path, is_ocr)
                
                # Get files from file lists (txt and md)
                file_lists_folder = 'temp'
                if os.path.exists(file_lists_folder):
                    for list_filename in ['file_list_txt.txt', 'file_list_md.txt']:
                        list_path = os.path.join(file_lists_folder, list_filename)
                        if os.path.exists(list_path):
                            try:
                                with open(list_path, 'r', encoding='utf-8') as f:
                                    for line in f:
                                        line = line.strip()
                                        # Skip headers and empty lines
                                        if line and not line.startswith('File List') and not line.startswith('Directory') and not line.startswith('Timestamp') and not line.startswith('Total files') and not line.startswith('='):
                                            if os.path.isfile(line):
                                                all_files.append((line, False))  # (path, is_ocr)
                            except Exception as e:
                                import logging
                                logging.warning(f"Failed to read {list_filename}: {e}")
                
                if not all_files:
                    self.app.after(0, lambda: messagebox.showinfo(
                        "No Documents",
                        "No documents found to analyze.\n\nPlease scan/encode documents first."
                    ))
                    self.app.after(0, lambda: self.progress_bar.set(0))
                    return
                
                total_files = len(all_files)
                self.app.after(0, lambda: self.progress_label.configure(text=f"Analyzing {total_files} documents..."))
                
                # System prompt for LLM analysis
                system_prompt = """You are a privacy and security analyzer. Your task is to analyze document content and identify if it contains sensitive or critical information.

Sensitive information includes:
- Personal identification (SSN, passport, driver's license, ID numbers)
- Financial information (credit cards, bank accounts, financial records)
- Credentials (passwords, API keys, tokens, secrets)
- Medical/health records (diagnoses, prescriptions, medical history)
- Confidential business information (trade secrets, proprietary data)
- Personal contact information in sensitive contexts (addresses, phone, email with personal data)
- Biometric data (fingerprints, facial recognition, DNA)

Respond with a JSON object:
{
  "is_sensitive": true/false,
  "confidence": "high"/"medium"/"low",
  "categories": ["category1", "category2"],
  "risk_level": "critical"/"high"/"medium"/"low",
  "explanation": "Brief explanation"
}"""
                
                sensitive_files = {}
                
                for idx, (filepath, is_ocr) in enumerate(all_files, 1):
                    progress = 0.15 + (idx / total_files) * 0.75
                    filename = Path(filepath).name
                    self.app.after(0, lambda p=progress, f=filename: (
                        self.progress_bar.set(p),
                        self.progress_label.configure(text=f"Analyzing: {f}...")
                    ))
                    
                    # Read file content
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    except Exception as e:
                        import logging
                        logging.warning(f"Failed to read {filepath}: {e}")
                        continue
                    
                    # Skip empty files
                    if not content.strip():
                        continue
                    
                    # Truncate content if too long (max ~10000 chars)
                    content_truncated = content[:10000]
                    
                    query = f"""Analyze this document and determine if it contains sensitive information:

{content_truncated}

Respond ONLY with the JSON object, no other text."""
                    
                    try:
                        result = llm_client.query_with_json_response(
                            query=query,
                            system_prompt=system_prompt,
                            max_retries=2,
                            temperature=0.1,
                            max_tokens=300
                        )
                        
                        if result.get('is_sensitive', False):
                            sensitive_files[filepath] = {
                                'filename': filename,
                                'is_ocr': is_ocr,
                                'analysis': result,
                                'preview': content_truncated[:500]
                            }
                    
                    except Exception as e:
                        import logging
                        logging.warning(f"Failed to analyze {filename}: {e}")
                        continue
                
                self.app.after(0, lambda: self.progress_bar.set(0.95))
                self.app.after(0, lambda: self.progress_label.configure(text="Preparing results..."))
                
                # Sort by risk level
                risk_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
                sorted_results = sorted(
                    sensitive_files.items(),
                    key=lambda x: risk_order.get(x[1]['analysis'].get('risk_level', 'low'), 3)
                )
                
                # Display results
                self.app.after(0, lambda: self.progress_bar.set(1.0))
                self.app.after(0, lambda: self.progress_label.configure(text="Analysis complete!"))
                self.app.after(0, lambda: self.display_sensitive_results(sorted_results))
                
            except Exception as e:
                self.app.after(0, lambda: messagebox.showerror(
                    "Analysis Error",
                    f"Error analyzing documents:\n{str(e)}"
                ))
                self.app.after(0, lambda: self.progress_label.configure(text="Analysis failed"))
                self.app.after(0, lambda: self.progress_bar.set(0))
        
        threading.Thread(target=analyze_sensitive, daemon=True).start()
    
    def display_sensitive_results(self, results):
        """Display LLM-analyzed sensitive documents in popup"""
        self.results_text.delete("1.0", "end")
        
        if not results:
            self.results_text.insert("1.0", 
                "✅ No sensitive documents found!\n\n"
                "Your scanned documents appear to be safe.\n\n"
                "Note: The LLM analyzed all documents for sensitive information.\n"
                "Always manually review critical documents for complete security."
            )
            messagebox.showinfo(
                "Analysis Complete",
                "✅ No sensitive documents found!\n\nYour documents appear to be safe."
            )
            return
        
        # Show summary in main text area
        summary = f"""{'='*80}
🚨 SENSITIVE DOCUMENTS FOUND: {len(results)}
{'='*80}

The LLM has analyzed all documents and found {len(results)} file(s) containing
sensitive or critical information.

A detailed review window has been opened showing:
• File locations
• Recommended actions
• Quick action buttons to delete or secure files

Please review each file carefully and take appropriate action.
{'='*80}
"""
        self.results_text.insert("end", summary)
        
        # Convert results to scan format and show popup
        converted_results = []
        for filepath, data in results:
            analysis = data['analysis']
            
            # Convert to scan result format
            converted = {
                'filename': data['filename'],
                'file_path': filepath,
                'file_type': 'text/markdown',
                'risk_level': analysis.get('risk_level', 'low'),
                'contains_sensitive_info': True,
                'detected_categories': analysis.get('detected_categories', []),
                'specific_findings': analysis.get('specific_findings', []),
                'recommendations': analysis.get('recommendations', ['Review and secure this file.']),
                'confidence': analysis.get('confidence', 'unknown')
            }
            
            converted_results.append(converted)
        
        # Show popup with results
        self.show_results_popup(converted_results)
    
    def quick_query_database(self):
        """Quick search of vector database from main UI"""
        query = self.query_entry.get().strip()
        
        if not query:
            messagebox.showwarning("Empty Query", "Please enter a search query!")
            return
        
        db_path = self.db_path_entry.get().strip()
        if not db_path:
            db_path = "./chroma_db"
        
        if not os.path.exists(db_path):
            messagebox.showwarning(
                "Database Not Found",
                f"Vector database not found at: {db_path}\n\nPlease encode documents first.\n\nUse '📚 Encode Documents' button to create the database."
            )
            return
        
        # Get number of results
        try:
            n_results = int(self.n_results_var.get())
            if n_results < 1:
                n_results = 5
        except ValueError:
            n_results = 5
            self.n_results_var.set("5")
        
        # Clear results and show searching message
        self.clear_results()
        self.results_text.insert("1.0", f"🔍 Searching for: '{query}'...\n\n")
        self.progress_bar.set(0.3)
        self.progress_label.configure(text=f"Searching database...")
        
        # Disable search button
        self.quick_search_btn.configure(state="disabled", text="⏳ Searching...")
        
        # Search in background thread
        def perform_search():
            try:
                self.app.after(0, lambda: self.progress_bar.set(0.5))
                
                encoder = DocumentEncoder(db_path=db_path)
                results = encoder.search_similar(query, n_results=n_results)
                
                self.app.after(0, lambda: self.progress_bar.set(0.9))
                
                # Display results
                self.app.after(0, lambda: self.display_query_results(query, results, n_results))
                
            except Exception as e:
                self.app.after(0, lambda: messagebox.showerror(
                    "Search Error",
                    f"Error searching database:\n{str(e)}"
                ))
                self.app.after(0, lambda: self.clear_results())
            finally:
                self.app.after(0, lambda: self.quick_search_btn.configure(state="normal", text="🔍 Search"))
                self.app.after(0, lambda: self.progress_bar.set(0))
                self.app.after(0, lambda: self.progress_label.configure(text="Ready"))
        
        threading.Thread(target=perform_search, daemon=True).start()
    
    def display_query_results(self, query, results, n_results):
        """Display quick query search results"""
        self.results_text.delete("1.0", "end")
        
        if not results or not results['documents'] or not results['documents'][0]:
            self.results_text.insert("1.0",
                f"{'='*80}\n"
                f"SEARCH RESULTS\n"
                f"{'='*80}\n\n"
                f"Query: '{query}'\n\n"
                f"❌ No results found.\n\n"
                f"Try:\n"
                f"• Different keywords\n"
                f"• More general terms\n"
                f"• Check if documents are encoded (use '📚 Encode Documents')\n"
            )
            return
        
        # Header
        header = f"""{'='*80}
SEARCH RESULTS
{'='*80}

Query: '{query}'
Found: {len(results['documents'][0])} result(s)

"""
        self.results_text.insert("end", header)
        
        # Display each result
        for idx, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            filename = metadata.get('filename', 'Unknown')
            filepath = metadata.get('filepath', 'N/A')
            is_ocr = metadata.get('is_ocr', False)
            file_ext = metadata.get('extension', '')
            similarity = 1 - distance
            
            # Similarity indicator
            if similarity > 0.85:
                sim_icon = "🟢 Excellent"
            elif similarity > 0.7:
                sim_icon = "🟡 Good"
            elif similarity > 0.5:
                sim_icon = "🟠 Fair"
            else:
                sim_icon = "🔴 Weak"
            
            result = f"""
{idx}. {filename}
   Similarity: {sim_icon} ({similarity:.2%})
   Source: {'OCR Result' if is_ocr else f'Document ({file_ext})'}
   Path: {filepath}
   
   Preview:
   {doc[:400]}{'...' if len(doc) > 400 else ''}

{'-'*80}
"""
            self.results_text.insert("end", result)
        
        # Footer
        footer = f"\n{'='*80}\n"
        if len(results['documents'][0]) >= n_results:
            footer += f"Showing top {n_results} results. Increase 'Results' number for more.\n"
        footer += f"{'='*80}\n"
        
        self.results_text.insert("end", footer)
        
        # Update status
        self.status_label.configure(text=f"Found {len(results['documents'][0])} result(s) for: {query}")
    
    def run(self):
        """Start the application"""
        self.app.mainloop()


# Run the application
if __name__ == "__main__":
    app = PrivacyScannerApp()
    app.run()