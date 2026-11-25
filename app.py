
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import csv
import os

# -------------------- SETTINGS --------------------
APP_TITLE = "AquaFlow"
DAILY_GOAL_ML = 2500
WATER_SIZES = [150, 250, 350, 500]
HISTORY_FILE = "water_history.csv"
REMINDER_MINUTES = 60

# -------------------- COLORS --------------------
BG = "#F5F0FF"
CARD = "#FFFFFF"
BLUE = "#9B7AE8"
DARK_BLUE = "#6845B5"
GREEN = "#55A889"
ORANGE = "#D99A55"
RED = "#D96B83"
TEXT = "#352B4A"
MUTED = "#887C9F"
LIGHT_BLUE = "#E9DFFF"
PURPLE = "#8B6AD9"

# -------------------- DATA --------------------
history = []
today_total = 0
water_y = 165
target_water_y = 165
reminder_enabled = False
reminder_job = None

# -------------------- CSV STORAGE --------------------
def ensure_history_file():
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "date", "time", "day", "month",
                "year", "amount_ml", "action"
            ])

def load_history():
    global history
    ensure_history_file()
    history = []

    with open(HISTORY_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            try:
                amount = row.get("amount_ml", "")

                if not amount:
                    amount = int(row.get("glasses", 0)) * 250

                history.append({
                    "date": row.get("date", ""),
                    "time": row.get("time", ""),
                    "day": row.get("day", ""),
                    "month": row.get("month", ""),
                    "year": row.get("year", ""),
                    "amount_ml": int(float(amount)),
                    "action": row.get("action", "Add")
                })

            except (ValueError, TypeError):
                continue

def save_history():
    with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as file:
        fields = [
            "date", "time", "day", "month",
            "year", "amount_ml", "action"
        ]

        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(history)

def record_event(amount, action):
    now = datetime.now()

    history.append({
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%I:%M %p"),
        "day": now.strftime("%A"),
        "month": now.strftime("%B"),
        "year": now.strftime("%Y"),
        "amount_ml": amount,
        "action": action
    })

    save_history()

def get_daily_total(day_string):
    return sum(
        item["amount_ml"]
        for item in history
        if item["date"] == day_string
    )

def get_week_data():
    today = date.today()
    days = []

    for offset in range(6, -1, -1):
        current = today - timedelta(days=offset)

        days.append((
            current,
            max(0, get_daily_total(current.isoformat()))
        ))

    return days

# -------------------- APP WINDOW --------------------
root = tk.Tk()
root.title(APP_TITLE)
root.geometry("1000x820")
root.minsize(850, 700)
root.configure(bg=BG)

style = ttk.Style()

try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure("TNotebook", background=BG, borderwidth=0)
style.configure(
    "TNotebook.Tab",
    font=("Arial", 10, "bold"),
    padding=(16, 9)
)
style.configure("Treeview", font=("Arial", 9), rowheight=27)
style.configure(
    "Treeview.Heading",
    font=("Arial", 9, "bold")
)

# -------------------- HELPERS --------------------
def rounded_button(parent, text, color, command, width=22):
    return tk.Button(
        parent,
        text=text,
        command=command,
        width=width,
        font=("Arial", 11, "bold"),
        bg=color,
        fg="white",
        activebackground=color,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        pady=10
    )

def current_date_label():
    return datetime.now().strftime("%A, %d %B %Y")

# -------------------- WATER FUNCTIONS --------------------
def refresh_totals():
    global today_total, target_water_y

    today_total = max(
        0,
        get_daily_total(date.today().isoformat())
    )

    remaining = max(0, DAILY_GOAL_ML - today_total)
    percent = min(
        100,
        int((today_total / DAILY_GOAL_ML) * 100)
    )

    total_label.config(
        text=f"Total Water: {today_total:,} ml"
    )

    remaining_label.config(
        text=f"Remaining: {remaining:,} ml"
    )

    percent_label.config(text=f"{percent}%")

    circle_amount_label.config(
        text=f"{today_total:,}/{DAILY_GOAL_ML:,} ml"
    )

    if percent >= 100:
        message_label.config(
            text="Amazing! Daily goal completed! 🏆",
            fg=GREEN
        )

    elif percent >= 50:
        message_label.config(
            text="Great progress! Keep it up! 💧",
            fg=BLUE
        )

    else:
        message_label.config(
            text="Every sip counts. Keep going! 💙",
            fg=DARK_BLUE
        )

    target_water_y = int(
        165 - (
            min(today_total, DAILY_GOAL_ML)
            / DAILY_GOAL_ML
        ) * 125
    )

    update_streak_and_badges()
    draw_weekly_chart()
    refresh_history_table()
    update_circle()
    animate_water()

def add_water():
    try:
        amount = int(size_var.get().split()[0])
    except (ValueError, IndexError):
        amount = 250

    record_event(amount, "Add")
    refresh_totals()

def remove_water():
    try:
        amount = int(size_var.get().split()[0])
    except (ValueError, IndexError):
        amount = 250

    if today_total <= 0:
        messagebox.showinfo(
            "Water Tracker",
            "There is no water recorded to remove."
        )
        return

    actual = min(amount, today_total)

    record_event(-actual, "Remove")
    refresh_totals()

def reset_today():
    global history

    answer = messagebox.askyesno(
        "Reset Today",
        "Reset today's water total and today's history entries?"
    )

    if not answer:
        return

    today = date.today().isoformat()

    history = [
        item for item in history
        if item["date"] != today
    ]

    save_history()
    refresh_totals()

# -------------------- STREAKS & BADGES --------------------
def calculate_streak():
    today = date.today()

    today_total_now = get_daily_total(today.isoformat())

    if today_total_now >= DAILY_GOAL_ML:
        cursor = today
    else:
        cursor = today - timedelta(days=1)

    streak = 0

    while get_daily_total(cursor.isoformat()) >= DAILY_GOAL_ML:
        streak += 1
        cursor -= timedelta(days=1)

    return streak

def update_streak_and_badges():
    streak = calculate_streak()

    streak_label.config(
        text=f"🔥 Current Streak: {streak} day{'s' if streak != 1 else ''}"
    )

    total_lifetime = sum(
        max(0, item["amount_ml"])
        for item in history
        if item["action"] == "Add"
    )

    today_complete = today_total >= DAILY_GOAL_ML

    badge_definitions = [
        ("💧 First Sip", "Log your first water intake", total_lifetime > 0),
        ("🎯 Goal Getter", "Complete your daily water goal", today_complete),
        ("🔥 3-Day Streak", "Complete your goal 3 days in a row", streak >= 3),
        ("🏆 7-Day Champion", "Complete your goal 7 days in a row", streak >= 7),
        ("🌊 Hydration Star", "Log 10,000 ml or more in total", total_lifetime >= 10000),
    ]

    for widget in badge_inner.winfo_children():
        widget.destroy()

    earned = 0

    for title, description, unlocked in badge_definitions:

        if unlocked:
            earned += 1

        row = tk.Frame(
            badge_inner,
            bg="#FBF9FF",
            padx=12,
            pady=9
        )

        row.pack(fill="x", pady=4)

        status = "UNLOCKED ✓" if unlocked else "LOCKED"
        status_color = GREEN if unlocked else MUTED

        tk.Label(
            row,
            text=title,
            font=("Arial", 10, "bold"),
            bg="#FBF9FF",
            fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            row,
            text=description,
            font=("Arial", 9),
            bg="#FBF9FF",
            fg=MUTED
        ).pack(anchor="w")

        tk.Label(
            row,
            text=status,
            font=("Arial", 8, "bold"),
            bg="#FBF9FF",
            fg=status_color
        ).pack(anchor="e")

    badge_count_label.config(
        text=f"{earned}/{len(badge_definitions)} badges unlocked"
    )

# -------------------- ANIMATED GLASS --------------------
def draw_glass():
    glass_canvas.delete("all")

    glass_canvas.create_oval(
        38, 10, 162, 36,
        outline="#A88BE3",
        width=3,
        fill="#FBF9FF"
    )

    glass_canvas.create_polygon(
        43, 24, 57, 190, 143, 190, 157, 24,
        outline="#A88BE3",
        fill="#FBF9FF",
        width=3
    )

    glass_canvas.create_line(
        48, 45, 60, 180,
        fill="#FFFFFF",
        width=4
    )

    glass_canvas.create_line(
        152, 45, 140, 180,
        fill="#FFFFFF",
        width=3
    )

    if water_y < 165:
        glass_canvas.create_polygon(
            57, water_y, 143, water_y,
            139, 184, 61, 184,
            fill="#B79AEF",
            outline="#9673DF",
            width=1
        )

        glass_canvas.create_arc(
            57, water_y - 7, 143, water_y + 7,
            start=0,
            extent=180,
            outline="#9673DF",
            width=2
        )

    glass_canvas.create_arc(
        38, 10, 162, 36,
        start=0,
        extent=180,
        style="arc",
        outline="#A88BE3",
        width=3
    )

def animate_water():
    global water_y

    if water_y > target_water_y:
        water_y = max(target_water_y, water_y - 4)
        draw_glass()
        root.after(15, animate_water)

    elif water_y < target_water_y:
        water_y = min(target_water_y, water_y + 4)
        draw_glass()
        root.after(15, animate_water)

    else:
        draw_glass()

# -------------------- WEEKLY CHART --------------------
def draw_weekly_chart():
    chart.delete("all")

    data = get_week_data()

    left, right = 48, 625
    top, bottom = 20, 220

    chart.create_line(
        left, bottom, right, bottom,
        fill="#B9A9D8",
        width=2
    )

    chart.create_line(
        left, top, left, bottom,
        fill="#B9A9D8",
        width=2
    )

    max_value = max(
        DAILY_GOAL_ML,
        max((amount for _, amount in data), default=0)
    )

    scale_max = max_value * 1.15

    for step in range(5):
        value = scale_max * step / 4
        y = bottom - (value / scale_max) * (bottom - top)

        chart.create_line(
            left, y, right, y,
            fill="#EEE8F8",
            dash=(2, 3)
        )

        chart.create_text(
            left - 8, y,
            text=f"{int(value)}",
            anchor="e",
            fill=MUTED,
            font=("Arial", 8)
        )

    slot = (right - left) / 7

    for index, (day_value, amount) in enumerate(data):

        x1 = left + index * slot + 14
        x2 = left + (index + 1) * slot - 14

        bar_height = (
            amount / scale_max
        ) * (bottom - top)

        y1 = bottom - bar_height

        bar_color = GREEN if amount >= DAILY_GOAL_ML else BLUE

        chart.create_rectangle(
            x1, y1, x2, bottom,
            fill=bar_color,
            outline=""
        )

        chart.create_text(
            (x1 + x2) / 2,
            max(top + 8, y1 - 10),
            text=str(amount),
            fill=TEXT,
            font=("Arial", 8, "bold")
        )

        chart.create_text(
            (x1 + x2) / 2,
            bottom + 17,
            text=day_value.strftime("%a"),
            fill=MUTED,
            font=("Arial", 8, "bold")
        )

    goal_y = bottom - (
        DAILY_GOAL_ML / scale_max
    ) * (bottom - top)

    chart.create_line(
        left, goal_y, right, goal_y,
        fill=ORANGE,
        width=2,
        dash=(5, 3)
    )

    chart.create_text(
        right - 2, goal_y - 9,
        text="Daily goal",
        anchor="e",
        fill=ORANGE,
        font=("Arial", 8, "bold")
    )

# -------------------- HISTORY TABLE --------------------
def refresh_history_table():
    for item in history_tree.get_children():
        history_tree.delete(item)

    for item in reversed(history[-200:]):

        amount = item["amount_ml"]

        history_tree.insert(
            "",
            "end",
            values=(
                item["date"],
                item["time"],
                item["action"],
                f"{amount:+,} ml" if amount < 0 else f"+{amount:,} ml"
            )
        )

# -------------------- WATER REMINDER --------------------
def reminder_tick():
    global reminder_job

    if not reminder_enabled:
        return

    messagebox.showinfo(
        "Water Reminder",
        "Time for a water break! 💧"
    )

    reminder_job = root.after(
        REMINDER_MINUTES * 60 * 1000,
        reminder_tick
    )

def toggle_reminder():
    global reminder_enabled, reminder_job

    reminder_enabled = not reminder_enabled

    if reminder_enabled:

        reminder_button.config(
            text="🔔 Reminder: ON",
            bg=GREEN
        )

        messagebox.showinfo(
            "Reminder Enabled",
            f"You'll get a reminder every {REMINDER_MINUTES} minutes while the app is open."
        )

        reminder_job = root.after(
            REMINDER_MINUTES * 60 * 1000,
            reminder_tick
        )

    else:

        reminder_button.config(
            text="🔕 Reminder: OFF",
            bg=PURPLE
        )

        if reminder_job is not None:
            root.after_cancel(reminder_job)
            reminder_job = None

def on_close():
    global reminder_job

    if reminder_job is not None:
        try:
            root.after_cancel(reminder_job)
        except tk.TclError:
            pass

    root.destroy()

# -------------------- HEADER --------------------
header = tk.Frame(root, bg=BG)
header.pack(fill="x", padx=24, pady=(18, 8))

tk.Label(
    header,
    text="AquaFlow",
    font=("Arial", 25, "bold"),
    bg=BG,
    fg=BLUE
).pack()

tk.Label(
    header,
    text="YOUR DAILY HYDRATION COMPANION",
    font=("Arial", 10, "bold"),
    bg=BG,
    fg=MUTED
).pack(pady=(2, 0))

date_label = tk.Label(
    header,
    text=current_date_label(),
    font=("Arial", 9),
    bg=BG,
    fg=MUTED
)

date_label.pack(pady=(5, 0))

# -------------------- NOTEBOOK --------------------
notebook = ttk.Notebook(root)
notebook.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=12
)

