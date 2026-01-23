"""AI-Powered Minimalistic Todo App"""

import customtkinter as ctk
import json
import os
import threading
from datetime import datetime
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

load_dotenv()

try:
    from groq import Groq

    GROQ_OK = True
except ImportError:
    GROQ_OK = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
API = os.getenv("GROQ_API_KEY", "")


@dataclass
class Sub:
    title: str
    time: str = "15 min"
    done: bool = False

    def to_dict(self):
        return asdict(self)

    @classmethod
    def of(cls, d):
        return cls(d["title"], d.get("time", "15 min"), d.get("done", False))


@dataclass
class Task:
    title: str
    subs: list = field(default_factory=list)
    pri: str = "Medium"
    tags: list = field(default_factory=list)
    done: bool = False
    col: bool = True
    at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self):
        return {
            **{k: v for k, v in asdict(self).items() if k != "subs"},
            "subs": [s.to_dict() for s in self.subs],
        }

    @classmethod
    def of(cls, d):
        return cls(
            d["title"],
            [Sub.of(s) for s in d.get("subs", [])],
            d.get("pri", "Medium"),
            d.get("tags", []),
            d.get("done", False),
            d.get("col", True),
            d.get("at", ""),
        )


class AI:
    def __init__(self):
        self.c = Groq(api_key=API) if API and GROQ_OK else None

    def gen(self, t, cb):
        if not self.c:
            cb(
                [
                    Sub("Plan", "5 min"),
                    Sub("Execute", "20 min"),
                    Sub("Review", "10 min"),
                ]
            )
            return

        def f():
            try:
                r = self.c.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "user",
                            "content": f'For "{t}", give 2-4 subtasks. Return ONLY: [{{"title":"...","time":"15 min"}}]',
                        }
                    ],
                    temperature=0.7,
                    max_tokens=300,
                )
                x = r.choices[0].message.content.strip()
                if "[" in x:
                    x = x[x.find("[") : x.rfind("]") + 1]
                cb([Sub(s["title"], s.get("time", "15 min")) for s in json.loads(x)])
            except Exception:
                cb(
                    [
                        Sub("Plan", "5 min"),
                        Sub("Execute", "20 min"),
                        Sub("Review", "10 min"),
                    ]
                )

        threading.Thread(target=f, daemon=True).start()

    def pri(self, t):
        t = t.lower()
        return (
            "High"
            if any(k in t for k in ["urgent", "asap", "deadline", "meeting"])
            else "Low"
            if any(k in t for k in ["someday", "maybe"])
            else "Medium"
        )

    def tags(self, t):
        t, r = t.lower(), []
        if any(k in t for k in ["meeting", "report", "work"]):
            r.append("Work")
        if any(k in t for k in ["gym", "doctor", "family"]):
            r.append("Personal")
        if any(k in t for k in ["buy", "grocery", "shop"]):
            r.append("Errands")
        return r or ["General"]


class Undo:
    def __init__(self):
        self.h = []

    def add(self, d):
        self.h.append(d)

    def pop(self):
        return self.h.pop() if self.h else None

    def ok(self):
        return bool(self.h)


