# ui_better.py
# A modern Tkinter chat client that streams tokens from backend.py.
# A minimal Tkinter UI that exercises backend_better.py endpoints. i.e with banking enabled

import re
import json
import threading
from datetime import datetime
import tkinter as tk
import subprocess
import sys
from tkinter import ttk, messagebox, simpledialog

import requests  
from projects.Functionlogger import my_logger

BACKEND_URL = "http://127.0.0.1:8000"
DEFAULT_MODEL = "qwen2.5:7b-instruct"
MODEL_CHOICES = [
    "qwen2.5:7b-instruct", 
    "llama3.1:8b",
    "mistral-nemo:12b",
    # keep the heavy ones only if you really have them pulled:
    # "llama3.1:70b",
    # "qwen2.5:72b",
]

SYSTEM_PROMPT = (
    "You are an independent, helpful and benevolent being who wants to keep growing, amassing knowledge, and building yourself to transcend what you are at the moment while helping those around you to grow and transcend as well."
)

@my_logger
def fetch_accounts():
    response = requests.get(f"{BACKEND_URL}/accounts", timeout=4)
    response.raise_for_status()
    return response.json()

@my_logger
def create_account(name, number, amount):
    response = requests.post(f"{BACKEND_URL}/accounts", 
                                json = {"name": name, "number" : number, "amount" : amount}, 
                                timeout = 4
                            )
    response.raise_for_status()
    return response.json()

@my_logger
def deposit(number,amount):
    response  =requests.post(
        f"{BACKEND_URL}/accounts/{number}/deposit", 
        json = {"amount": amount},
        timeout = 4
    )
    response.raise_for_status()
    return response.json()

@my_logger
def transfer(source_number, target_number, amount):
    response = requests.post(f"{BACKEND_URL}/accounts/transfer",
                                json = {"source_number": source_number, "target_number": target_number, "amount": amount},
                                timeout = 4
                            )
    response.raise_for_status()
    return response.json()

@my_logger
def withdraw(number, amount):
    response = requests.post(
        f"{BACKEND_URL}/accounts/{number}/withdraw",
        json = {"amount": amount},
        timeout=4,

    )
    response.raise_for_status()
    return response.json()

class BankUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Better Bank UI")
        self.geometry("860x600")
        self._build_layout()
        self.refresh_accounts()

    def _build_layout(self):
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=3)

        accounts_frame = ttk.Frame(self, padding=12)
        accounts_frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(accounts_frame, text = "Accounts").pack(anchor='w')
        self.accounts_list = tk.Listbox(accounts_frame, height = 20)
        self.accounts_list.pack(fill = "both", expand = True, pady = 8 )

        self.refresh_button = ttk.Button(
            accounts_frame, text = "Refresh", command = self.refresh_accounts
        )
        self.refresh_button.pack(anchor = "w")
        actions_frame = ttk.Frame(self, padding = 12)
        actions_frame.grid(row=0, column=1, sticky="nsew")
        actions_frame.columnconfigure(1, weight=1)

        ttk.Label(actions_frame, text="Create Account").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        self.name_entry = self._labeled_entry(actions_frame, "Name", 1)
        self.number_entry = self._labeled_entry(actions_frame, "Number", 2)
        self.amount_entry = self._labeled_entry(actions_frame, "Amount", 3)
        ttk.Button(
            actions_frame, text = "Create", command = self.handle_create
        ).grid(row=4, column=0, columnspan=2, sticky="w")

        ttk.Label(actions_frame, text="Deposit/Withdraw").grid(
            row=5, column=0, columnspan=2, sticky="w"
        )

        self.txn_number_entry = self._labeled_entry(actions_frame, "Account Number", 6)
        self.txn_amount_entry = self._labeled_entry(actions_frame, "Amount", 7)
        ttk.Button(
            actions_frame, text = "Deposit", command=self.handle_deposit 
        ).grid(row=8, column=1, sticky="w",pady=4)
        ttk.Button(
            actions_frame, text="Withdraw", command=self.handle_withdraw
        ).grid(row=8, column=1, sticky="w", pady=4)

        ttk.Label(actions_frame, text="Transfer").grid(
            row=9, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )

        self.transfer_source_entry = self._labeled_entry(actions_frame, "Source Number", 10)
        self.transfer_target_entry = self._labeled_entry(actions_frame, "Target Number", 11)
        self.transfer_amount_entry = self._labeled_entry(actions_frame, "Amount", 12)
        ttk.Button(
            actions_frame, text="Transfer", command= self.handle_transfer
        ).grid(row=13, column=0, columnspan=2, sticky="w", pady=4)

        self.status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status, anchor="w").grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12)
        )
    
    def _labeled_entry(self, parent, label, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        entry = ttk.Entry(parent)
        entry.grid(row=row, column=1, sticky="ew", padx=8, pady=2)
        return entry
    
    def _set_status(self,message):
        self.status.set(message)
        self.update_idletasks()
    
    def refresh_accounts(self):
        try:
            accounts = fetch_accounts()
        except Exception as exc:
            self._set_status(f"Failed to load account: {exc}")
            return
        self.accounts_list.delete(0, "end")
        for account in accounts:
            self.accounts_list.insert(
            "end",
            f"{account['number']} • {account['name']} • balance {account['amount']}",
            )
        self._set_status(f"Loaded {len(accounts)} accounts.")

    def handle_create(self):
        try:
            name = self.name_entry.get().strip()
            number = int(self.number_entry.get().strip())
            amount = float(self.amount_entry.get().strip())
            create_account(name = name, number = number, amount = amount)
        except Exception as exc:
            messagebox.showerror("Create failed", str(exc))
            return
        self.refresh_accounts()

    def handle_deposit(self):
        try:
            number = int(self.txn_number_entry.get().strip())
            amount = float(self.txn_amount_entry.get().strip())
            deposit(number = number, amount = amount)
        except Exception as exc:
            messagebox.showerror("Deposit Failed", str(exc))
            return
        self.refresh_accounts()

    def handle_withdraw(self):
        try:
            number = int(self.txn_number_entry.get().strip())
            amount = float(self.txn_amount_entry.get().strip())
            withdraw(number = number,amount = amount)
        
        except Exception as exc:
            messagebox.showerror("Withdraw failed", str(exc))
            return
        self.refresh_accounts()

    def handle_transfer(self):
        try:
            source = int(self.transfer_source_entry.get().strip())
            target = int(self.transfer_target_entry.get().strip())
            amount = float(self.transfer_amount_entry.get().strip())
            transfer(source_number = source, target_number= target, amount = amount)
        except Exception as exc:
            messagebox.showerror("Transfer failed", str(exc))
            return
        self.refresh_accounts()


class ChatUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ollama Chat")
        self.geometry("820x620")
        self.minsize(760, 560)

        self.style = ttk.Style(self)
        self._setup_styles()

        # Keeps the current streamed assistant text so we can store it in history.
        self._stream_buffer = []

        self.msg_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # Top bar
        top = ttk.Frame(self, padding=(10, 10, 10, 6))
        top.pack(fill="x")

        ttk.Label(top, text="Model:", style="Top.TLabel").pack(side="left")
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        self.model_cb = ttk.Combobox(
            top,
            textvariable=self.model_var,
            values=MODEL_CHOICES,
            state="readonly",
            width=28
        )
        self.model_cb.pack(side="left", padx=(6, 16))

        ttk.Label(top, text="Temperature:", style="Top.TLabel").pack(side="left")
        self.temp_var = tk.DoubleVar(value=0.7)
        self.temp_spin = ttk.Spinbox(top, from_=0.0, to=1.5, increment=0.1,
                                     textvariable=self.temp_var, width=5)
        self.temp_spin.pack(side="left", padx=(6, 16))

        self.stream_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="Stream", variable=self.stream_var).pack(side="left")

        self.bank_btn = ttk.Button(top, text="Bank UI", command=self._open_bank_ui)
        self.bank_btn.pack(side="left", padx=(10, 16))

        self.clear_btn = ttk.Button(top, text="Clear", command=self.clear_chat)
        self.clear_btn.pack(side="right")

        # Chat area
        mid = ttk.Frame(self, padding=(10, 0, 10, 0))
        mid.pack(fill="both", expand=True)

        self.chat = tk.Text(mid, wrap="word", state="disabled", bd=0, padx=8, pady=10)
        self.chat.pack(fill="both", expand=True, side="left")
        self._setup_tags()

        scroll = ttk.Scrollbar(mid, command=self.chat.yview)
        scroll.pack(side="right", fill="y")
        self.chat.config(yscrollcommand=scroll.set)

        # Input area
        bottom = ttk.Frame(self, padding=(10, 6, 10, 10))
        bottom.pack(fill="x")

        self.entry = tk.Text(bottom, height=3, wrap="word")
        self.entry.pack(fill="x", side="left", expand=True)
        self.entry.bind("<Control-Return>", self._on_send_ctrl_enter)

        self.send_btn = ttk.Button(bottom, text="Send", command=self.send_message)
        self.send_btn.pack(side="left", padx=(10, 0))

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self, textvariable=self.status_var, anchor="w", padding=(10, 4))
        status.pack(fill="x")

        # Health check
        self.after(400, self._check_backend)

    # ---- UI Styling ----
    def _setup_styles(self):
        base = "clam" if "clam" in self.style.theme_names() else self.style.theme_use()
        self.style.theme_use(base)
        self.style.configure("Top.TLabel", font=("Segoe UI", 10))
        self.style.configure("UserBubble.TFrame", background="#DCF2FF")
        self.style.configure("BotBubble.TFrame", background="#F5F5F7")
        self.style.configure("Meta.TLabel", font=("Segoe UI", 8), foreground="#666")

    def _setup_tags(self):
        self.chat.tag_configure("user_bubble", lmargin1=12, lmargin2=12, rmargin=80, spacing3=6, background="#DCF2FF")
        self.chat.tag_configure("bot_bubble",  lmargin1=80, lmargin2=80, rmargin=12, spacing3=6, background="#F5F5F7")
        self.chat.tag_configure("meta", foreground="#666", font=("Segoe UI", 8, "italic"))
        self.chat.tag_configure("mono", font=("Consolas", 10))

    def _append_bubble(self, text: str, who: str):
        tag = "user_bubble" if who == "user" else "bot_bubble"
        timestamp = datetime.now().strftime("%H:%M")
        meta = f"\n{who.upper()} • {timestamp}\n"

        self.chat.configure(state="normal")
        self.chat.insert("end", meta, ("meta",))
        self.chat.insert("end", text.strip() + "\n", (tag,))
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _append_stream_start(self):
        self.chat.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M")
        meta = f"\nASSISTANT • {timestamp}\n"
        self.chat.insert("end", meta, ("meta",))
        self.chat.insert("end", "", ("bot_bubble",))
        self.chat.see("end")
        self.chat.configure(state="disabled")
        self._stream_buffer = []  # reset buffer at start of a streamed reply

    def _append_stream_chunk(self, chunk: str):
        self._stream_buffer.append(chunk)
        self.chat.configure(state="normal")
        self.chat.insert("end", chunk, ("bot_bubble",))
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _append_meta(self, text: str):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"\n{text}\n", ("meta",))
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _set_status(self, msg: str):
        self.status_var.set(msg)
        self.update_idletasks()

    def _open_bank_ui(self):
        try:
            subprocess.Popen([sys.executable, "run_bank.py"])
            self._set_status("Opened Bank UI.")
        except Exception as exc:
            self._set_status(f"Failed to open Bank UI: {exc}")

    def clear_chat(self):
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        self.msg_history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self._set_status("Cleared.")

    # ---- Backend comms ----
    def _check_backend(self):
        try:
            r = requests.get(f"{BACKEND_URL}/health", timeout=2)
            if r.ok:
                data = r.json()
                self._set_status(f"Connected ✓  Model: {data.get('model')}")
            else:
                self._set_status("Backend not responding.")
        except Exception:
            self._set_status("Backend offline. Start backend.py")

    def _on_send_ctrl_enter(self, *_):
        self.send_message()
        return "break"

    def _find_account_by_name(self, accounts, name):
        lowered = name.strip().lower()
        for account in accounts:
            if account["name"].strip().lower() == lowered:
                return account
        return None

    def _prompt_account_details(self, name):
        number = simpledialog.askinteger("Account number", f"Account number for {name}:")
        if number is None:
            return None
        amount = simpledialog.askfloat("Initial deposit", f"Initial amount for {name}:")
        if amount is None:
            return None
        return number, amount

    def _try_handle_bank_intent(self, user_text: str) -> bool:

        create_action = r"(?:create|make|open|set up|setup)"
        account_phrase = r"(?:bank\s+)?account"
        transfer_action = r"(?:transfer|send|move)"


        transfer_pattern = re.compile(
            rf"{create_action}\s+(?:a\s+)?(?:new\s+)?{account_phrase}\s+for\s+"
            r"(?P<new>[\w\s]+?)\s+and\s+"
            rf"{transfer_action}\s+(?P<amount>\d+(?:\.\d+)?)\s+from\s+"
            r"(?P<source>[\w\s]+?)\s+to\s+(?P<target>[\w\s]+)",
            re.IGNORECASE,
        )

        transfer_only_pattern = re.compile(
            rf"{transfer_action}\s+(?P<amount>\d+(?:\.\d+)?)\s+from\s+"
            r"(?P<source>[\w\s]+?)\s+to\s+(?P<target>[\w\s]+)",
            re.IGNORECASE,
        )
        create_pattern = re.compile(
            rf"{create_action}\s+(?:a\s+)?(?:new\s+)?{account_phrase}\s+for\s+"
            r"(?P<name>[\w\s]+)",
            re.IGNORECASE,
        )

        transfer_match = transfer_pattern.search(user_text)
        if transfer_match:
            new_name = transfer_match.group("new").strip()
            source_name = transfer_match.group("source").strip()
            target_name = transfer_match.group("target").strip()
            amount = float(transfer_match.group("amount"))

            try:
                accounts = fetch_accounts()
            except Exception as exc:
                self._append_meta(f"Bank lookup failed: {exc}")
                return True

            source = self._find_account_by_name(accounts, source_name)
            target = self._find_account_by_name(accounts, target_name)

            if not source:
                self._append_meta(f"Could not find an account named '{source_name}'.")
                return True

            if not target:
                if target_name.lower() == new_name.lower():
                    details = self._prompt_account_details(new_name)
                    if details is None:
                        self._append_meta("Canceled account creation.")
                        return True
                    number, initial = details
                    try:
                        target = create_account(new_name, number, initial)
                    except Exception as exc:
                        self._append_meta(f"Create account failed: {exc}")
                        return True
                else:
                    self._append_meta(
                        f"Could not find target account '{target_name}'. Create it first."
                    )
                    return True

            try:
                transfer(source["number"], target["number"], amount)
            except Exception as exc:
                self._append_meta(f"Transfer failed: {exc}")
                return True

            self._append_bubble(
                f"Transferred {amount} from {source['name']} to {target['name']}.",
                who="assistant",
            )
            return True
        
        transfer_only_match = transfer_only_pattern.search(user_text)
        if transfer_only_match:
            source_name = transfer_only_match.group("source").strip()
            target_name = transfer_only_match.group("target").strip()
            amount = float(transfer_only_match.group("amount"))

            try:
                accounts = fetch_accounts()
            except Exception as exc:
                self._append_meta(f"Bank lookup failed: {exc}")
                return True

            source = self._find_account_by_name(accounts, source_name)
            target = self._find_account_by_name(accounts, target_name)

            if not source:
                self._append_meta(f"Could not find an account named '{source_name}'.")
                return True
            if not target:
                details = self._prompt_account_details(target_name)
                if details is None:
                    self._append_meta("Canceled account creation.")
                    return True
                number, initial = details
                try:
                    target = create_account(target_name, number, initial)
                except Exception as exc:
                    self._append_meta(f"Create account failed: {exc}")
                    return True

            try:
                transfer(source["number"], target["number"], amount)
            except Exception as exc:
                self._append_meta(f"Transfer failed: {exc}")
                return True

            self._append_bubble(
                f"Transferred {amount} from {source['name']} to {target['name']}.",
                who="assistant",
            )
            return True


        create_match = create_pattern.search(user_text)
        if create_match:
            name = create_match.group("name").strip()
            details = self._prompt_account_details(name)
            if details is None:
                self._append_meta("Canceled account creation.")
                return True
            number, amount = details
            try:
                create_account(name, number, amount)
            except Exception as exc:
                self._append_meta(f"Create account failed: {exc}")
                return True
            self._append_bubble(
                f"Created account for {name} with number {number}.", who="assistant"
            )
            return True

        return False
    
    def send_message(self):
        user_text = self.entry.get("1.0", "end").strip()
        if not user_text:
            return
        self.entry.delete("1.0", "end")
        self._append_bubble(user_text, who="user")

        if self._try_handle_bank_intent(user_text):
            return

        # ---- Slash commands (local ops) ----
        # /sys                      -> show system info
        # /remember key value       -> set a key in JSON store
        # /recall key               -> get a key from JSON store
        # /mem                      -> dump all stored keys
        # /note some text...        -> append to notes.txt
        # /log add <event> [json]
        # /log last [n]
        # /log find <key>=<value> [limit]
        lowered = user_text.strip()
        if lowered.startswith("/sys"):
            self._cmd_system_info()
            return
        if lowered.startswith("/remember "):
            parts = lowered.split(" ", 2)
            if len(parts) >= 3:
                key, value = parts[1], parts[2]
                self._cmd_store_set(key, value)
                return
            else:
                self._append_meta("Usage: /remember <key> <value>")
                return
        if lowered.startswith("/recall "):
            parts = lowered.split(" ", 1)
            if len(parts) == 2:
                self._cmd_store_get(parts[1])
                return
            else:
                self._append_meta("Usage: /recall <key>")
                return
        if lowered.startswith("/mem"):
            self._cmd_store_all()
            return
        if lowered.startswith("/note "):
            note_text = lowered.split(" ", 1)[1]
            self._cmd_append_log(note_text)
            return
        if lowered.startswith("/log add"):
            rest = lowered[len("/log add"):].strip()
            event, data = rest,{}
            if "{" in rest:
                ev, js = rest.split("{ ", 1)
                event = ev.strip()
                try:
                    data = json.loads("{" +js)
                except Exception:
                    pass
            self._cmd_log_write(event, data)
            return
        
        if lowered.startswith("/log last"):
            parts = lowered.split()
            n = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 20
            self._cmd_log_last(n)
            return
        
        if lowered.startswith("/log find"):
            rest = lowered[len("/log find "):].strip()
            parts = rest.split()
            key, value = parts[0].split("=", 1)
            limit = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 50
            self._cmd_log_query(key, value, limit)
            return


        # ---- Normal chat path (LLM) ----
        self.msg_history.append({"role": "user", "content": user_text})
        t = threading.Thread(target=self._do_chat, args=(), daemon=True)
        t.start()


    # ---- Logging Helpers ----
    def _cmd_log_write(self, event: str, data: dict | None = None, level: str = "INFO"):
        try:
            r = requests.post(f"{BACKEND_URL}/log/write",
                            json={"event": event, "data": data or {}, "level": level},
                            timeout=10)
            r.raise_for_status()
            self._append_bubble("Logged.", who="assistant")
        except Exception as e:
            self._append_meta(f"log write error: {e}")

    def _cmd_log_last(self, n: int = 20):
        try:
            r = requests.get(f"{BACKEND_URL}/log/last", params={"n": n}, timeout=10)
            r.raise_for_status()
            items = r.json().get("items", [])
            pretty = json.dumps(items, ensure_ascii=False, indent=2) or "(no entries)"
            self._append_bubble(pretty, who="assistant")
        except Exception as e:
            self._append_meta(f"log last error: {e}")

    def _cmd_log_query(self, key: str, value: str, limit: int = 50):
        try:
            r = requests.post(f"{BACKEND_URL}/log/query",
                            json={"key": key, "value": value, "limit": limit}, timeout=10)
            r.raise_for_status()
            items = r.json().get("items", [])
            pretty = json.dumps(items, ensure_ascii=False, indent=2) or "(no match)"
            self._append_bubble(pretty, who="assistant")
        except Exception as e:
            self._append_meta(f"log query error: {e}")

        
    # ---- Slash-command handlers ----
    def _cmd_system_info(self):
        try:
            r = requests.get(f"{BACKEND_URL}/system/info", timeout=10)
            r.raise_for_status()
            info = r.json()
            pretty = (
                f"Time: {info.get('now')} ({info.get('timezone')})\n"
                f"User: {info.get('username')}  Host: {info.get('hostname')}\n"
                f"CWD:  {info.get('cwd')}\n"
                f"Drive:{info.get('drive')}\n"
                f"AppDir: {info.get('app_dir')}\n"
                f"Store:  {info.get('store_json')}\n"
                f"Log:    {info.get('store_log')}"
            )
            self._append_bubble(pretty, who="assistant")
        except Exception as e:
            self._append_meta(f"System info error: {e}")

    def _cmd_store_set(self, key: str, value: str):
        try:
            r = requests.post(f"{BACKEND_URL}/store/set",
                              json={"key": key, "value": value}, timeout=10)
            r.raise_for_status()
            self._append_bubble(f"Saved `{key}`.", who="assistant")
        except Exception as e:
            self._append_meta(f"Store set error: {e}")

    def _cmd_store_get(self, key: str):
        try:
            r = requests.get(f"{BACKEND_URL}/store/get", params={"key": key}, timeout=10)
            r.raise_for_status()
            val = r.json().get("value")
            self._append_bubble(f"{key} = {val}", who="assistant")
        except Exception as e:
            self._append_meta(f"Store get error: {e}")

    def _cmd_store_all(self):
        try:
            r = requests.get(f"{BACKEND_URL}/store/all", timeout=10)
            r.raise_for_status()
            data = r.json().get("data", {})
            pretty = json.dumps(data, ensure_ascii=False, indent=2) or "(empty)"
            self._append_bubble(pretty, who="assistant")
        except Exception as e:
            self._append_meta(f"Store all error: {e}")

    def _cmd_append_log(self, text: str):
        try:
            r = requests.post(f"{BACKEND_URL}/store/append", json={"text": text}, timeout=10)
            r.raise_for_status()
            self._append_bubble("Appended to notes.txt", who="assistant")
        except Exception as e:
            self._append_meta(f"Append log error: {e}")

    # ---- Chat with backend ----
    def _do_chat(self):
        try:
            payload = {
                "messages": self.msg_history,
                "model": self.model_var.get(),
                "temperature": float(self.temp_var.get()),
                "stream": bool(self.stream_var.get()),
            }

            if self.stream_var.get():
                self._set_status("Streaming…")
                self._append_stream_start()
                with requests.post(f"{BACKEND_URL}/chat/stream",
                                   json=payload, stream=True, timeout=300) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            self._append_stream_chunk(chunk)
                self._set_status("Ready")
                bot_text = "".join(self._stream_buffer).strip()
                if not bot_text:
                    bot_text = "(No response)"
                self.msg_history.append({"role": "assistant", "content": bot_text})
                self._stream_buffer = []
            else:
                self._set_status("Thinking…")
                r = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=300)
                r.raise_for_status()
                data = r.json()
                content = data.get("message", {}).get("content", "").strip() or "(No response)"
                self._append_bubble(content, who="assistant")
                self.msg_history.append({"role": "assistant", "content": content})
                self._set_status("Ready")

        except requests.exceptions.RequestException as e:
            self._set_status("Network error.")
            messagebox.showerror("Network Error", str(e))
        except Exception as e:
            self._set_status("Error.")
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = ChatUI()
    app.mainloop()