dashboard_tab = tk.Frame(notebook, bg=BG)
weekly_tab = tk.Frame(notebook, bg=BG)
badges_tab = tk.Frame(notebook, bg=BG)
history_tab = tk.Frame(notebook, bg=BG)

notebook.add(dashboard_tab, text="Dashboard")
notebook.add(weekly_tab, text="Weekly Progress")
notebook.add(badges_tab, text="Achievements")
notebook.add(history_tab, text="Today's History")

# -------------------- DASHBOARD TAB --------------------
summary_card = tk.Frame(
    dashboard_tab,
    bg=CARD,
    padx=18,
    pady=14,
    highlightthickness=1,
    highlightbackground="#E5D9FA"
)

summary_card.pack(fill="x", padx=10, pady=10)

total_label = tk.Label(
    summary_card,
    text="Total Water: 0 ml",
    font=("Arial", 15, "bold"),
    bg=CARD,
    fg=TEXT
)

total_label.pack(pady=3)

remaining_label = tk.Label(
    summary_card,
    text=f"Remaining: {DAILY_GOAL_ML} ml",
    font=("Arial", 12),
    bg=CARD,
    fg=MUTED
)

remaining_label.pack(pady=3)

message_label = tk.Label(
    summary_card,
    text="Every sip counts. Keep going! 💙",
    font=("Arial", 11, "bold"),
    bg=CARD,
    fg=BLUE
)