class SubW(ctk.CTkFrame):
    def __init__(self, m, sub, chg, dl):
        super().__init__(m, fg_color="transparent")
        self.sub, self.chg, self.ed = sub, chg, False
        self.grid_columnconfigure(1, weight=1)
        self.cb = ctk.CTkCheckBox(
            self,
            text="",
            width=24,
            command=self._t,
            checkbox_width=18,
            checkbox_height=18,
        )
        self.cb.grid(row=0, column=0, padx=(25, 5), pady=3)
        self.l = ctk.CTkLabel(
            self, text=sub.title, font=ctk.CTkFont(size=12), anchor="w", cursor="hand2"
        )
        self.l.grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        self.l.bind("<Double-1>", self._et)
        self.tm = ctk.CTkLabel(
            self,
            text=sub.time,
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray50"),
            width=60,
            cursor="hand2",
        )
        self.tm.grid(row=0, column=2, padx=5, pady=3)
        self.tm.bind("<Double-1>", self._em)
        ctk.CTkButton(
            self,
            text="×",
            width=20,
            height=20,
            fg_color="transparent",
            hover_color=("gray75", "gray30"),
            text_color=("gray30", "gray60"),
            command=lambda: dl(sub),
        ).grid(row=0, column=3, padx=(0, 5), pady=3)
        self._u()

    def _t(self):
        self.sub.done = not self.sub.done
        self._u()
        self.chg()

    def _u(self):
        (self.cb.select if self.sub.done else self.cb.deselect)()
        self.l.configure(
            text_color=("gray50", "gray55") if self.sub.done else ("gray20", "gray80"),
            font=ctk.CTkFont(size=12, overstrike=self.sub.done),
        )

    def _et(self, _=None):
        if self.ed:
            return
        self.ed = True
        self.l.grid_forget()
        self.e = ctk.CTkEntry(self, font=ctk.CTkFont(size=12), height=24)
        self.e.insert(0, self.sub.title)
        self.e.grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        self.e.focus()
        self.e.bind("<Return>", self._st)
        self.e.bind("<FocusOut>", self._st)

    def _st(self, _=None):
        if not self.ed:
            return
        n = self.e.get().strip()
        if n:
            self.sub.title = n
            self.l.configure(text=n)
        self.e.destroy()
        self.l.grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        self.ed = False
        self.chg()

    def _em(self, _=None):
        if self.ed:
            return
        self.ed = True
        self.tm.grid_forget()
        self.te = ctk.CTkEntry(self, font=ctk.CTkFont(size=11), width=60, height=24)
        self.te.insert(0, self.sub.time)
        self.te.grid(row=0, column=2, padx=5, pady=3)
        self.te.focus()
        self.te.bind("<Return>", self._sm)
        self.te.bind("<FocusOut>", self._sm)

    def _sm(self, _=None):
        if not self.ed:
            return
        n = self.te.get().strip()
        if n:
            self.sub.time = n
            self.tm.configure(text=n)
        self.te.destroy()
        self.tm.grid(row=0, column=2, padx=5, pady=3)
        self.ed = False
        self.chg()


