import tkinter as tk
from tkinter import messagebox, ttk
import os, webbrowser, json, threading, queue, time, concurrent.futures, ssl
from pathlib import Path
from collections import OrderedDict
from requests.adapters import HTTPAdapter

exec("import subprocess, sys\nfor m in ['requests','urllib3']:\n try: __import__(m)\n except ImportError: subprocess.check_call([sys.executable,'-m','pip','install',m])")
import requests, urllib3
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

show_selected_only = False

json_files = [
    "BROWSERS.json",
    "COMMUNICATION.json",
    "DEVELOPMENT.json",
    "DOCUMENT.json",
    "GAMES.json",
    "MICROSOFTTOOLS.json",
    "MULTIMEDIATOOLS.json",
    "PROTOOLS.json",
    "UTILITIES.json",
]

base_url = "https://raw.githubusercontent.com/its-Jaxx/MS-Installer/main/JSON/"
icon_url = "https://raw.githubusercontent.com/its-Jaxx/MS-Installer/main/MEDIA/ICON.ico"
headers = {"User-Agent": "Mozilla/5.0"}

apps = OrderedDict()
app_data_lock = threading.Lock()
status_queue = queue.Queue()

cache_dir = Path(os.getenv('LocalAppData')) / 'MS-Installer'
cache_dir.mkdir(parents=True, exist_ok=True)

class ToolTip:
    def __init__(self, widget, text, delay=1000):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.delay = delay
        widget.bind("<Enter>", self.schedule)
        widget.bind("<Leave>", self.unschedule)

    def schedule(self, event=None):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)

    def unschedule(self, event=None):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        self.hide()

    def show(self):
        if self.tipwindow or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert") or (0, 0, 0, 0)
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify="left",
                         background="#333333", foreground="#ffffff",
                         relief="solid", borderwidth=1,
                         font=("Segoe UI", 9),
                         wraplength=300)
        label.pack(ipadx=4)

    def hide(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def get_user_friendly_error(exception):
    if isinstance(exception, requests.exceptions.ConnectionError):
        return "Connection Error: Check your internet connection."
    elif isinstance(exception, requests.exceptions.Timeout):
        return "Request timed out. Please try again."
    elif isinstance(exception, requests.exceptions.HTTPError):
        if exception.response.status_code == 404:
            return "Resource not found. The file may have been moved or deleted."
        else:
            return f"HTTP Error {exception.response.status_code}"
    elif isinstance(exception, ssl.SSLCertVerificationError):
        return "SSL Certificate Error: Connection not secure."
    else:
        return f"Error: {str(exception)}"

def fetch_file(url, session=None):
    try:
        session = session or requests_retry_session()
        response = session.get(url, headers=headers, timeout=10, verify=True)
        response.raise_for_status()
        return response
    except Exception as e:
        return get_user_friendly_error(e)

def fetch_icon():
    try:
        icon_path = cache_dir / "icon.ico"
        
        if not icon_path.exists() or time.time() - icon_path.stat().st_mtime > 86400:
            response = fetch_file(icon_url)
            if not isinstance(response, str):
                with open(icon_path, "wb") as f:
                    f.write(response.content)
        
        if icon_path.exists():
            root.iconbitmap(str(icon_path))
    except Exception as e:
        status_queue.put(("error", f"Icon Error: {get_user_friendly_error(e)}"))

def save_cache():
    cache_data = {
        "timestamp": time.time(),
        "apps": apps
    }
    with open(cache_dir / "cache.json", "w") as f:
        json.dump(cache_data, f)

def load_cache():
    cache_file = cache_dir / "cache.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
            if time.time() - cache_data["timestamp"] < 86400:
                ordered_apps = OrderedDict()
                for category in cache_data["apps"]:
                    ordered_apps[category] = cache_data["apps"][category]
                return ordered_apps
        except:
            pass
    return None

def fetch_json_files():
    global apps
    cached_apps = load_cache()
    
    if cached_apps:
        with app_data_lock:
            apps = cached_apps
        status_queue.put(("status", "Loaded items from cache")); time.sleep(3)
        status_queue.put(("status", ""))
        status_queue.put(("update", None))
        return
    
    status_queue.put(("status", "No cache found - Starting download"))
    
    session = requests_retry_session()
    futures = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for filename in json_files:
            url = base_url + filename
            futures[filename] = executor.submit(fetch_file, url, session)
    
    for filename in json_files:
        future = futures[filename]
        try:
            result = future.result()
            if isinstance(result, str):
                status_queue.put(("error", f"Error fetching {filename}: {result}"))
            else:
                data = json.loads(result.text)
                category = next(iter(data))
                with app_data_lock:
                    apps[category] = data[category]
                status_queue.put(("category", category))
        except Exception as e:
            status_queue.put(("error", f"Error processing {filename}: {get_user_friendly_error(e)}"))
    
    save_cache()
    status_queue.put(("update", None))
    status_queue.put(("status", ""))

root = tk.Tk()
root.title("MS Installer")
root.geometry("1400x800")
root.configure(bg="#1e1e1e")

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=0)
root.grid_columnconfigure(1, weight=1)