message_label.pack(pady=(7, 2))

streak_label = tk.Label(
    summary_card,
    text="🔥 Current Streak: 0 days",
    font=("Arial", 11, "bold"),
    bg=CARD,
    fg=ORANGE
)

streak_label.pack(pady=5)

# -------------------- CIRCULAR PROGRESS --------------------
progress_card = tk.Frame(
    dashboard_tab,
    bg=CARD,
    padx=12,
    pady=12,
    highlightthickness=1,
    highlightbackground="#E5D9FA"
)

progress_card.pack(padx=10, pady=5)

progress_canvas = tk.Canvas(
    progress_card,
    width=190,
    height=190,
    bg=CARD,
    highlightthickness=0
)

progress_canvas.pack()

progress_canvas.create_oval(
    17, 17, 173, 173,
    outline=LIGHT_BLUE,
    width=15
)

progress_arc = progress_canvas.create_arc(
    17, 17, 173, 173,
    start=90,
    extent=0,
    style="arc",
    outline=BLUE,
    width=15
)

percent_label = tk.Label(
    progress_card,
    text="0%",
    font=("Arial", 24, "bold"),
    bg=CARD,
    fg=DARK_BLUE
)

percent_label.place(
    relx=0.5,
    rely=0.43,
    anchor="center"
)

