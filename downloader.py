import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from concurrent.futures import ThreadPoolExecutor

class DownloaderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Universal Downloader")
        self.urls = []
        self.output_dir = os.getcwd()
        self.total = 0
        self.completed = 0
        self.download_audio = tk.BooleanVar(value=False)
        
        # UI Components
        self.url_frame = ttk.LabelFrame(self.root, text="URLs (one per line)")
        self.url_text = tk.Text(self.url_frame, height=10, width=50)
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.status = ttk.Label(self.root, text="Ready")
        self.output_btn = ttk.Button(self.root, text="Output Folder", command=self.choose_output)
        
        # Audio Checkbox
        self.audio_checkbox = ttk.Checkbutton(
            self.root,
            text="Download Audio Only",
            variable=self.download_audio
        )
        
        self.start_btn = ttk.Button(self.root, text="Start Downloads", command=self.start_downloads)
        
        # Layout
        self.url_frame.pack(padx=10, pady=10, fill='both')
        self.url_text.pack(padx=5, pady=5)
        self.output_btn.pack(pady=5)
        self.audio_checkbox.pack(pady=5)
        self.start_btn.pack(pady=5)
        self.progress.pack(padx=10, pady=5, fill='x')
        self.status.pack(pady=5)
        
    def choose_output(self):
        self.output_dir = filedialog.askdirectory() or self.output_dir

    def start_downloads(self):
        self.urls = self.url_text.get("1.0", tk.END).strip().split('\n')
        if not self.urls:
            messagebox.showwarning("No URLs", "Please enter at least one URL")
            return
            
        self.total = len(self.urls)
        self.completed = 0
        self.start_btn.config(state=tk.DISABLED)
        self.progress['maximum'] = self.total
        self.progress['value'] = 0
        
        self.executor = ThreadPoolExecutor()
        self.futures = [self.executor.submit(self.download, url) for url in self.urls]
        self.root.after(100, self.check_progress)

    def download(self, url):
        try:
            import yt_dlp
            ydl_opts = {
                'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [self.ydl_progress_hook],
                'quiet': True,
                'no_warnings': True,
                'format': 'bestaudio' if self.download_audio.get() else 'best',
                'merge_output_format': 'mp4'  # Ensure audio/video merged properly
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return (True, filename)
        except ImportError:
            try:
                response = requests.get(url, stream=True, timeout=10)
                response.raise_for_status()
                filename = os.path.join(self.output_dir, url.split('/')[-1])
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(8192):
                        f.write(chunk)
                return (True, filename)
            except Exception as e:
                return (False, (url, str(e)))
        except Exception as e:
            return (False, (url, str(e)))

    def ydl_progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            self.root.after(0, lambda: self.status.config(text=f"Downloading: {d['filename']} ({percent})"))
        elif d['status'] == 'finished':
            self.root.after(0, self.update_progress)

    def update_progress(self):
        self.completed += 1
        self.progress['value'] = self.completed
        self.status.config(text=f"Completed {self.completed}/{self.total}")

    def check_progress(self):
        if self.completed == self.total:
            self.executor.shutdown()
            self.show_results()
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.root.after(100, self.check_progress)

    def show_results(self):
        results = [f.result() for f in self.futures]
        success = sum(1 for r in results if r[0])
        errors = [r[1] for r in results if not r[0]]
        
        message = f"✅ Success: {success}/{self.total}\n"
        if errors:
            message += "\n❌ Errors:\n" + "\n".join([f"- {e[0]}: {e[1]}" for e in errors])
            
        messagebox.showinfo("Download Complete", message)

if __name__ == "__main__":
    try:
        import yt_dlp
    except ImportError:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing Dependency", 
            "This program requires yt-dlp to download videos/audio.\n\n"
            "Install it using: pip install yt-dlp")
        root.destroy()
    else:
        app = DownloaderApp()
        app.root.mainloop()