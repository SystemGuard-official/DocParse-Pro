import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import csv
import json
from datetime import datetime
from collections import defaultdict

class TrOCRAnnotationTool:
    def __init__(self):
        # Configuration
        self.image_dir = r"images\set1"
        self.data_file = r"images\annotations_data.json"
        self.current_index = 0
        self.current_user = ""
        self.current_filter = "all"  # all, annotated, unannotated, flagged, bookmarked
        
        # Data structure: {filename: {users: {user: {text, timestamp, confidence}}, flags: [], bookmarks: [], consensus: text}}
        self.data = {}
        self.filtered_files = []
        
        # Load image files
        self.image_files = sorted([f for f in os.listdir(self.image_dir) 
                                 if f.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp', '.tiff'))])
        
        if not self.image_files:
            messagebox.showerror("Error", f"No images found in {self.image_dir}")
            return
        
        # Initialize data structure
        self.initialize_data()
        
        # Get current user
        self.get_current_user()
        
        # Load existing data
        self.load_data()
        
        # Setup GUI
        self.setup_gui()
        
        # Apply initial filter
        self.apply_filter()
        
        # Show first image
        if self.filtered_files:
            self.show_image(0)
        
        # Focus on entry for immediate typing
        self.entry.focus_set()

    def initialize_data(self):
        """Initialize data structure for all image files"""
        for filename in self.image_files:
            if filename not in self.data:
                self.data[filename] = {
                    'users': {},
                    'flags': [],
                    'bookmarks': [],
                    'consensus': '',
                    'created': datetime.now().isoformat(),
                    'modified': datetime.now().isoformat()
                }

    def get_current_user(self):
        """Get current user name"""
        user = simpledialog.askstring("User Login", "Enter your username:", 
                                     initialvalue=os.getenv('USERNAME', 'user1'))
        if not user:
            messagebox.showerror("Error", "Username is required")
            exit()
        self.current_user = user.strip()

    def load_data(self):
        """Load existing data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Merge with initialized data to ensure all files are present
                    for filename, file_data in loaded_data.items():
                        if filename in self.data:
                            self.data[filename].update(file_data)
            except Exception as e:
                messagebox.showwarning("Warning", f"Could not load existing data: {e}")

    def save_data(self):
        """Save all data to JSON file"""
        try:
            # Update modified timestamp
            for filename in self.data:
                self.data[filename]['modified'] = datetime.now().isoformat()
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                
            # Also export to CSV for backward compatibility
            self.export_to_csv()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save data: {e}")

    def export_to_csv(self):
        """Export current user's annotations to CSV"""
        csv_file = f"images/annotations_{self.current_user}.csv"
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "text", "confidence", "timestamp", "flags", "bookmarked"])
                
                for filename in self.image_files:
                    file_data = self.data[filename]
                    user_data = file_data['users'].get(self.current_user, {})
                    text = user_data.get('text', '')
                    confidence = user_data.get('confidence', '')
                    timestamp = user_data.get('timestamp', '')
                    flags = ', '.join(file_data.get('flags', []))
                    bookmarked = len(file_data.get('bookmarks', [])) > 0
                    
                    writer.writerow([filename, text, confidence, timestamp, flags, bookmarked])
        except Exception as e:
            messagebox.showwarning("Warning", f"Could not export CSV: {e}")

    def apply_filter(self):
        """Apply current filter to file list"""
        if self.current_filter == "all":
            self.filtered_files = self.image_files[:]
        elif self.current_filter == "annotated":
            self.filtered_files = [f for f in self.image_files 
                                 if self.current_user in self.data[f]['users'] 
                                 and self.data[f]['users'][self.current_user].get('text', '').strip()]
        elif self.current_filter == "unannotated":
            self.filtered_files = [f for f in self.image_files 
                                 if self.current_user not in self.data[f]['users'] 
                                 or not self.data[f]['users'][self.current_user].get('text', '').strip()]
        elif self.current_filter == "flagged":
            self.filtered_files = [f for f in self.image_files 
                                 if self.data[f].get('flags', [])]
        elif self.current_filter == "bookmarked":
            self.filtered_files = [f for f in self.image_files 
                                 if self.data[f].get('bookmarks', [])]
        elif self.current_filter == "consensus_needed":
            self.filtered_files = [f for f in self.image_files 
                                 if len(self.data[f]['users']) > 1 
                                 and not self.data[f].get('consensus', '').strip()]
        
        # Reset current index if needed
        if self.current_index >= len(self.filtered_files):
            self.current_index = 0

    def setup_gui(self):
        """Setup the GUI components"""
        self.root = tk.Tk()
        self.root.title(f"TrOCR Annotation Tool - User: {self.current_user}")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main container
        main_frame = tk.Frame(self.root, bg="#f0f0f0", padx=20, pady=15)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Top section: User info and filters
        self.create_header_section(main_frame)
        
        # Navigation section
        self.create_navigation_section(main_frame)
        
        # Middle section: Image display
        self.create_image_section(main_frame)
        
        # Bottom section: Text input and controls
        self.create_input_section(main_frame)
        
        # Side panel for consensus and flags
        self.create_side_panel(main_frame)
        
        # Bind keyboard shortcuts
        self.setup_keyboard_shortcuts()

    def create_header_section(self, parent):
        """Create header with user info and filters"""
        header_frame = tk.Frame(parent, bg="#2196F3", relief="solid", bd=1)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # User info
        user_frame = tk.Frame(header_frame, bg="#2196F3")
        user_frame.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        tk.Label(user_frame, text=f"User: {self.current_user}", font=("Arial", 11, "bold"), 
                bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Button(user_frame, text="Switch User", command=self.switch_user,
                 bg="#1976D2", fg="white", font=("Arial", 9), relief="flat").pack(side=tk.LEFT)
        
        # Filter controls
        filter_frame = tk.Frame(header_frame, bg="#2196F3")
        filter_frame.grid(row=0, column=1, sticky="e", padx=10, pady=5)
        
        tk.Label(filter_frame, text="Filter:", font=("Arial", 10, "bold"), 
                bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=(0, 5))
        
        self.filter_var = tk.StringVar(value="all")
        filter_options = [
            ("All Images", "all"),
            ("Annotated", "annotated"), 
            ("Unannotated", "unannotated"),
            ("Flagged", "flagged"),
            ("Bookmarked", "bookmarked"),
            ("Need Consensus", "consensus_needed")
        ]
        
        filter_menu = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                  values=[opt[0] for opt in filter_options], 
                                  state="readonly", width=15)
        filter_menu.pack(side=tk.LEFT, padx=(0, 10))
        filter_menu.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        tk.Button(filter_frame, text="Refresh", command=self.refresh_filter,
                 bg="#1976D2", fg="white", font=("Arial", 9), relief="flat").pack(side=tk.LEFT)

    def create_navigation_section(self, parent):
        """Create navigation and progress section"""
        nav_frame = tk.Frame(parent, bg="#f0f0f0")
        nav_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        nav_frame.grid_columnconfigure(1, weight=1)
        
        # Navigation controls
        nav_controls = tk.Frame(nav_frame, bg="#f0f0f0")
        nav_controls.grid(row=0, column=0, sticky="w")
        
        tk.Button(nav_controls, text="◀◀ First", command=self.first_image,
                 bg="#2196F3", fg="white", font=("Arial", 9), width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(nav_controls, text="◀ Prev", command=self.prev_image,
                 bg="#2196F3", fg="white", font=("Arial", 9), width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(nav_controls, text="Next ▶", command=self.next_image,
                 bg="#4CAF50", fg="white", font=("Arial", 9), width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(nav_controls, text="Last ▶▶", command=self.last_image, 
                 bg="#2196F3", fg="white", font=("Arial", 9), width=8).pack(side=tk.LEFT, padx=(0, 15))
        
        # Jump to specific image
        jump_frame = tk.Frame(nav_controls, bg="#f0f0f0")
        jump_frame.pack(side=tk.LEFT)
        
        tk.Label(jump_frame, text="Go to:", bg="#f0f0f0", font=("Arial", 9)).pack(side=tk.LEFT)
        self.jump_var = tk.StringVar()
        jump_entry = tk.Entry(jump_frame, textvariable=self.jump_var, width=5, font=("Arial", 9))
        jump_entry.pack(side=tk.LEFT, padx=(5, 5))
        jump_entry.bind('<Return>', self.jump_to_image)
        
        tk.Button(jump_frame, text="Go", command=self.jump_to_image,
                 bg="#FF9800", fg="white", font=("Arial", 9), width=4).pack(side=tk.LEFT)
        
        # Progress and status
        status_frame = tk.Frame(nav_frame, bg="#f0f0f0")
        status_frame.grid(row=0, column=1, sticky="e")
        
        self.progress_label = tk.Label(status_frame, text="", font=("Arial", 11, "bold"), 
                                     bg="#f0f0f0", fg="#333")
        self.progress_label.pack(side=tk.TOP, anchor="e")
        
        self.status_label = tk.Label(status_frame, text="", font=("Arial", 9), 
                                   bg="#f0f0f0", fg="#666")
        self.status_label.pack(side=tk.TOP, anchor="e")

    def create_image_section(self, parent):
        """Create image display section"""
        # Main content frame
        content_frame = tk.Frame(parent, bg="#f0f0f0")
        content_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 15))
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Image frame with border
        img_frame = tk.Frame(content_frame, bg="white", relief="solid", bd=1)
        img_frame.grid(row=0, column=0, sticky="nsew")
        img_frame.grid_rowconfigure(0, weight=1)
        img_frame.grid_columnconfigure(0, weight=1)
        
        # Image display with status indicators
        img_container = tk.Frame(img_frame, bg="white")
        img_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        img_container.grid_rowconfigure(1, weight=1)
        img_container.grid_columnconfigure(0, weight=1)
        
        # Status indicators
        self.status_indicators = tk.Frame(img_container, bg="white")
        self.status_indicators.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Image label
        self.img_label = tk.Label(img_container, bg="white", text="Loading image...", 
                                font=("Arial", 12), fg="#666")
        self.img_label.grid(row=1, column=0)
        
        # Filename and controls
        filename_frame = tk.Frame(img_frame, bg="white")
        filename_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        filename_frame.grid_columnconfigure(0, weight=1)
        
        self.filename_label = tk.Label(filename_frame, text="", font=("Arial", 10, "bold"), 
                                     bg="white", fg="#333")
        self.filename_label.grid(row=0, column=0)
        
        # Image controls
        controls_frame = tk.Frame(filename_frame, bg="white")
        controls_frame.grid(row=1, column=0, pady=(5, 0))
        
        tk.Button(controls_frame, text="🚩 Flag", command=self.toggle_flag,
                 bg="#F44336", fg="white", font=("Arial", 9), width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(controls_frame, text="🔖 Bookmark", command=self.toggle_bookmark,
                 bg="#9C27B0", fg="white", font=("Arial", 9), width=10).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(controls_frame, text="👥 View All Users", command=self.show_all_annotations,
                 bg="#607D8B", fg="white", font=("Arial", 9), width=12).pack(side=tk.LEFT)

    def create_input_section(self, parent):
        """Create text input and control section"""
        input_frame = tk.Frame(parent, bg="#f0f0f0")
        input_frame.grid(row=3, column=0, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Text input label with confidence
        label_frame = tk.Frame(input_frame, bg="#f0f0f0")
        label_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        label_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(label_frame, text="Transcription:", font=("Arial", 11, "bold"), 
                bg="#f0f0f0", fg="#333").pack(side=tk.LEFT)
        
        # Confidence selector
        conf_frame = tk.Frame(label_frame, bg="#f0f0f0")
        conf_frame.pack(side=tk.RIGHT)
        
        tk.Label(conf_frame, text="Confidence:", font=("Arial", 9), 
                bg="#f0f0f0", fg="#666").pack(side=tk.LEFT, padx=(0, 5))
        
        self.confidence_var = tk.StringVar(value="high")
        conf_menu = ttk.Combobox(conf_frame, textvariable=self.confidence_var,
                               values=["low", "medium", "high"], state="readonly", width=8)
        conf_menu.pack(side=tk.LEFT)
        
        # Text input with frame
        entry_frame = tk.Frame(input_frame, bg="white", relief="solid", bd=1)
        entry_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        entry_frame.grid_columnconfigure(0, weight=1)
        
        self.entry = tk.Entry(entry_frame, font=("Arial", 14), bg="white", fg="#333",
                            relief="flat", bd=5)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind('<Return>', lambda e: self.save_and_next())
        self.entry.bind('<Control-s>', lambda e: self.save_current())
        
        # Action buttons
        button_frame = tk.Frame(input_frame, bg="#f0f0f0")
        button_frame.grid(row=2, column=0)
        
        tk.Button(button_frame, text="Save Current (Ctrl+S)", command=self.save_current,
                 bg="#FF9800", fg="white", font=("Arial", 10), width=18, height=1,
                 relief="flat", bd=0).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="Save & Next (Enter)", command=self.save_and_next,
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=18, height=1,
                 relief="flat", bd=0).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="Skip (Space)", command=self.skip_image,
                 bg="#9E9E9E", fg="white", font=("Arial", 10), width=12, height=1,
                 relief="flat", bd=0).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="Clear Text", command=self.clear_text,
                 bg="#F44336", fg="white", font=("Arial", 10), width=12, height=1,
                 relief="flat", bd=0).pack(side=tk.LEFT)

    def create_side_panel(self, parent):
        """Create side panel for consensus and multi-user info"""
        side_frame = tk.Frame(parent, bg="#e8e8e8", relief="solid", bd=1, width=300)
        side_frame.grid(row=2, column=1, rowspan=2, sticky="nsew", padx=(10, 0))
        side_frame.grid_rowconfigure(1, weight=1)
        side_frame.grid_propagate(False)
        
        # Panel header
        header = tk.Label(side_frame, text="Multi-User Info", font=("Arial", 11, "bold"),
                         bg="#2196F3", fg="white", pady=5)
        header.grid(row=0, column=0, sticky="ew")
        
        # Scrollable content
        canvas = tk.Canvas(side_frame, bg="#e8e8e8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(side_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="#e8e8e8")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=1, column=1, sticky="ns")
        
        side_frame.grid_columnconfigure(0, weight=1)

    def update_side_panel(self):
        """Update the side panel with current image info"""
        # Clear existing content
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.filtered_files or self.current_index >= len(self.filtered_files):
            return
            
        filename = self.filtered_files[self.current_index]
        file_data = self.data[filename]
        
        y_pos = 0
        
        # All users' annotations
        if file_data['users']:
            tk.Label(self.scrollable_frame, text="User Annotations:", font=("Arial", 10, "bold"),
                    bg="#e8e8e8", fg="#333").grid(row=y_pos, column=0, sticky="w", pady=(0, 5))
            y_pos += 1
            
            for user, user_data in file_data['users'].items():
                user_frame = tk.Frame(self.scrollable_frame, bg="#f8f8f8", relief="solid", bd=1)
                user_frame.grid(row=y_pos, column=0, sticky="ew", pady=2, padx=2)
                user_frame.grid_columnconfigure(1, weight=1)
                
                # User info
                user_color = "#4CAF50" if user == self.current_user else "#2196F3"
                tk.Label(user_frame, text=user, font=("Arial", 9, "bold"),
                        bg=user_color, fg="white", padx=5).grid(row=0, column=0, sticky="w")
                
                confidence = user_data.get('confidence', 'unknown')
                conf_color = {"high": "#4CAF50", "medium": "#FF9800", "low": "#F44336"}.get(confidence, "#9E9E9E")
                tk.Label(user_frame, text=confidence, font=("Arial", 8),
                        bg=conf_color, fg="white", padx=3).grid(row=0, column=1, sticky="e", padx=(5, 0))
                
                # Text
                text = user_data.get('text', '')
                text_label = tk.Label(user_frame, text=text if text else "(no annotation)", 
                                    font=("Arial", 9), bg="#f8f8f8", fg="#333" if text else "#999",
                                    wraplength=250, justify="left")
                text_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
                
                # Timestamp
                timestamp = user_data.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        time_str = dt.strftime("%m/%d %H:%M")
                        tk.Label(user_frame, text=time_str, font=("Arial", 8),
                                bg="#f8f8f8", fg="#666").grid(row=2, column=0, columnspan=2, sticky="e", padx=5, pady=(0, 2))
                    except:
                        pass
                
                y_pos += 1
        
        # Consensus section
        tk.Label(self.scrollable_frame, text="Consensus:", font=("Arial", 10, "bold"),
                bg="#e8e8e8", fg="#333").grid(row=y_pos, column=0, sticky="w", pady=(15, 5))
        y_pos += 1
        
        consensus_frame = tk.Frame(self.scrollable_frame, bg="#fff3cd", relief="solid", bd=1)
        consensus_frame.grid(row=y_pos, column=0, sticky="ew", pady=2, padx=2)
        consensus_frame.grid_columnconfigure(0, weight=1)
        
        consensus_text = file_data.get('consensus', '')
        if consensus_text:
            tk.Label(consensus_frame, text=consensus_text, font=("Arial", 9, "bold"),
                    bg="#fff3cd", fg="#856404", wraplength=250, justify="left").grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        else:
            tk.Label(consensus_frame, text="No consensus set", font=("Arial", 9),
                    bg="#fff3cd", fg="#856404").grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        if len(file_data['users']) > 1:
            tk.Button(consensus_frame, text="Set Consensus", command=self.set_consensus,
                     bg="#28a745", fg="white", font=("Arial", 8)).grid(row=1, column=0, pady=2)
        
        y_pos += 1
        
        # Flags and bookmarks
        if file_data.get('flags') or file_data.get('bookmarks'):
            tk.Label(self.scrollable_frame, text="Status:", font=("Arial", 10, "bold"),
                    bg="#e8e8e8", fg="#333").grid(row=y_pos, column=0, sticky="w", pady=(15, 5))
            y_pos += 1
            
            if file_data.get('flags'):
                flags_text = "🚩 Flags: " + ", ".join(file_data['flags'])
                tk.Label(self.scrollable_frame, text=flags_text, font=("Arial", 9),
                        bg="#e8e8e8", fg="#d32f2f", wraplength=250).grid(row=y_pos, column=0, sticky="w", pady=2)
                y_pos += 1
            
            if file_data.get('bookmarks'):
                bookmarks_text = "🔖 Bookmarked by: " + ", ".join(file_data['bookmarks'])
                tk.Label(self.scrollable_frame, text=bookmarks_text, font=("Arial", 9),
                        bg="#e8e8e8", fg="#7b1fa2", wraplength=250).grid(row=y_pos, column=0, sticky="w", pady=2)
                y_pos += 1
        
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Control-Right>', lambda e: self.next_image())
        self.root.bind('<Control-Left>', lambda e: self.prev_image())
        self.root.bind('<Control-Home>', lambda e: self.first_image())
        self.root.bind('<Control-End>', lambda e: self.last_image())
        self.root.bind('<space>', lambda e: self.skip_image() if self.root.focus_get() != self.entry else None)
        self.root.bind('<Escape>', lambda e: self.entry.focus_set())
        self.root.bind('<F5>', lambda e: self.show_image(self.current_index))
        self.root.bind('<F1>', lambda e: self.toggle_flag())
        self.root.bind('<F2>', lambda e: self.toggle_bookmark())

    def show_image(self, index):
        """Display image at given index"""
        if not self.filtered_files or not (0 <= index < len(self.filtered_files)):
            return
            
        self.current_index = index
        filename = self.filtered_files[index]
        file_data = self.data[filename]
        
        try:
            # Load and display image
            image_path = os.path.join(self.image_dir, filename)
            img = Image.open(image_path)
            
            # Scale image appropriately
            max_width, max_height = 700, 400
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            if img.width < 200:
                scale_factor = 200 / img.width
                new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
                img = img.resize(new_size, Image.Resampling.NEAREST)
            
            photo = ImageTk.PhotoImage(img)
            self.img_label.config(image=photo, text="")
            self.img_label.image = photo
            
        except Exception as e:
            self.img_label.config(image="", text=f"Error loading image: {e}")
            self.img_label.image = None
        
        # Update status indicators
        self.update_status_indicators(filename, file_data)
        
        # Update filename
        self.filename_label.config(text=filename)
        
        # Update text entry
        self.entry.delete(0, tk.END)
        user_data = file_data['users'].get(self.current_user, {})
        existing_text = user_data.get('text', '')
        existing_confidence = user_data.get('confidence', 'high')
        
        self.entry.insert(0, existing_text)
        self.confidence_var.set(existing_confidence)
        
        # Update UI components
        self.update_progress()
        self.update_side_panel()
        
        # Keep focus on entry for continuous typing
        self.entry.focus_set()
        self.entry.icursor(tk.END)

    def update_status_indicators(self, filename, file_data):
        """Update status indicators above the image"""
        # Clear existing indicators
        for widget in self.status_indicators.winfo_children():
            widget.destroy()
        
        indicators = []
        
        # User annotation status
        if self.current_user in file_data['users'] and file_data['users'][self.current_user].get('text', '').strip():
            indicators.append(("✅ Annotated", "#4CAF50"))
        else:
            indicators.append(("❌ Not Annotated", "#F44336"))
        
        # Multi-user status
        user_count = len(file_data['users'])
        if user_count > 1:
            indicators.append((f"👥 {user_count} users", "#2196F3"))
        
        # Consensus status
        if file_data.get('consensus', '').strip():
            indicators.append(("🎯 Consensus", "#4CAF50"))
        elif user_count > 1:
            indicators.append(("❓ No Consensus", "#FF9800"))
        
        # Flags
        if file_data.get('flags'):
            flags_text = f"🚩 {len(file_data['flags'])} flags"
            indicators.append((flags_text, "#F44336"))
        
        # Bookmarks
        if file_data.get('bookmarks'):
            bookmark_text = f"🔖 {len(file_data['bookmarks'])} bookmarks"
            indicators.append((bookmark_text, "#9C27B0"))
        
        # Display indicators
        for i, (text, color) in enumerate(indicators):
            label = tk.Label(self.status_indicators, text=text, font=("Arial", 9, "bold"),
                           bg=color, fg="white", padx=8, pady=2)
            label.pack(side=tk.LEFT, padx=2)

    def update_progress(self):
        """Update progress information"""
        if not self.filtered_files:
            self.progress_label.config(text="No images match filter")
            self.status_label.config(text="")
            return
        
        # Current position in filtered list
        current_pos = self.current_index + 1
        total_filtered = len(self.filtered_files)
        
        # Overall statistics
        annotated_by_user = sum(1 for fname in self.image_files 
                               if self.current_user in self.data[fname]['users'] 
                               and self.data[fname]['users'][self.current_user].get('text', '').strip())
        total_images = len(self.image_files)
        
        progress_text = f"Image {current_pos} of {total_filtered} (filtered)"
        status_text = f"User progress: {annotated_by_user}/{total_images} ({(annotated_by_user/total_images)*100:.1f}%)"
        
        self.progress_label.config(text=progress_text)
        self.status_label.config(text=status_text)

    def save_current(self):
        """Save current annotation without moving to next"""
        if not self.filtered_files:
            return
            
        text = self.entry.get().strip()
        confidence = self.confidence_var.get()
        filename = self.filtered_files[self.current_index]
        
        # Save user annotation
        if self.current_user not in self.data[filename]['users']:
            self.data[filename]['users'][self.current_user] = {}
        
        self.data[filename]['users'][self.current_user].update({
            'text': text,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        })
        
        self.save_data()
        self.update_progress()
        self.update_side_panel()
        self.update_status_indicators(filename, self.data[filename])
        messagebox.showinfo("Saved", f"Annotation saved for {filename}")

    def save_and_next(self):
        """Save current annotation and move to next image"""
        self.save_current()
        self.next_image()

    def skip_image(self):
        """Skip current image without saving"""
        self.next_image()

    def clear_text(self):
        """Clear the text entry"""
        self.entry.delete(0, tk.END)
        self.entry.focus_set()

    def next_image(self):
        """Move to next image"""
        if not self.filtered_files:
            return
            
        if self.current_index < len(self.filtered_files) - 1:
            self.show_image(self.current_index + 1)
        else:
            messagebox.showinfo("Complete", "You've reached the last image in the current filter!")

    def prev_image(self):
        """Move to previous image"""
        if not self.filtered_files:
            return
            
        if self.current_index > 0:
            self.show_image(self.current_index - 1)
        else:
            messagebox.showinfo("Info", "You're at the first image in the current filter!")

    def first_image(self):
        """Jump to first image"""
        if self.filtered_files:
            self.show_image(0)

    def last_image(self):
        """Jump to last image"""
        if self.filtered_files:
            self.show_image(len(self.filtered_files) - 1)

    def jump_to_image(self, event=None):
        """Jump to specific image number in filtered list"""
        if not self.filtered_files:
            return
            
        try:
            target = int(self.jump_var.get())
            if 1 <= target <= len(self.filtered_files):
                self.show_image(target - 1)
                self.jump_var.set("")
            else:
                messagebox.showerror("Error", f"Please enter a number between 1 and {len(self.filtered_files)}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")

    def switch_user(self):
        """Switch to a different user"""
        new_user = simpledialog.askstring("Switch User", "Enter username:", 
                                         initialvalue=self.current_user)
        if new_user and new_user.strip() != self.current_user:
            self.current_user = new_user.strip()
            self.root.title(f"TrOCR Annotation Tool - User: {self.current_user}")
            
            # Update header
            for widget in self.root.winfo_children():
                self.setup_gui()
                break
            
            # Refresh display
            self.apply_filter()
            if self.filtered_files:
                self.show_image(0)

    def on_filter_change(self, event=None):
        """Handle filter change"""
        filter_map = {
            "All Images": "all",
            "Annotated": "annotated", 
            "Unannotated": "unannotated",
            "Flagged": "flagged",
            "Bookmarked": "bookmarked",
            "Need Consensus": "consensus_needed"
        }
        
        selected = self.filter_var.get()
        self.current_filter = filter_map.get(selected, "all")
        self.apply_filter()
        
        if self.filtered_files:
            self.show_image(0)
        else:
            # Clear display if no images match filter
            self.img_label.config(image="", text="No images match the current filter")
            self.img_label.image = None
            self.filename_label.config(text="")
            self.entry.delete(0, tk.END)
            for widget in self.status_indicators.winfo_children():
                widget.destroy()
            self.update_side_panel()
        
        self.update_progress()

    def refresh_filter(self):
        """Refresh the current filter"""
        self.apply_filter()
        if self.filtered_files:
            # Try to stay on the same image if possible
            current_filename = self.filtered_files[self.current_index] if self.current_index < len(self.filtered_files) else None
            if current_filename and current_filename in self.filtered_files:
                new_index = self.filtered_files.index(current_filename)
                self.show_image(new_index)
            else:
                self.show_image(0)
        self.update_progress()

    def toggle_flag(self):
        """Toggle flag status for current image"""
        if not self.filtered_files:
            return
            
        filename = self.filtered_files[self.current_index]
        
        # Get flag reason
        if self.current_user not in self.data[filename]['flags']:
            reason = simpledialog.askstring("Flag Image", 
                                          "Reason for flagging (optional):",
                                          initialvalue="difficult to read")
            if reason is not None:  # User didn't cancel
                flag_entry = f"{self.current_user}: {reason.strip()}" if reason.strip() else self.current_user
                self.data[filename]['flags'].append(flag_entry)
                self.save_data()
        else:
            # Remove user's flags
            self.data[filename]['flags'] = [f for f in self.data[filename]['flags'] 
                                          if not f.startswith(f"{self.current_user}:") and f != self.current_user]
            self.save_data()
        
        self.update_status_indicators(filename, self.data[filename])
        self.update_side_panel()

    def toggle_bookmark(self):
        """Toggle bookmark status for current image"""
        if not self.filtered_files:
            return
            
        filename = self.filtered_files[self.current_index]
        
        if self.current_user not in self.data[filename]['bookmarks']:
            self.data[filename]['bookmarks'].append(self.current_user)
        else:
            self.data[filename]['bookmarks'].remove(self.current_user)
        
        self.save_data()
        self.update_status_indicators(filename, self.data[filename])
        self.update_side_panel()

    def show_all_annotations(self):
        """Show a dialog with all annotations for current image"""
        if not self.filtered_files:
            return
            
        filename = self.filtered_files[self.current_index]
        file_data = self.data[filename]
        
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title(f"All Annotations - {filename}")
        dialog.geometry("600x400")
        dialog.configure(bg="#f0f0f0")
        
        # Create scrollable text area
        frame = tk.Frame(dialog, bg="#f0f0f0", padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        text_area = tk.Text(frame, font=("Arial", 11), bg="white", wrap="word")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)
        
        text_area.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate with annotations
        content = f"Image: {filename}\n{'='*50}\n\n"
        
        if file_data['users']:
            content += "USER ANNOTATIONS:\n" + "-"*30 + "\n\n"
            for user, user_data in file_data['users'].items():
                content += f"👤 {user} ({user_data.get('confidence', 'unknown')} confidence)\n"
                content += f"   Text: {user_data.get('text', '(empty)')}\n"
                timestamp = user_data.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        content += f"   Time: {dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    except:
                        pass
                content += "\n"
        
        if file_data.get('consensus'):
            content += "CONSENSUS:\n" + "-"*30 + "\n"
            content += f"📝 {file_data['consensus']}\n\n"
        
        if file_data.get('flags'):
            content += "FLAGS:\n" + "-"*30 + "\n"
            for flag in file_data['flags']:
                content += f"🚩 {flag}\n"
            content += "\n"
        
        if file_data.get('bookmarks'):
            content += "BOOKMARKS:\n" + "-"*30 + "\n"
            for bookmark in file_data['bookmarks']:
                content += f"🔖 {bookmark}\n"
        
        text_area.insert("1.0", content)
        text_area.config(state="disabled")

    def set_consensus(self):
        """Set consensus annotation for current image"""
        if not self.filtered_files:
            return
            
        filename = self.filtered_files[self.current_index]
        file_data = self.data[filename]
        
        if len(file_data['users']) < 2:
            messagebox.showwarning("Warning", "Need at least 2 user annotations to set consensus")
            return
        
        # Create consensus dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Set Consensus - {filename}")
        dialog.geometry("500x400")
        dialog.configure(bg="#f0f0f0")
        
        frame = tk.Frame(dialog, bg="#f0f0f0", padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="User Annotations:", font=("Arial", 12, "bold"),
                bg="#f0f0f0").pack(anchor="w", pady=(0, 10))
        
        # Show all user annotations with radio buttons
        consensus_var = tk.StringVar()
        
        for user, user_data in file_data['users'].items():
            text = user_data.get('text', '')
            confidence = user_data.get('confidence', 'unknown')
            
            rb_frame = tk.Frame(frame, bg="white", relief="solid", bd=1)
            rb_frame.pack(fill="x", pady=2)
            
            tk.Radiobutton(rb_frame, text=f"{user} ({confidence}): {text}", 
                          variable=consensus_var, value=text,
                          font=("Arial", 10), bg="white", anchor="w",
                          wraplength=400).pack(fill="x", padx=10, pady=5)
        
        # Custom consensus option
        tk.Label(frame, text="Or enter custom consensus:", font=("Arial", 11, "bold"),
                bg="#f0f0f0").pack(anchor="w", pady=(20, 5))
        
        custom_entry = tk.Entry(frame, font=("Arial", 11), width=50)
        custom_entry.pack(pady=5)
        
        def save_consensus():
            consensus_text = custom_entry.get().strip() or consensus_var.get()
            if consensus_text:
                self.data[filename]['consensus'] = consensus_text
                self.save_data()
                self.update_side_panel()
                messagebox.showinfo("Success", "Consensus saved!")
                dialog.destroy()
            else:
                messagebox.showwarning("Warning", "Please select or enter consensus text")
        
        tk.Button(frame, text="Save Consensus", command=save_consensus,
                 bg="#4CAF50", fg="white", font=("Arial", 11), 
                 pady=5).pack(pady=20)

    def run(self):
        """Start the application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("Error", f"Application error: {e}")

    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Save all data before closing?"):
            self.save_data()
        self.root.destroy()


if __name__ == "__main__":
    try:
        app = TrOCRAnnotationTool()
        app.run()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Startup Error", f"Could not start application: {e}")
        print(f"Error details: {e}")
        import traceback
        traceback.print_exc()