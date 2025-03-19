import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import threading
import sys
from PIL import Image, ImageTk, ImageDraw, ImageFont
import random

# Import the story poster script
# Assuming the script is named 'whatsapp_story_poster.py'
# and is in the same directory
try:
    from whatsapp_story_poster import post_whatsapp_stories
except ImportError:
    # Fallback function if import fails
    def post_whatsapp_stories(photo_directory, num_photos, headless=False):
        print(f"Would post {num_photos} photos from {photo_directory} (Headless: {headless})")
        return

class WhatsAppStoryPosterUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WhatsApp Hikaye Gönderici")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Set style
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 11))
        self.style.configure("Large.TButton", font=("Arial", 12, "bold"))
        self.style.configure("TLabel", font=("Arial", 11))
        self.style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        self.style.configure("Title.TLabel", font=("Arial", 14, "bold"))
        
        # Application variables
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.photos_dir = os.path.join(self.script_dir, "pictures")
        self.current_folder = self.photos_dir
        self.ensure_folder_exists(self.photos_dir)
        
        self.folders = self.get_subfolders()
        self.image_files = []
        self.thumbnails = {}
        self.selected_image = None
        
        # UI variables
        self.num_photos_var = tk.IntVar(value=5)
        self.status_var = tk.StringVar(value="Hazır")
        self.running = False
        self.running_thread = None
        
        # Create UI
        self.create_menu()
        self.create_main_layout()
        
        # Load initial images
        self.load_images_from_folder()
    
    def ensure_folder_exists(self, folder_path):
        """Ensure the specified folder exists."""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    
    def get_subfolders(self):
        """Get a list of subfolders in the photos directory."""
        if not os.path.exists(self.photos_dir):
            return []
        
        folders = ["Varsayılan (pictures)"]
        for item in os.listdir(self.photos_dir):
            full_path = os.path.join(self.photos_dir, item)
            if os.path.isdir(full_path):
                folders.append(item)
        
        return folders
    
    def create_menu(self):
        """Create application menu."""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Fotoğraf Ekle", command=self.add_photos)
        file_menu.add_command(label="Yeni Klasör", command=self.create_new_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.root.quit)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Seçili Fotoğrafı Sil", command=self.remove_selected)
        edit_menu.add_command(label="Tümünü Temizle", command=self.clear_all)
        menubar.add_cascade(label="Düzenle", menu=edit_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Hakkında", command=self.show_about)
        help_menu.add_command(label="Yardım", command=self.show_help)
        menubar.add_cascade(label="Yardım", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_layout(self):
        """Create the main application layout."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for title and instructions
        top_frame = ttk.Frame(main_frame, padding="10")
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(top_frame, text="WhatsApp Hikaye Gönderici", style="Title.TLabel")
        title_label.pack()
        
        instructions = ("Bu uygulama, WhatsApp hikayelerinize otomatik olarak fotoğraf göndermek için tasarlanmıştır.\n"
                        "Kullanım: Fotoğraf ekleyin → Sayısını ayarlayın → Göndermeyi başlatın → WhatsApp QR kodunu tarayın")
        ttk.Label(top_frame, text=instructions, wraplength=800).pack(pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(top_frame)
        buttons_frame.pack(pady=10)
        
        # Big Add Photos button at the top
        add_photos_btn = ttk.Button(buttons_frame, text="FOTOĞRAF EKLE", command=self.add_photos, style="Large.TButton")
        add_photos_btn.pack(side=tk.LEFT, ipadx=20, ipady=10, padx=(0, 20))
        
        # Number of photos spinner
        photo_count_frame = ttk.Frame(buttons_frame)
        photo_count_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(photo_count_frame, text="Fotoğraf Sayısı:", style="Header.TLabel").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Spinbox(photo_count_frame, from_=1, to=20, textvariable=self.num_photos_var, width=3, 
                   font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # Big Start button (with green styling) at the top
        self.top_start_btn = ttk.Button(buttons_frame, text="BAŞLAT", command=self.start_posting, style="Green.TButton")
        self.top_start_btn.configure(width=15)
        self.top_start_btn.pack(side=tk.LEFT, ipadx=20, ipady=10)
        
        # Left panel (image management)
        left_panel = ttk.LabelFrame(main_frame, text="Fotoğraf Yönetimi", padding="10")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Folder selection
        folder_frame = ttk.Frame(left_panel)
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(folder_frame, text="Klasör:").pack(side=tk.LEFT, padx=(0, 5))
        self.folder_combobox = ttk.Combobox(folder_frame, values=self.folders, state="readonly")
        self.folder_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.folder_combobox.current(0)
        self.folder_combobox.bind("<<ComboboxSelected>>", self.on_folder_changed)
        
        ttk.Button(folder_frame, text="Yeni Klasör", command=self.create_new_folder, width=12).pack(side=tk.LEFT, padx=5)
        
        # Images list with thumbnails
        self.create_image_list(left_panel)
        
        # Image management buttons
        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Fotoğraf Ekle", command=self.add_photos).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Seçili Fotoğrafı Sil", command=self.remove_selected).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Tümünü Temizle", command=self.clear_all).pack(side=tk.RIGHT)
        
        # Right panel (preview, settings and controls)
        right_panel = ttk.Frame(main_frame, padding="10", width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_panel.pack_propagate(False)  # Prevent the frame from shrinking
        
        # Image preview frame
        preview_frame = ttk.LabelFrame(right_panel, text="Fotoğraf Önizleme", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.preview_canvas = tk.Canvas(preview_frame, bg="white", highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Settings
        settings_frame = ttk.LabelFrame(right_panel, text="Ayarlar", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Random selection info
        ttk.Label(settings_frame, text="Not: Fotoğraflar mevcut klasörden\nrastgele seçilecektir.", style="Header.TLabel").pack(pady=5)
        
        # Controls
        controls_frame = ttk.LabelFrame(right_panel, text="Kontroller", padding="10")
        controls_frame.pack(fill=tk.X)
        
        self.start_button = ttk.Button(controls_frame, text="GÖNDERMEYİ BAŞLAT", command=self.start_posting, style="Large.TButton")
        self.start_button.pack(fill=tk.X, pady=(0, 5), ipady=5)
        
        self.stop_button = ttk.Button(controls_frame, text="DURDUR", command=self.stop_posting, state=tk.DISABLED)
        self.stop_button.pack(fill=tk.X, ipady=5)
        
        # Status
        status_frame = ttk.LabelFrame(right_panel, text="Durum", padding="10")
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, wraplength=250, style="Header.TLabel")
        self.status_label.pack(fill=tk.X)
        
    def create_image_list(self, parent):
        """Create the image list frame with thumbnails."""
        # Create frame for image list
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable canvas for thumbnails
        canvas_frame = ttk.Frame(list_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create a frame inside the canvas to hold the thumbnails
        self.thumbnails_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.thumbnails_frame, anchor=tk.NW)
        
        # Configure style for green start button
        self.style.configure("Green.TButton", foreground="black", background="green")
        self.style.map("Green.TButton",
                  foreground=[('pressed', 'black'), ('active', 'black')],
                  background=[('pressed', 'dark green'), ('active', 'green')])
        
        # Configure scrolling
        self.thumbnails_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Enable mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
    
    def on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        """When the canvas is resized, resize the inner frame to match."""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def load_images_from_folder(self):
        """Load and display image thumbnails from the current folder."""
        # Clear existing thumbnails
        for widget in self.thumbnails_frame.winfo_children():
            widget.destroy()
        
        self.image_files = []
        self.thumbnails = {}
        
        # Get image files from folder
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        if os.path.exists(self.current_folder):
            for filename in os.listdir(self.current_folder):
                file_path = os.path.join(self.current_folder, filename)
                if os.path.isfile(file_path) and any(filename.lower().endswith(ext) for ext in valid_extensions):
                    self.image_files.append(file_path)
        
        # Display thumbnails
        if not self.image_files:
            no_images_label = ttk.Label(
                self.thumbnails_frame, 
                text="Bu klasörde hiç fotoğraf yok.\n'FOTOĞRAF EKLE' düğmesine tıklayarak fotoğraf ekleyebilirsiniz.",
                wraplength=300,
                style="Header.TLabel"
            )
            no_images_label.pack(pady=20)
            
            # Add a big add photos button in the center
            add_btn = ttk.Button(
                self.thumbnails_frame, 
                text="FOTOĞRAF EKLE", 
                command=self.add_photos,
                style="Large.TButton"
            )
            add_btn.pack(pady=10, ipadx=20, ipady=10)
            return
        
        # Calculate layout
        canvas_width = self.canvas.winfo_width()
        thumbnail_size = 120
        margin = 10
        columns = max(1, (canvas_width - margin) // (thumbnail_size + margin))
        
        # Create thumbnail widgets
        for i, file_path in enumerate(self.image_files):
            row = i // columns
            col = i % columns
            
            frame = ttk.Frame(self.thumbnails_frame, padding=5)
            frame.grid(row=row, column=col, padx=5, pady=5)
            
            # Create thumbnail
            try:
                img = Image.open(file_path)
                img.thumbnail((thumbnail_size, thumbnail_size))
                
                # Add a light border
                img_with_border = Image.new("RGB", (img.width + 2, img.height + 2), "#DDDDDD")
                img_with_border.paste(img, (1, 1))
                
                photo = ImageTk.PhotoImage(img_with_border)
                self.thumbnails[file_path] = photo  # Keep a reference
                
                # Add thumbnail label
                label = ttk.Label(frame, image=photo, cursor="hand2")
                label.image = photo
                label.pack()
                
                # Add filename label
                filename = os.path.basename(file_path)
                short_name = filename[:15] + "..." if len(filename) > 15 else filename
                name_label = ttk.Label(frame, text=short_name, wraplength=thumbnail_size)
                name_label.pack()
                
                # Bind click event
                label.bind("<Button-1>", lambda e, path=file_path: self.on_thumbnail_click(path))
            except Exception as e:
                ttk.Label(frame, text=f"Hata\n{os.path.basename(file_path)}").pack()
    
    def on_thumbnail_click(self, file_path):
        """Handle thumbnail click event to show preview."""
        self.selected_image = file_path
        self.show_preview(file_path)
    
    def show_preview(self, file_path):
        """Show larger preview of the selected image."""
        # Clear the canvas
        self.preview_canvas.delete("all")
        
        try:
            # Open and resize image for preview
            img = Image.open(file_path)
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            # Skip if canvas size is not yet determined
            if canvas_width <= 1 or canvas_height <= 1:
                self.preview_canvas.after(100, lambda: self.show_preview(file_path))
                return
            
            # Resize image while maintaining aspect ratio
            img_width, img_height = img.size
            ratio = min(canvas_width / img_width, canvas_height / img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            img = img.resize((new_width, new_height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # Keep a reference to prevent garbage collection
            self.preview_photo = photo
            
            # Add image to canvas
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=photo)
            
            # Add file name as text
            filename = os.path.basename(file_path)
            self.preview_canvas.create_text(
                canvas_width // 2, 
                canvas_height - 20, 
                text=filename,
                fill="black"
            )
        except Exception as e:
            # Show error message
            self.preview_canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text=f"Fotoğraf yüklenirken hata oluştu:\n{str(e)}",
                fill="red"
            )
    
    def add_photos(self):
        """Open file dialog to add photos to the current folder."""
        filetypes = [
            ("Fotoğraf dosyaları", "*.jpg *.jpeg *.png *.gif *.bmp"),
            ("JPEG dosyaları", "*.jpg *.jpeg"),
            ("PNG dosyaları", "*.png"),
            ("Tüm dosyalar", "*.*")
        ]
        
        filenames = filedialog.askopenfilenames(
            title="Eklemek için fotoğraf seçin",
            filetypes=filetypes
        )
        
        if not filenames:
            return
        
        # Ensure destination folder exists
        self.ensure_folder_exists(self.current_folder)
        
        # Copy files to the current folder
        copied_count = 0
        for src_path in filenames:
            try:
                filename = os.path.basename(src_path)
                dest_path = os.path.join(self.current_folder, filename)
                
                # Check if file already exists
                if os.path.exists(dest_path):
                    # Add a suffix to avoid overwriting
                    base, ext = os.path.splitext(filename)
                    dest_path = os.path.join(self.current_folder, f"{base}_{random.randint(1000, 9999)}{ext}")
                
                shutil.copy2(src_path, dest_path)
                copied_count += 1
            except Exception as e:
                messagebox.showerror("Hata", f"{src_path} kopyalanırken hata oluştu:\n{str(e)}")
        
        # Reload the images
        self.load_images_from_folder()
        
        if copied_count > 0:
            self.status_var.set(f"{copied_count} fotoğraf {os.path.basename(self.current_folder)} klasörüne eklendi")
    
    def remove_selected(self):
        """Remove the selected image from the folder."""
        if not self.selected_image:
            messagebox.showinfo("Seçim Yok", "Lütfen silmek için bir fotoğraf seçin.")
            return
        
        try:
            file_to_remove = self.selected_image
            response = messagebox.askyesno(
                "Silmeyi Onayla",
                f"{os.path.basename(file_to_remove)} fotoğrafını silmek istediğinizden emin misiniz?"
            )
            
            if response:
                os.remove(file_to_remove)
                self.selected_image = None
                
                # Reload the images
                self.load_images_from_folder()
                
                # Clear the preview
                self.preview_canvas.delete("all")
                
                self.status_var.set(f"{os.path.basename(file_to_remove)} silindi")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya silinirken hata oluştu:\n{str(e)}")
    
    def clear_all(self):
        """Remove all images from the current folder."""
        if not self.image_files:
            messagebox.showinfo("Klasör Boş", "Silinecek fotoğraf yok.")
            return
        
        response = messagebox.askyesno(
            "Tümünü Silmeyi Onayla",
            f"{os.path.basename(self.current_folder)} klasöründeki TÜM fotoğrafları silmek istediğinizden emin misiniz?"
        )
        
        if not response:
            return
        
        try:
            deleted_count = 0
            for file_path in self.image_files:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except:
                    pass
            
            self.selected_image = None
            
            # Reload the images
            self.load_images_from_folder()
            
            # Clear the preview
            self.preview_canvas.delete("all")
            
            self.status_var.set(f"{deleted_count} fotoğraf silindi")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosyalar silinirken hata oluştu:\n{str(e)}")
    
    def create_new_folder(self):
        """Create a new subfolder in the photos directory."""
        folder_name = tk.simpledialog.askstring(
            "Yeni Klasör",
            "Yeni klasör için bir isim girin:",
            parent=self.root
        )
        
        if not folder_name:
            return
        
        # Clean folder name
        folder_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in folder_name)
        
        try:
            new_folder_path = os.path.join(self.photos_dir, folder_name)
            if os.path.exists(new_folder_path):
                messagebox.showerror("Hata", f"'{folder_name}' klasörü zaten var.")
                return
            
            os.makedirs(new_folder_path)
            
            # Update folders list
            self.folders = self.get_subfolders()
            self.folder_combobox['values'] = self.folders
            
            # Select the new folder
            self.folder_combobox.set(folder_name)
            
            # Update current folder
            self.current_folder = new_folder_path
            
            # Reload images (which will be empty for the new folder)
            self.load_images_from_folder()
            
            self.status_var.set(f"'{folder_name}' klasörü oluşturuldu")
        except Exception as e:
            messagebox.showerror("Hata", f"Klasör oluşturulurken hata oluştu:\n{str(e)}")
    
    def on_folder_changed(self, event):
        """Handle folder selection change."""
        selected = self.folder_combobox.get()
        
        if selected == "Varsayılan (pictures)":
            self.current_folder = self.photos_dir
        else:
            self.current_folder = os.path.join(self.photos_dir, selected)
        
        # Reload images for the selected folder
        self.load_images_from_folder()
        
        # Clear the preview
        self.preview_canvas.delete("all")
        
        self.status_var.set(f"'{selected}' klasörüne geçildi")
    
    def start_posting(self):
        """Start the WhatsApp story posting process."""
        if self.running:
            messagebox.showinfo("Zaten Çalışıyor", "İşlem zaten çalışıyor.")
            return
        
        # Check if there are images in the current folder
        if not self.image_files:
            messagebox.showerror("Fotoğraf Yok", "Mevcut klasörde gönderilebilecek fotoğraf yok.")
            return
        
        num_photos = self.num_photos_var.get()
        
        # Check if enough photos
        if len(self.image_files) < num_photos:
            response = messagebox.askyesno(
                "Yeterli Fotoğraf Yok",
                f"{num_photos} fotoğraf göndermek istiyorsunuz ancak klasörde sadece {len(self.image_files)} fotoğraf var.\n\n"
                f"{len(self.image_files)} fotoğrafla devam etmek istiyor musunuz?"
            )
            
            if not response:
                return
            
            num_photos = len(self.image_files)
            self.num_photos_var.set(num_photos)
        
        # Show instructions before starting
        messagebox.showinfo(
            "Bilgi",
            "Gönderme işlemi başlatılıyor!\n\n"
            "1. WhatsApp Web tarayıcıda açılacak\n"
            "2. QR kodu telefonunuzla taramanız gerekecek\n"
            "3. Ardından işlem otomatik olarak devam edecek\n\n"
            "Devam etmek için OK'a tıklayın."
        )
        
        # Update UI state
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.top_start_btn.config(state=tk.DISABLED)
        self.bottom_start_btn.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("WhatsApp Hikaye Gönderici başlatılıyor...")
        
        # Start the process in a separate thread
        self.running_thread = threading.Thread(
            target=self.run_posting_process,
            args=(self.current_folder, num_photos, False)  # Always run with headless=False
        )
        self.running_thread.daemon = True
        self.running_thread.start()
    
    def run_posting_process(self, folder, num_photos, headless):
        """Run the WhatsApp story posting process in a separate thread."""
        try:
            self.update_status(f"{os.path.basename(folder)} klasöründen {num_photos} fotoğraf gönderiliyor...")
            post_whatsapp_stories(folder, num_photos, headless)
            self.update_status("Gönderme işlemi tamamlandı!")
        except Exception as e:
            self.update_status(f"Hata: {str(e)}")
        finally:
            # Reset UI state
            self.root.after(0, self.reset_ui_state)
    
    def update_status(self, message):
        """Update the status message from a thread."""
        self.root.after(0, lambda: self.status_var.set(message))
    
    def reset_ui_state(self):
        """Reset the UI state after the posting process."""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.top_start_btn.config(state=tk.NORMAL)
        self.bottom_start_btn.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def stop_posting(self):
        """Stop the WhatsApp story posting process."""
        if not self.running:
            return
        
        response = messagebox.askyesno(
            "Durdurmayı Onayla",
            "Gönderme işlemini durdurmak istediğinizden emin misiniz?\n\n"
            "Bu, tarayıcının açık kalmasına neden olabilir."
        )
        
        if not response:
            return
        
        self.status_var.set("İşlem durduruluyor... Lütfen bekleyin.")
        
        # There's no clean way to stop the Selenium process
        # We can only terminate the thread, which isn't recommended
        # Instead, we'll just update the UI to reflect the stopped state
        # and the user will need to manually close the browser
        
        self.reset_ui_state()
        self.status_var.set("İşlem durduruldu. Tarayıcıyı manuel olarak kapatmanız gerekebilir.")
    
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "WhatsApp Hikaye Gönderici Hakkında",
            "WhatsApp Hikaye Gönderici\n\n"
            "WhatsApp Hikayelerinize otomatik olarak fotoğraf göndermek için bir araç\n\n"
            "© 2023"
        )
    
    def show_help(self):
        """Show help dialog."""
        help_text = (
            "WhatsApp Hikaye Gönderici Yardımı\n\n"
            "1. Fotoğraf Ekle: 'FOTOĞRAF EKLE' düğmesine tıklayarak fotoğrafları seçili klasöre ekleyin\n\n"
            "2. Klasör Oluştur: 'Yeni Klasör' düğmesine tıklayarak farklı fotoğraf grupları için klasörler oluşturun\n\n"
            "3. Sayıyı Ayarla: Göndermek istediğiniz fotoğraf sayısını ayarlayın\n\n"
            "4. Göndermeyi Başlat: 'GÖNDERMEYİ BAŞLAT' düğmesine tıklayarak otomatik gönderme işlemini başlatın\n\n"
            "5. QR Kodu Tara: Tarayıcı açıldığında, WhatsApp QR kodunu telefonunuzla tarayın.\n\n"
            "Not: Fotoğraflar seçili klasörden rastgele seçilecektir."
        )
        messagebox.showinfo("Yardım", help_text)


if __name__ == "__main__":
    # Ensure that PIL is installed
    try:
        import PIL
    except ImportError:
        print("Hata: PIL (Pillow) gereklidir. Lütfen şu komutla yükleyin:")
        print("pip install pillow")
        sys.exit(1)
    
    # Create the Tkinter application
    root = tk.Tk()
    app = WhatsAppStoryPosterUI(root)
    root.mainloop()