circle_amount_label = tk.Label(
    progress_card,
    text=f"0/{DAILY_GOAL_ML} ml",
    font=("Arial", 9),
    bg=CARD,
    fg=MUTED
)

circle_amount_label.place(
    relx=0.5,
    rely=0.59,
    anchor="center"
)

def update_circle():
    try:
        percent = min(
            100,
            today_total / DAILY_GOAL_ML * 100
        )

        progress_canvas.itemconfig(
            progress_arc,
            extent=-3.6 * percent
        )

    except tk.TclError:
        pass

# -------------------- WATER CONTROLS --------------------
controls = tk.Frame(dashboard_tab, bg=BG)
controls.pack(pady=8)

tk.Label(
    controls,
    text="Select Water Size:",
    font=("Arial", 11, "bold"),
    bg=BG,
    fg=TEXT
).pack(pady=(2, 5))

size_var = tk.StringVar(value="250 ml")

size_box = ttk.Combobox(
    controls,
    textvariable=size_var,
    values=[f"{size} ml" for size in WATER_SIZES],
    state="readonly",
    width=15,
    font=("Arial", 10)
)

size_box.pack(pady=(0, 9))

rounded_button(
    controls,
    "➕  Add Water",
    GREEN,
    add_water,
    25
).pack(pady=4)