class TaskW(ctk.CTkFrame):
    def __init__(self, m, task, cbs, dcbs=None):
        super().__init__(m, fg_color=("gray90", "gray17"), corner_radius=12)
        self.task, self.cbs, self.dcbs = task, cbs, dcbs or {}
        self.grid_columnconfigure(3, weight=1)
        ctk.CTkLabel(
            self,
            text="●",
            font=ctk.CTkFont(size=10),
            text_color={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}.get(
                task.pri, "#888"
            ),
        ).grid(row=0, column=0, padx=(12, 0), pady=12)
        self.exp = ctk.CTkButton(
            self,
            text="▶" if task.col else "▼",
            width=24,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            hover_color=("gray80", "gray25"),
            text_color=("gray30", "gray60"),
            command=self._c,
        )
        self.exp.grid(row=0, column=1, padx=5, pady=12)
        self.chk = ctk.CTkCheckBox(
            self,
            text="",
            width=24,
            command=self._t,
            checkbox_width=20,
            checkbox_height=20,
        )
        self.chk.grid(row=0, column=2, padx=(0, 5), pady=12, sticky="w")
        self.ttl = ctk.CTkLabel(
            self, text=task.title, font=ctk.CTkFont(size=14), anchor="w"
        )
        self.ttl.grid(row=0, column=3, padx=5, pady=12, sticky="ew")
        ctk.CTkLabel(
            self,
            text=" ".join(f"#{t}" for t in task.tags[:2]),
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60"),
        ).grid(row=0, column=4, padx=5, pady=12)
        self.cnt = ctk.CTkLabel(
            self,
            text=f"({len(task.subs)})" if task.subs else "",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        )
        self.cnt.grid(row=0, column=5, padx=5, pady=12)
        ctk.CTkButton(
            self,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=("gray75", "gray30"),
            text_color=("gray30", "gray60"),
            command=lambda: cbs["del"](task),
        ).grid(row=0, column=6, padx=(5, 12), pady=12)
        self.sf = ctk.CTkFrame(self, fg_color="transparent")
        self._rs()
        if not task.col:
            self._s()
        self._u()
        for w in [self, self.ttl]:
            w.bind(
                "<ButtonPress-1>",
                lambda e: self.dcbs.get("s", lambda *a: None)(e, self),
            )
            w.bind(
                "<B1-Motion>", lambda e: self.dcbs.get("m", lambda *a: None)(e, self)
            )
            w.bind(
                "<ButtonRelease-1>",
                lambda e: self.dcbs.get("e", lambda *a: None)(e, self),
            )

    def _c(self):
        self.task.col = not self.task.col
        self.exp.configure(text="▶" if self.task.col else "▼")
        self.sf.grid_forget() if self.task.col else self._s()
        self.cbs["chg"]()

    def _s(self):
        self.sf.grid(row=1, column=0, columnspan=7, sticky="ew", padx=10, pady=(0, 10))

    def _rs(self):
        for w in self.sf.winfo_children():
            w.destroy()
        for s in self.task.subs:
            SubW(self.sf, s, self.cbs["chg"], self._ds).pack(fill="x", pady=1)
        ctk.CTkButton(
            self.sf,
            text="+ Add subtask",
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=("gray80", "gray25"),
            text_color=("gray30", "gray60"),
            anchor="w",
            command=self._a,
        ).pack(fill="x", padx=25, pady=(5, 0))

    def _a(self):
        self.task.subs.append(Sub("New subtask", "15 min"))
        self._rs()
        self.cnt.configure(text=f"({len(self.task.subs)})")
        self.cbs["chg"]()

    def _ds(self, s):
        self.task.subs.remove(s)
        self._rs()
        self.cnt.configure(text=f"({len(self.task.subs)})" if self.task.subs else "")
        self.cbs["chg"]()

    def _t(self):
        self.task.done = not self.task.done
        self._u()
        self.cbs["tog"]()

    def _u(self):
        (self.chk.select if self.task.done else self.chk.deselect)()
        self.ttl.configure(
            text_color=("gray50", "gray55") if self.task.done else ("gray10", "gray90"),
            font=ctk.CTkFont(size=14, overstrike=self.task.done),
        )


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("✨ Smart Todo")
        self.geometry("700x800")
        self.minsize(550, 600)
        self.tasks, self.fm, self.sq, self.hist, self.hi = [], "all", "", [], -1
        self.undo, self.ai, self.drag = Undo(), AI(), None
        self._ld()
        self._ui()
        self._rf()
        self.bind("<Control-Return>", lambda _: self._add())
        self.bind("<Control-z>", lambda _: self._ud())
        self.bind("<Control-f>", lambda _: self.se.focus())
        self.bind("<Escape>", lambda _: self._clr())
        self.protocol("WM_DELETE_WINDOW", self._ex)

    def _ld(self):
        if os.path.exists("tasks.json"):
            try:
                with open("tasks.json") as f:
                    d = json.load(f)
                    self.tasks = [Task.of(t) for t in d.get("tasks", [])]
                    ctk.set_appearance_mode(d.get("theme", "dark"))
            except Exception:
                pass

    def _sv(self):
        with open("tasks.json", "w") as f:
            json.dump(
                {
                    "tasks": [t.to_dict() for t in self.tasks],
                    "theme": ctk.get_appearance_mode(),
                },
                f,
                indent=2,
            )

    def _ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        h = ctk.CTkFrame(self, fg_color="transparent")
        h.grid(row=0, column=0, padx=24, pady=(24, 12), sticky="ew")
        h.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            h, text="✨ Smart Todo", font=ctk.CTkFont(size=28, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        self.thm = ctk.CTkSwitch(h, text="", width=50, command=self._tm)
        self.thm.grid(row=0, column=2, padx=10)
        if ctk.get_appearance_mode().lower() == "light":
            self.thm.select()
        ctk.CTkButton(
            h,
            text="📤",
            width=36,
            height=36,
            corner_radius=18,
            font=ctk.CTkFont(size=16),
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray25"),
            text_color=("gray20", "gray90"),
            command=self._exp,
        ).grid(row=0, column=3, padx=2)
        ctk.CTkButton(
            h,
            text="📥",
            width=36,
            height=36,
            corner_radius=18,
            font=ctk.CTkFont(size=16),
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray25"),
            text_color=("gray20", "gray90"),
            command=self._imp,
        ).grid(row=0, column=4, padx=2)
        self.st = ctk.CTkLabel(
            h, text="", font=ctk.CTkFont(size=12), text_color=("gray40", "gray60")
        )
        self.st.grid(row=1, column=0, columnspan=5, sticky="w", pady=(8, 0))
        self.se = ctk.CTkEntry(
            self,
            placeholder_text="🔍 Search...",
            height=38,
            font=ctk.CTkFont(size=13),
            border_width=1,
        )
        self.se.grid(row=1, column=0, padx=24, pady=8, sticky="ew")
        self.se.bind("<KeyRelease>", lambda _: self._sch())
        i = ctk.CTkFrame(self, fg_color="transparent")
        i.grid(row=2, column=0, padx=24, pady=8, sticky="ew")
        i.grid_columnconfigure(0, weight=1)
        self.en = ctk.CTkEntry(
            i,
            placeholder_text="Add task... (Ctrl+Enter)",
            height=44,
            font=ctk.CTkFont(size=14),
            border_width=2,
        )
        self.en.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.en.bind("<Return>", lambda _: self._add())
        self.en.bind("<Up>", self._rc)
        ctk.CTkButton(
            i,
            text="Add",
            width=70,
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._add,
        ).grid(row=0, column=1)
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=3, column=0, padx=24, pady=(0, 8), sticky="ew")
        self.fb = {}
        for j, (m, lb) in enumerate(
            [("all", "All"), ("pending", "Pending"), ("completed", "Completed")]
        ):
            b = ctk.CTkButton(
                f,
                text=lb,
                width=80,
                height=30,
                font=ctk.CTkFont(size=12),
                fg_color=("#3b82f6", "gray30") if m == "all" else ("gray85", "gray25"),
                text_color=("white", "gray90") if m == "all" else ("gray30", "gray70"),
                border_width=0 if m == "all" else 1,
                border_color=("gray60", "gray50"),
                command=lambda m=m: self._fl(m),
            )
            b.grid(row=0, column=j, padx=(0, 5))
            self.fb[m] = b
        self.ls = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.ls.grid(row=4, column=0, padx=24, pady=(0, 16), sticky="nsew")
        self.ls.grid_columnconfigure(0, weight=1)
        self.ub = ctk.CTkButton(
            self,
            text="↩ Undo",
            width=80,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=("gray80", "gray25"),
            hover_color=("gray70", "gray35"),
            text_color=("gray40", "gray60"),
            command=self._ud,
        )
        self.ub.place(relx=1, rely=1, x=-30, y=-20, anchor="se")
        self._uub()

    def _add(self):
        t = self.en.get().strip()
        if not t:
            return
        task = Task(t, pri=self.ai.pri(t), tags=self.ai.tags(t))
        self.hist.append(t)
        self.hi = -1
        self.ai.gen(t, lambda s: self._os(task, s))
        self.tasks.insert(0, task)
        self.en.delete(0, "end")
        self._sv()
        self._rf()

    def _os(self, task, s):
        task.subs = s
        self._sv()
        self.after(0, self._rf)

    def _rc(self, _=None):
        if not self.hist:
            return
        self.hi = (self.hi + 1) % len(self.hist)
        self.en.delete(0, "end")
        self.en.insert(0, self.hist[-(self.hi + 1)])

    def _dl(self, task):
        self.undo.add({"t": task.to_dict(), "i": self.tasks.index(task)})
        self.tasks.remove(task)
        self._sv()
        self._rf()
        self._uub()

    def _fl(self, m):
        self.fm = m
        for k, b in self.fb.items():
            b.configure(
                fg_color=("#3b82f6", "gray30") if k == m else ("gray85", "gray25"),
                text_color=("white", "gray90") if k == m else ("gray30", "gray70"),
                border_width=0 if k == m else 1,
            )
        self._rf()

    def _sch(self):
        self.sq = self.se.get().strip().lower()
        self._rf()

    def _clr(self):
        self.se.delete(0, "end")
        self.sq = ""
        self._rf()

    def _flt(self):
        ts = self.tasks
        if self.fm == "pending":
            ts = [t for t in ts if not t.done]
        elif self.fm == "completed":
            ts = [t for t in ts if t.done]
        if self.sq:
            ts = [
                t
                for t in ts
                if self.sq in t.title.lower()
                or any(self.sq in s.title.lower() for s in t.subs)
            ]
        return ts

    def _rf(self):
        for w in self.ls.winfo_children():
            w.destroy()
        for j, t in enumerate(self._flt()):
            TaskW(
                self.ls,
                t,
                {
                    "tog": lambda: (self._sv(), self._us()),
                    "del": self._dl,
                    "chg": self._sv,
                },
                {"s": self._ds, "m": self._dm, "e": self._de},
            ).grid(row=j, column=0, pady=4, sticky="ew")
        if not self._flt():
            ctk.CTkLabel(
                self.ls,
                text="Add your first task ✨" if not self.sq else "No matches",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray60"),
            ).grid(row=0, column=0, pady=50)
        self._us()

    def _us(self):
        t, d = len(self.tasks), sum(1 for x in self.tasks if x.done)
        self.st.configure(text=f"{t} tasks • {t - d} pending • {d} done")

    def _tm(self):
        ctk.set_appearance_mode("light" if self.thm.get() else "dark")
        self._sv()

    def _ud(self, _=None):
        if not self.undo.ok():
            return
        s = self.undo.pop()
        if s:
            self.tasks.insert(min(s["i"], len(self.tasks)), Task.of(s["t"]))
            self._sv()
            self._rf()
        self._uub()

    def _uub(self):
        self.ub.configure(
            state="normal" if self.undo.ok() else "disabled",
            fg_color=("gray80", "gray25") if self.undo.ok() else ("gray90", "gray20"),
        )

    def _ds(self, e, w):
        self.drag = w

    def _dm(self, e, w):
        pass

    def _de(self, e, w):
        if not self.drag:
            return
        for j, c in enumerate(self.ls.winfo_children()):
            if (
                isinstance(c, TaskW)
                and c.winfo_rooty() <= e.y_root <= c.winfo_rooty() + c.winfo_height()
            ):
                t = self.drag.task
                if t in self.tasks:
                    o = self.tasks.index(t)
                    self.tasks.remove(t)
                    self.tasks.insert(min(j, len(self.tasks)), t)
                if o != j:
                    self._sv()
                    self._rf()
                break
        self.drag = None

    def _exp(self):
        from tkinter import filedialog

        p = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")]
        )
        if p:
            with open(p, "w") as f:
                json.dump({"tasks": [t.to_dict() for t in self.tasks]}, f, indent=2)

    def _imp(self):
        from tkinter import filedialog

        p = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if p:
            try:
                with open(p) as f:
                    self.tasks.extend(
                        [Task.of(t) for t in json.load(f).get("tasks", [])]
                    )
                    self._sv()
                    self._rf()
            except Exception:
                pass

    def _ex(self):
        self._sv()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
