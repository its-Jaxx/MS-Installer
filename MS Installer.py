import tkinter as tk
from tkinter import messagebox, ttk
import os, webbrowser, json, asyncio, aiohttp

exec("try:\n import requests\nexcept ImportError:\n import subprocess, sys\n subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])")
import requests

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
headers = {"User-Agent": "Mozilla/5.0"}

async def fetch_json(session, filename):
    url = base_url + filename
    async with session.get(url) as response:
        response.raise_for_status()
        text = await response.text()
        data = json.loads(text)
        category = next(iter(data))
        return category, data[category]

async def fetch_all():
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [fetch_json(session, filename) for filename in json_files]
        results = await asyncio.gather(*tasks)
        return {category: content for category, content in results}

apps = asyncio.run(fetch_all())

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

root = tk.Tk()
root.title("MS Installer")
root.geometry("1400x800")
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)
root.configure(bg="#1e1e1e")

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

left_frame = tk.Frame(root, bg=BOX_COLOR)
left_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)

def options_btn(btn_text, btn_value, btn_var):
    tk.Radiobutton(left_frame, text=btn_text, variable=btn_var, value=btn_value,
               bg=BOX_COLOR, fg=BTN_TEXT_COLOR, selectcolor=BOX_COLOR, activebackground=BOX_COLOR,
               activeforeground=TEXT_COLOR, highlightthickness=0).pack(anchor="w", padx=30)

tk.Label(left_frame, text="Package Manager", bg=BOX_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).pack(pady=(20, 5), anchor="w", padx=20)
options_btn("Winget", "winget", package_manager); options_btn("Chocolatey", "choco", package_manager)

tk.Label(left_frame, text="Installer Format", bg=BOX_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).pack(pady=(20, 5), anchor="w", padx=20)
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
        populate_apps(selected_only=True)
        show_selected_btn.config(text="Show Full List")
    else:
        populate_apps(search_var.get().lower())
        show_selected_btn.config(text="Show Selected Apps")

def btn_gen(btn_text, btn_cmd, pady=10):
    tk.Button(left_frame, text=btn_text, command=btn_cmd,
          bg=BOX_COLOR, fg=BTN_TEXT_COLOR, activebackground=BUTTON_ACTIVE, activeforeground=TEXT_COLOR,
          relief="flat", highlightthickness=0).pack(pady=(pady, 10), padx=20, fill="x")

btn_gen("Clear Selection", clear_selection, 40)

show_selected_btn = tk.Button(left_frame, text="Show Selected Apps", command=show_selected,
    bg=BOX_COLOR, fg=BTN_TEXT_COLOR, activebackground=BUTTON_ACTIVE, activeforeground=TEXT_COLOR,
    relief="flat", highlightthickness=0)
show_selected_btn.pack(pady=(10, 10), padx=20, fill="x")

btn_gen("Generate Installer", lambda: generate_installer())
btn_gen("About", lambda: about_installer())

right_frame = tk.Frame(root, bg=BOX_COLOR)
right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
right_frame.rowconfigure(2, weight=1)
right_frame.columnconfigure(0, weight=1)

search_frame = tk.Frame(right_frame, bg=BOX_COLOR)
search_frame.grid(row=0, column=0, pady=10, sticky="ew")
search_frame.grid_columnconfigure(0, weight=1)

search_var = tk.StringVar()
search_entry = tk.Entry(
    search_frame, textvariable=search_var, bg="#252526", fg=TEXT_COLOR,
    insertbackground=TEXT_COLOR, relief="flat", font=("Segoe UI", 10), width=40
)
search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

search_icon = tk.Label(
    search_frame, text="\U0001F50D", bg=BOX_COLOR, fg=SEARCH_TEXT_COLOR, font=("Segoe UI", 10)
)
search_icon.grid(row=0, column=1, sticky="w")

canvas_frame = tk.Frame(right_frame, bg=BOX_COLOR)
canvas_frame.grid(row=2, column=0, sticky="nsew")
canvas_frame.rowconfigure(0, weight=1)
canvas_frame.columnconfigure(0, weight=1)

canvas = tk.Canvas(canvas_frame, bg=BOX_COLOR, highlightthickness=0)
scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg=BOX_COLOR)

canvas_back = tk.Canvas(canvas_frame, bg=BOX_COLOR, highlightthickness=0)
scrollable_frame_back = tk.Frame(canvas_back, bg=BOX_COLOR)
canvas_back.create_window((0, 0), window=scrollable_frame_back, anchor="nw")

def _on_scroll(*args):
    canvas.yview(*args)
    canvas_back.yview(*args)

def _on_yscroll(first, last):
    scrollbar.set(first, last)

canvas.configure(yscrollcommand=_on_yscroll)
canvas_back.configure(yscrollcommand=_on_yscroll)
scrollbar.config(command=_on_scroll)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

def _on_mousewheel(event):
    current_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)
canvas.bind_all("<Button-4>", lambda e: current_canvas.yview_scroll(-1, "units"))
canvas.bind_all("<Button-5>", lambda e: current_canvas.yview_scroll(1, "units"))

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.grid(row=0, column=0, sticky="nsew")
canvas_back.grid_forget()
scrollbar.grid(row=0, column=1, sticky="ns")
current_canvas = canvas
current_frame = scrollable_frame

app_buttons, app_widgets = {}, {}
last_columns = 0

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
    populate_apps()
    root.update()

def populate_apps(filter_text="", selected_only=False):
    global last_columns, current_canvas, current_frame

    current_width = canvas_frame.winfo_width()
    if current_width < 100:
        current_width = root.winfo_width() - 200
    available_width = max(300, current_width - 40)
    max_cols = calculate_columns(available_width)
    last_columns = max_cols

    frame_to_draw = scrollable_frame_back if current_frame == scrollable_frame else scrollable_frame
    canvas_to_draw = canvas_back if current_canvas == canvas else canvas

    for widget in frame_to_draw.winfo_children():
        widget.destroy()

    filter_text = filter_text.lower().strip()
    for category, items in apps.items():

        if selected_only:
            filtered_items = {k: v for k, v in items.items() if k in selected_apps}
        else:
            filtered_items = {k: v for k, v in items.items() if filter_text in k.lower()} if filter_text else items

        if not filtered_items:
            continue
        cat_label = tk.Label(frame_to_draw, text=category, bg=BOX_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold"))
        cat_label.pack(anchor="w", pady=(15, 5), padx=10)

        group_frame = tk.Frame(frame_to_draw, bg=BOX_COLOR)
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
                command=lambda name=app_name: toggle_app(name, app_buttons[name])
            )
            btn.grid(row=row, column=col, padx=5, pady=1, sticky="w")
            app_buttons[app_name] = btn
            app_widgets[app_name] = (btn, group_frame, cat_label)
            if "desc" in app_data:
                ToolTip(btn, app_data["desc"])
            col += 1
            if col >= max_cols:
                col = 0; row += 1

    canvas_to_draw.update_idletasks()
    canvas_to_draw.configure(scrollregion=canvas_to_draw.bbox("all"))

    current_canvas.grid_forget()
    canvas_to_draw.grid(row=0, column=0, sticky="nsew")
    current_canvas = canvas_to_draw
    current_frame = frame_to_draw

def update_search(*args):
    populate_apps(search_var.get().lower())

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