rounded_button(
    controls,
    "➖  Remove Water",
    ORANGE,
    remove_water,
    25
).pack(pady=4)

rounded_button(
    controls,
    "↻  Reset Today",
    RED,
    reset_today,
    25
).pack(pady=4)

reminder_button = rounded_button(
    controls,
    "🔕 Reminder: OFF",
    PURPLE,
    toggle_reminder,
    25
)

reminder_button.pack(pady=4)

# -------------------- ANIMATED GLASS --------------------
glass_card = tk.Frame(
    dashboard_tab,
    bg=CARD,
    padx=10,
    pady=8,
    highlightthickness=1,
    highlightbackground="#E5D9FA"
)

glass_card.pack(pady=8)

tk.Label(
    glass_card,
    text="Live Water Glass",
    font=("Arial", 10, "bold"),
    bg=CARD,
    fg=TEXT
).pack()

glass_canvas = tk.Canvas(
    glass_card,
    width=200,
    height=205,
    bg=CARD,
    highlightthickness=0
)

glass_canvas.pack()

# -------------------- WEEKLY TAB --------------------
tk.Label(
    weekly_tab,
    text="Your Last 7 Days",
    font=("Arial", 18, "bold"),
    bg=BG,
    fg=TEXT
).pack(pady=(22, 4))

tk.Label(
    weekly_tab,
    text="Daily water intake in ml (green = goal completed)",
    font=("Arial", 9),
    bg=BG,
    fg=MUTED
).pack(pady=(0, 12))

chart_card = tk.Frame(
    weekly_tab,
    bg=CARD,
    padx=12,
    pady=12
)

chart_card.pack(
    padx=15,
    pady=8,
    fill="x"
)

chart = tk.Canvas(
    chart_card,
    width=650,
    height=255,
    bg=CARD,
    highlightthickness=0
)

chart.pack(fill="x")

tk.Label(
    weekly_tab,
    text=f"Daily target: {DAILY_GOAL_ML:,} ml",
    font=("Arial", 11, "bold"),
    bg=BG,
    fg=GREEN
).pack(pady=12)

# -------------------- ACHIEVEMENTS TAB --------------------
tk.Label(
    badges_tab,
    text="Your Achievements",
    font=("Arial", 18, "bold"),
    bg=BG,
    fg=TEXT
).pack(pady=(20, 5))

badge_count_label = tk.Label(
    badges_tab,
    text="0/5 badges unlocked",
    font=("Arial", 10, "bold"),
    bg=BG,
    fg=BLUE
)

badge_count_label.pack(pady=(0, 12))

badge_outer = tk.Frame(badges_tab, bg=BG)
badge_outer.pack(
    fill="both",
    expand=True,
    padx=25,
    pady=5
)

badge_inner = tk.Frame(badge_outer, bg=BG)
badge_inner.pack(fill="x")

# -------------------- HISTORY TAB --------------------
tk.Label(
    history_tab,
    text="Water History",
    font=("Arial", 17, "bold"),
    bg=BG,
    fg=TEXT
).pack(pady=(20, 12))

table_frame = tk.Frame(history_tab, bg=CARD)

table_frame.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=8
)

columns = ("date", "time", "action", "amount")

history_tree = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)

history_tree.heading("date", text="Date")
history_tree.heading("time", text="Time")
history_tree.heading("action", text="Action")
history_tree.heading("amount", text="Amount")

history_tree.column("date", width=120, anchor="center")
history_tree.column("time", width=110, anchor="center")
history_tree.column("action", width=100, anchor="center")
history_tree.column("amount", width=120, anchor="center")

history_tree.pack(
    fill="both",
    expand=True,
    padx=8,
    pady=8
)

tk.Label(
    history_tab,
    text="Your complete history is saved automatically in water_history.csv",
    font=("Arial", 9),
    bg=BG,
    fg=MUTED
).pack(pady=8)

# -------------------- START APP --------------------
load_history()
refresh_totals()

root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()