selected_apps = set()
package_manager = tk.StringVar(value="winget")
package_manager.trace_add("write", lambda *args: populate_apps(search_var.get().lower()))
installer_format = tk.StringVar(value="py")

SEARCH_TEXT_COLOR = "#ffffff"
BOX_COLOR = "#2d2d2d"
HIGHLIGHT_COLOR = "#3b70a5"
BUTTON_ACTIVE = "#4a90d9"
TEXT_COLOR = "#ff00ff"
BTN_TEXT_COLOR = "#d0d0d0"

left_frame = tk.Frame(root, bg=BOX_COLOR, padx=10, pady=10)
left_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)

def options_btn(btn_text, btn_value, btn_var):
    tk.Radiobutton(left_frame, text=btn_text, variable=btn_var, value=btn_value,
               bg=BOX_COLOR, fg=BTN_TEXT_COLOR, selectcolor=BOX_COLOR, activebackground=BOX_COLOR,
               activeforeground=TEXT_COLOR, highlightthickness=0).pack(anchor="w", padx=30)

tk.Label(left_frame, text="Package Manager", bg=BOX_COLOR, fg=TEXT_COLOR, 
        font=("Segoe UI", 10, "bold")).pack(pady=(20, 5), anchor="w", padx=20)
options_btn("Winget", "winget", package_manager); options_btn("Chocolatey", "choco", package_manager)

tk.Label(left_frame, text="Installer Format", bg=BOX_COLOR, fg=TEXT_COLOR, 
        font=("Segoe UI", 10, "bold")).pack(pady=(20, 5), anchor="w", padx=20)
options_btn("Python (.py)", "py", installer_format); options_btn("Powershell (.ps1)", "ps1", installer_format); options_btn("Batch (.bat)", "bat", installer_format)

def clear_selection():
    for app, btn in list(app_buttons.items()):
        if str(btn) in root.children or btn.winfo_exists():
            btn.config(bg=BOX_COLOR)
    selected_apps.clear()

def about_installer():
    webbrowser.open("https://github.com/its-Jaxx/MS-Installer?tab=readme-ov-file")

def show_selected():
    global show_selected_only
    show_selected_only = not show_selected_only
    if show_selected_only:
        populate_apps(search_var.get().lower(), selected_only=True)
        show_selected_btn.config(text="Show Full List")
    else:
        populate_apps(search_var.get().lower())
        show_selected_btn.config(text="Show Selected Apps")

def btn_gen(btn_text, btn_cmd, pady=10):
    btn = tk.Button(left_frame, text=btn_text, command=btn_cmd,
          bg=BOX_COLOR, fg=BTN_TEXT_COLOR, activebackground=BUTTON_ACTIVE, activeforeground=TEXT_COLOR,
          relief="flat", highlightthickness=0, bd=0)
    btn.pack(pady=(pady, 10), padx=20, fill="x")
    return btn

btn_gen("Clear Selection", clear_selection, 40)

show_selected_btn = tk.Button(left_frame, text="Show Selected Apps", command=show_selected,
    bg=BOX_COLOR, fg=BTN_TEXT_COLOR, activebackground=BUTTON_ACTIVE, activeforeground=TEXT_COLOR,
    relief="flat", highlightthickness=0, bd=0)
show_selected_btn.pack(pady=(10, 10), padx=20, fill="x")

btn_gen("Generate Installer", lambda: generate_installer())
btn_gen("About", lambda: about_installer())

right_frame = tk.Frame(root, bg=BOX_COLOR, padx=10, pady=10)
right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
right_frame.grid_rowconfigure(2, weight=1)
right_frame.grid_columnconfigure(0, weight=1)

