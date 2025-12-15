import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
import tkintermapview
import requests
import threading
import time

import sys
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetDllDirectoryW(None)

class AutobahnApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Autobahn Cockpit Ultimate (Cached)")
        self.root.geometry("1500x950")
        
        self.BASE_URL = "https://verkehr.autobahn.de/o/autobahn"
        
        # --- EINSTELLUNGEN & CACHE ---
        self.refresh_interval_min = 5  # Standard: 5 Minuten
        self.last_refresh_time = 0
        self.data_cache = {} # Format: { "A1": { "timestamp": 12345, "data": {...} } }
        self.current_road_id = None
        
        # Datenspeicher (Aktuelle Ansicht)
        self.current_data = {
            "warning": [], "closure": [], "roadworks": [], 
            "charging": [], "webcam": [], "parking": []
        }
        
        self.map_filters = {
            "warning":   tk.IntVar(value=1), "closure":   tk.IntVar(value=1),
            "roadworks": tk.IntVar(value=1), "charging":  tk.IntVar(value=1),
            "webcam":    tk.IntVar(value=1), "parking":   tk.IntVar(value=1)
        }
        self.feed_filters = {"warning": tk.IntVar(value=1), "closure": tk.IntVar(value=1)}
        self.legend_widgets = {}
        self.feed_map = {}

        # --- LAYOUT ---
        self.main_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashwidth=5, bg="#d9d9d9")
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.main_pane, width=340); self.main_pane.add(self.left_frame, minsize=320)
        self.center_frame = ttk.Frame(self.main_pane, width=800); self.main_pane.add(self.center_frame, minsize=400, stretch="always")
        self.right_frame = ttk.Frame(self.main_pane, width=350); self.main_pane.add(self.right_frame, minsize=300)

        # === LINKS ===
        pad = ttk.Frame(self.left_frame, padding="10")
        pad.pack(fill=tk.BOTH, expand=True)

        # Header Zeile: Label + Settings Button
        head_frame = ttk.Frame(pad)
        head_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(head_frame, text="Autobahn:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        # Settings Button (⚙️)
        ttk.Button(head_frame, text="⚙️", width=3, command=self.open_settings).pack(side=tk.RIGHT)

        self.combo = ttk.Combobox(pad, state="readonly")
        self.combo.pack(fill=tk.X, pady=(0, 10))
        self.combo.bind("<<ComboboxSelected>>", self.on_autobahn_selected)

        # Layer
        grp = ttk.LabelFrame(pad, text="Karten-Layer", padding="5")
        grp.pack(fill=tk.X, pady=5)
        self.create_map_toggle(grp, "warning", "Warnungen", "orange")
        self.create_map_toggle(grp, "closure", "Sperrungen", "black")
        self.create_map_toggle(grp, "roadworks", "Baustellen", "red")
        ttk.Separator(grp, orient="horizontal").pack(fill="x", pady=4)
        self.create_map_toggle(grp, "charging", "Laden", "green")
        self.create_map_toggle(grp, "parking", "Parken", "purple")
        self.create_map_toggle(grp, "webcam", "Cams", "blue")

        # Feed
        ttk.Label(pad, text="Meldungs-Ticker:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 2))
        ff = ttk.Frame(pad); ff.pack(fill=tk.X, pady=(0, 5))
        ttk.Checkbutton(ff, text="⚠️ Meldungen", variable=self.feed_filters["warning"], style="Toolbutton", command=self.refresh_feed_list).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Checkbutton(ff, text="⛔ Sperrungen", variable=self.feed_filters["closure"], style="Toolbutton", command=self.refresh_feed_list).pack(side=tk.LEFT, fill=tk.X, expand=True)

        fc = ttk.Frame(pad); fc.pack(fill=tk.BOTH, expand=True)
        self.feed_tree = ttk.Treeview(fc, columns=("icon", "msg"), show="headings", selectmode="browse", height=15)
        self.feed_tree.heading("icon", text="Typ"); self.feed_tree.column("icon", width=35, anchor="center")
        self.feed_tree.heading("msg", text="Inhalt"); self.feed_tree.column("msg", width=200)
        sb = ttk.Scrollbar(fc, orient="vertical", command=self.feed_tree.yview); self.feed_tree.configure(yscrollcommand=sb.set)
        self.feed_tree.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        self.feed_tree.bind("<<TreeviewSelect>>", self.on_feed_click)

        self.status = tk.StringVar(value="Startklar")
        ttk.Label(pad, textvariable=self.status, relief=tk.SUNKEN, anchor="w", font=("Segoe UI", 8)).pack(side=tk.BOTTOM, fill=tk.X)

        # === MITTE ===
        mc = ttk.Frame(self.center_frame); mc.pack(fill=tk.BOTH, expand=True)
        self.map = tkintermapview.TkinterMapView(mc, corner_radius=0); self.map.pack(fill=tk.BOTH, expand=True)
        self.map.set_position(51.16, 10.45); self.map.set_zoom(6)
        
        # Map Mode Overlay
        self.mode_frame = tk.Frame(self.map, bg="white", padx=5, pady=5)
        self.mode_frame.place(relx=0.97, rely=0.02, anchor="ne")
        tk.Button(self.mode_frame, text="Karte", command=lambda: self.set_map_mode("topo"), bg="#e0e0e0", relief="flat").pack(side="left", padx=2)
        tk.Button(self.mode_frame, text="Satellit", command=lambda: self.set_map_mode("sat"), bg="#e0e0e0", relief="flat").pack(side="left", padx=2)

        # === RECHTS ===
        self.detail_frame = ttk.Frame(self.right_frame, padding="15"); self.detail_frame.pack(fill=tk.BOTH, expand=True)
        self.clear_details()

        # Start
        self.load_roads()
        self.start_auto_refresh_loop()

    # --- SETTINGS & CACHE LOGIC ---
    def open_settings(self):
        top = Toplevel(self.root)
        top.title("Einstellungen")
        top.geometry("300x150")
        
        ttk.Label(top, text="Aktualisierungs-Intervall (Minuten):").pack(pady=10)
        
        spin = ttk.Spinbox(top, from_=1, to=60, width=5)
        spin.set(self.refresh_interval_min)
        spin.pack(pady=5)
        
        def save():
            try:
                val = int(spin.get())
                self.refresh_interval_min = val
                messagebox.showinfo("Gespeichert", f"Intervall auf {val} Minuten gesetzt.")
                top.destroy()
                # Sofort prüfen, ob Update nötig
                self.check_update_needed() 
            except ValueError:
                messagebox.showerror("Fehler", "Bitte eine ganze Zahl eingeben.")

        ttk.Button(top, text="Speichern", command=save).pack(pady=10)

    def start_auto_refresh_loop(self):
        """Prüft alle 30 Sekunden, ob die Daten veraltet sind"""
        self.check_update_needed()
        # Loop: Ruft sich selbst alle 30s auf
        self.root.after(30000, self.start_auto_refresh_loop)

    def check_update_needed(self):
        """Prüft Cache-Alter und lädt neu falls nötig"""
        if not self.current_road_id: return
        
        # Cache prüfen
        if self.current_road_id in self.data_cache:
            cache_entry = self.data_cache[self.current_road_id]
            age_min = (time.time() - cache_entry["timestamp"]) / 60
            
            if age_min >= self.refresh_interval_min:
                self.status.set(f"Auto-Update für {self.current_road_id}...")
                self.load_data(self.current_road_id, force_refresh=True)

    # --- DATA LOADING ---
    def on_autobahn_selected(self, e):
        rid = self.combo.get()
        if rid: self.load_data(rid)

    def load_data(self, rid, force_refresh=False):
        self.current_road_id = rid
        
        # 1. CACHE PRÜFEN (wenn nicht forced)
        if not force_refresh and rid in self.data_cache:
            cache_entry = self.data_cache[rid]
            age_min = (time.time() - cache_entry["timestamp"]) / 60
            
            # Wenn Cache frisch genug (jünger als Intervall)
            if age_min < self.refresh_interval_min:
                self.status.set(f"Lade {rid} aus Cache ({int(age_min)} min alt)...")
                self._on_loaded(cache_entry["data"], from_cache=True)
                return

        # 2. NETZWERK ABRUF
        self.map.delete_all_marker(); self.clear_details()
        self.feed_tree.delete(*self.feed_tree.get_children())
        self.status.set(f"Lade {rid} vom Server...")
        
        def fetch():
            d = {}
            for ep, k in [("warning","warning"), ("closure","closure"), ("roadworks","roadworks"), 
                          ("electric_charging_station","charging"), ("parking_lorry","parking"), ("webcam","webcam")]:
                try: 
                    ak = ep if ep not in ["electric_charging_station", "parking_lorry"] else ep
                    r = requests.get(f"{self.BASE_URL}/{rid}/services/{ep}")
                    d[k] = r.json().get(ak, []) if r.ok else []
                except: d[k] = []
            self.root.after(0, lambda: self._on_loaded_network(rid, d))
        
        threading.Thread(target=fetch, daemon=True).start()

    def _on_loaded_network(self, rid, data):
        # Cache aktualisieren
        self.data_cache[rid] = {
            "timestamp": time.time(),
            "data": data
        }
        self._on_loaded(data, from_cache=False)

    def _on_loaded(self, data, from_cache=False):
        self.current_data = data
        
        # GUI Updates
        for k, var in self.legend_widgets.items():
            var.set(f"{var.get().split('(')[0].strip()} ({len(data.get(k, []))})")
            
        self.refresh_feed_list()
        self.redraw_map()
        
        src = "Cache" if from_cache else "Live"
        self.status.set(f"Daten geladen ({src}). Nächstes Update in {self.refresh_interval_min} min.")

    # --- STANDARD FUNKTIONEN (Map, Feed, etc.) ---
    def set_map_mode(self, mode):
        if mode == "topo":
            self.map.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
        elif mode == "sat":
            self.map.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)

    def create_map_toggle(self, parent, key, txt, col):
        f = ttk.Frame(parent); f.pack(fill=tk.X, pady=1)
        c = tk.Canvas(f, width=14, height=14, highlightthickness=0); c.pack(side=tk.LEFT, padx=5)
        c.create_oval(2,2,12,12, fill=col, outline=col)
        self.legend_widgets[key] = tk.StringVar(value=txt)
        ttk.Checkbutton(f, textvariable=self.legend_widgets[key], variable=self.map_filters[key], style="Toolbutton", command=self.redraw_map).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def load_roads(self):
        threading.Thread(target=lambda: self.root.after(0, lambda: self._upd_combo(requests.get(self.BASE_URL).json().get("roads", []))), daemon=True).start()

    def _upd_combo(self, roads):
        self.combo['values'] = roads
        if roads: self.combo.set(roads[0]); self.on_autobahn_selected(None)

    def refresh_feed_list(self):
        self.feed_tree.delete(*self.feed_tree.get_children()); self.feed_map.clear()
        its = []
        if self.feed_filters["warning"].get():
            for w in self.current_data.get("warning", []): its.append({"type":"warn","data":w,"icon":"⚠️","key":"warning"})
        if self.feed_filters["closure"].get():
            for c in self.current_data.get("closure", []): its.append({"type":"close","data":c,"icon":"⛔","key":"closure"})
        for i in its:
            idx = self.feed_tree.insert("", "end", values=(i["icon"], i["data"].get("title") or i["data"].get("subtitle") or "Info"))
            self.feed_map[idx] = i

    def on_feed_click(self, e):
        s = self.feed_tree.selection()
        if s:
            i = self.feed_map.get(s[0])
            if i:
                self.show_details(i["key"], i["data"])
                p = self.get_coords(i["data"])
                if p: self.map.set_position(p[0], p[1]); self.map.set_zoom(12)

    def get_coords(self, i):
        try:
            if 'coordinate' in i: return float(i['coordinate']['lat']), float(i['coordinate']['long'])
            if 'geometry' in i: return float(i['geometry']['coordinates'][1]), float(i['geometry']['coordinates'][0])
        except: pass
        return None

    def redraw_map(self):
        self.map.delete_all_marker(); b = []
        def add(k, i, c1, c2):
            if self.map_filters[k].get():
                for x in self.current_data.get(k, []):
                    p = self.get_coords(x)
                    if p:
                        self.map.set_marker(p[0], p[1], text=i, marker_color_circle=c1, marker_color_outside=c2, command=lambda m, d=x, t=k: self.show_details(t, d))
                        b.append(p)
        add("parking","P","purple","#4a0072"); add("webcam","📷","blue","darkblue"); add("charging","⚡","green","darkgreen")
        add("roadworks","🚧","red","darkred"); add("closure","⛔","black","#333333"); add("warning","⚠️","orange","#cc8400")
        if b: self.map.fit_bounding_box((max(x[0] for x in b), min(x[1] for x in b)), (min(x[0] for x in b), max(x[1] for x in b)))

    def clear_details(self):
        for w in self.detail_frame.winfo_children(): w.destroy()
        ttk.Label(self.detail_frame, text="Details", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0,20))
        ttk.Label(self.detail_frame, text="Bitte Element wählen", foreground="gray").pack()

    def show_details(self, key, item):
        for w in self.detail_frame.winfo_children(): w.destroy()
        t_map = {"warning":"Meldung","closure":"Sperrung","roadworks":"Bau","charging":"Laden","parking":"Rast","webcam":"Cam"}
        ttk.Label(self.detail_frame, text=t_map.get(key, key).upper(), foreground="gray", font=("Segoe UI", 8)).pack(anchor="w")
        ttk.Label(self.detail_frame, text=item.get("title") or item.get("subtitle") or "-", font=("Segoe UI", 11, "bold"), wraplength=300).pack(anchor="w", pady=(0,10))
        ttk.Separator(self.detail_frame, orient="horizontal").pack(fill="x", pady=5)
        tf = ttk.Frame(self.detail_frame); tf.pack(fill="both", expand=True)
        txt = tk.Text(tf, wrap="word", bg="#f4f4f4", relief="flat", padx=5, pady=5)
        scr = ttk.Scrollbar(tf, orient="vertical", command=txt.yview); txt.configure(yscrollcommand=scr.set)
        txt.pack(side="left", fill="both", expand=True); scr.pack(side="right", fill="y")
        l = []
        if "identifier" in item: l.append(f"ID: {item['identifier']}")
        if "startTimestamp" in item: l.append(f"Start: {item['startTimestamp']}")
        if "description" in item: l.append("\n" + ("\n".join(item["description"]) if isinstance(item["description"], list) else str(item["description"])))
        txt.insert("1.0", "\n".join(l)); txt.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    try: from ctypes import windll; windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    AutobahnApp(root)
    root.mainloop()