search_frame = tk.Frame(right_frame, bg=BOX_COLOR)
search_frame.grid(row=0, column=0, pady=10, sticky="ew")
search_frame.grid_columnconfigure(0, weight=1)

search_var = tk.StringVar()
search_entry = tk.Entry(
    search_frame, textvariable=search_var, bg="#252526", fg=TEXT_COLOR,
    insertbackground=TEXT_COLOR, relief="flat", font=("Segoe UI", 10), width=40,
    highlightthickness=0, bd=2, highlightbackground="#444", highlightcolor="#555"
)
search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

search_icon = tk.Label(
    search_frame, text="\U0001F50D", bg=BOX_COLOR, fg=SEARCH_TEXT_COLOR, font=("Segoe UI", 10)
)
search_icon.grid(row=0, column=1, sticky="w")

status_label = tk.Label(
    right_frame, 
    text="Initializing...", 
    bg=BOX_COLOR, 
    fg=TEXT_COLOR,
    anchor="w",
    font=("Segoe UI", 9)
)
status_label.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 5))

canvas_frame = tk.Frame(right_frame, bg=BOX_COLOR)
canvas_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
canvas_frame.grid_rowconfigure(0, weight=1)
canvas_frame.grid_columnconfigure(0, weight=1)

canvas = tk.Canvas(canvas_frame, bg=BOX_COLOR, highlightthickness=0)
scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg=BOX_COLOR)

scrollable_frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

def _on_yscroll(first, last):
    scrollbar.set(first, last)

canvas.configure(yscrollcommand=_on_yscroll)
scrollbar.config(command=canvas.yview)

def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)
canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

def _configure_scrollregion(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

scrollable_frame.bind("<Configure>", _configure_scrollregion)

def _configure_canvas(event):
    canvas.itemconfig(scrollable_frame_id, width=event.width)

canvas.bind("<Configure>", _configure_canvas)

canvas.grid(row=0, column=0, sticky="nsew")
scrollbar.grid(row=0, column=1, sticky="ns")

app_buttons, app_widgets = {}, {}
last_columns = 0
processing_category = False

def calculate_columns(available_width):
    return min(max(1, available_width // 140), 10)

def toggle_app(app_name, button):
    if app_name in selected_apps:
        selected_apps.remove(app_name)
        button.config(bg=BOX_COLOR)
    else:
        selected_apps.add(app_name)
        button.config(bg=HIGHLIGHT_COLOR)

def init_app():
    threading.Thread(target=fetch_json_files, daemon=True).start()
    threading.Thread(target=fetch_icon, daemon=True).start()
    root.after(100, check_status_queue)

def check_status_queue():
    try:
        while True:
            msg_type, content = status_queue.get_nowait()
            
            if msg_type == "status":
                status_label.config(text=content)
            
            elif msg_type == "update":
                populate_apps(search_var.get().lower(), selected_only=show_selected_only)
            
            elif msg_type == "category":
                status_label.config(text=f"Processing {content}...")
            
            elif msg_type == "error":
                status_label.config(text=content)
                messagebox.showerror("Error", content)
        
    except queue.Empty:
        pass
    
    root.after(100, check_status_queue)

def populate_apps(filter_text="", selected_only=False):
    global last_columns, processing_category
    
    if processing_category:
        return
    
    processing_category = True
    try:
        canvas_frame.update_idletasks()
        current_width = canvas_frame.winfo_width()
        if current_width < 100:
            current_width = 800
            
        available_width = max(300, current_width - 40)
        max_cols = calculate_columns(available_width)
        last_columns = max_cols

        for widget in scrollable_frame.winfo_children():
            widget.destroy()

        filter_text = filter_text.lower().strip()
        
        with app_data_lock:
            if not apps:
                empty_label = tk.Label(scrollable_frame, text="Loading applications...", 
                                     bg=BOX_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 12))
                empty_label.pack(pady=50)
            else:
                for category, items in apps.items():
                    if selected_only:
                        filtered_items = {k: v for k, v in items.items() if k in selected_apps and (filter_text in k.lower() if filter_text else True)}
                    else:
                        filtered_items = {k: v for k, v in items.items() if filter_text in k.lower()} if filter_text else items

                    if not filtered_items:
                        continue
                    
                    cat_label = tk.Label(scrollable_frame, text=category, bg=BOX_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold"))
                    cat_label.pack(anchor="w", pady=(15, 5), padx=10)

                    group_frame = tk.Frame(scrollable_frame, bg=BOX_COLOR)
                    group_frame.pack(anchor="w", fill="x", padx=20)

                    row = col = 0
                    manager = package_manager.get()
                    for app_name, app_data in filtered_items.items():
                        if app_data.get(manager, "").lower() == "n/a":
                            continue
                        display_text = app_name if len(app_name) <= 21 else app_name[:16] + "..."
                        btn = tk.Button(
                            group_frame,
                            text=display_text,
                            width=15,
                            bg=HIGHLIGHT_COLOR if app_name in selected_apps else BOX_COLOR,
                            fg=BTN_TEXT_COLOR,
                            relief="flat",
                            activebackground=BUTTON_ACTIVE,
                            activeforeground=TEXT_COLOR,
                            highlightthickness=0,
                            command=lambda name=app_name: toggle_app(name, app_buttons.get(name))
                        )
                        btn.grid(row=row, column=col, padx=5, pady=1, sticky="w")
                        app_buttons[app_name] = btn
                        if "desc" in app_data:
                            ToolTip(btn, app_data["desc"])
                        col += 1
                        if col >= max_cols:
                            col = 0; row += 1

        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.yview_moveto(0)
        
    finally:
        processing_category = False

def update_search(*args):
    populate_apps(search_var.get().lower(), selected_only=show_selected_only)

search_var.trace_add("write", update_search)

resize_timer = None

def handle_resize(event):
    global resize_timer
    if event.widget == root:
        if resize_timer:
            root.after_cancel(resize_timer)
        resize_timer = root.after(150, lambda: populate_apps(search_var.get().lower()))

root.bind("<Configure>", handle_resize)

manager = package_manager.get()
fmt = installer_format.get()

def winget_installer(pkg_id):
    return f"winget install --id {pkg_id} -e --accept-package-agreements --accept-source-agreements"

def choco_installer(pkg_id):
    return f"choco install {pkg_id} -y"

def create_manager_installer_lines():
    lines = []
    for app_name in selected_apps:
        for cat in apps:
            if app_name in apps[cat]:
                pkg_id = apps[cat][app_name].get(manager)
                if pkg_id and pkg_id.lower() != "n/a":
                    if manager == "winget":
                        lines.append(winget_installer(pkg_id))
                    else:
                        lines.append(choco_installer(pkg_id))
                break
    return lines

def generate_installer():
    if not selected_apps:
        messagebox.showerror("Error", "No applications selected.")
        return
    
    lines = []

    if fmt == "py":
        lines += [
            "import sys, subprocess, os, ctypes\n\ndef is_admin():\n    try:\n        return ctypes.windll.shell32.IsUserAnAdmin()\n    except:\n        return False\n\nif not is_admin():\n    script = os.path.abspath(sys.argv[0])\n    params = ' '.join([f'\"{arg}\"' for arg in sys.argv[1:]])\n    ctypes.windll.shell32.ShellExecuteW(None, \"runas\", sys.executable, f'\"{script}\" {params}', None, 1)\n    sys.exit()\n\ndef main():"
        ]
        lines += [f"    subprocess.run(\"{line}\", shell=True, check=True)" for line in create_manager_installer_lines()]
        lines += ["\nif __name__ == \"__main__\":\n    main()"]

    elif fmt == "ps1":
        lines += ["if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] \"Administrator\")) {\n    $script = $MyInvocation.MyCommand.Definition\n    Start-Process powershell -ArgumentList \"-NoProfile -ExecutionPolicy Bypass -File `\"$script`\"\" -Verb RunAs\n    exit\n}\n"]
        lines += create_manager_installer_lines()

    elif fmt == "bat":
        lines += ["net session >nul 2>&1\nif %errorLevel% neq 0 (\n    powershell -Command \"Start-Process '%~f0' -Verb runAs\"\n    exit /b\n)",]
        lines += create_manager_installer_lines()

    else:
        messagebox.showerror("Error", "Unsupported installer format.")
        return

    filename = f"{manager}_installer.{fmt}"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    FILE_LOCATION = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    messagebox.showinfo("Success", f"Installer script generated at {FILE_LOCATION}")

root.after(100, init_app)
root.mainloop()