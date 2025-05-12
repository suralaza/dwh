import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import threading
import subprocess
import time

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Мастер релиза")
        self.root.geometry("700x500")
        self.mappings = {}
        self.params = {}

        self.make_tabs()
        self.create_mapping_tab()
        self.create_build_tab()

    def make_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        self.mapping_frame = ttk.Frame(self.notebook)
        self.build_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.mapping_frame, text="Маппинг Git")
        self.notebook.add(self.build_frame, text="Сборка релиза")

    # --- Маппинг Git ---
    def create_mapping_tab(self):
        left = ttk.Frame(self.mapping_frame)
        left.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        right = ttk.Frame(self.mapping_frame)
        right.pack(side='right', fill='both', expand=False)

        self.mapping_tree = ttk.Treeview(left, show='tree')
        self.mapping_tree.pack(side='left', fill='both', expand=True)
        self.mapping_tree.bind('<Button-3>', self.show_context_menu)

        self.scrollbar = ttk.Scrollbar(left, orient='vertical', command=self.mapping_tree.yview)
        self.mapping_tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side='right', fill='y')

        button_width = 20
        load_folder_btn = tk.Button(right, text="Выбрать проект Git", width=button_width, command=self.load_folder_dialog)
        save_btn = tk.Button(right, text="Сохранить маппинг", width=button_width, command=self.save_mapping)
        # Новая кнопка "Загрузить маппинг"
        load_mapping_btn = tk.Button(right, text="Загрузить маппинг", width=button_width, command=self.load_mapping)
        # Новая кнопка "Показать маппинг"
        show_mapping_btn = tk.Button(right, text="Показать маппинг", width=button_width, command=self.show_mapping_popup)
        # Кладём все четыре кнопки
        load_folder_btn.pack(pady=5)
        save_btn.pack(pady=5)
        load_mapping_btn.pack(pady=5)
        show_mapping_btn.pack(pady=5)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Показать параметры", command=self.open_configure_panel)

    # --- Новая функция ---
    def load_mapping(self):
        path = filedialog.askopenfilename(title="Загрузить маппинг", filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')])
        if path:
            try:
                with open(path, encoding='utf-8') as f:
                    self.mappings = json.load(f)
                self.base_folder = ""  # чтобы не использовать старую папку
                self.update_treeview()
                messagebox.showinfo("Маппинг загружен", "Маппинг успешно загружен из файла.")
            except Exception as e:
                messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить маппинг: {e}")

    # --- Новая функция ---
    def show_mapping_popup(self):
        def pretty_dict(d, indent=0):
            res = ''
            if isinstance(d, dict):
                for k, v in d.items():
                    res += "  " * indent + str(k) + "\n"
                    res += pretty_dict(v, indent + 1)
            elif isinstance(d, list):
                for v in d:
                    if isinstance(v, (dict, list)):
                        res += pretty_dict(v, indent + 1)
                    else:
                        res += "  " * indent + str(v) + "\n"
            return res

        popup = tk.Toplevel(self.root)
        popup.title("Текущий маппинг")
        popup.geometry("600x500")
        txt = tk.Text(popup, wrap='word')
        txt.pack(fill='both', expand=True, padx=10, pady=10)
        if 'structure' in self.mappings:
            pretty = "*structure*\n" + pretty_dict(self.mappings['structure'])
        else:
            pretty = "(Нет structure в маппинге)"
        if 'params' in self.mappings:
            pretty += "\n*params*\n"
            for k, v in self.mappings['params'].items():
                pretty += f"{k}:\n"
                for item in v:
                    pretty += "  - "
                    pretty += ", ".join(f"{kk}={vv}" for kk, vv in item.items())
                    pretty += "\n"
        txt.insert('1.0', pretty)
        txt.config(state='disabled')
        tk.Button(popup, text="Закрыть", command=popup.destroy).pack(pady=5)

    def load_folder_dialog(self):
        folder_path = filedialog.askdirectory(title="Выберите папку проекта")
        if folder_path:
            self.load_folder_hierarchy(folder_path)

    def load_folder_hierarchy(self, folder_path):
        self.base_folder = folder_path
        self.mappings = self.scan_folders_only(folder_path)
        self.update_treeview()

    def scan_folders_only(self, path):
        folders = {}
        try:
            for entry in os.listdir(path):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    folders[entry] = self.scan_folders_only(full_path)
        except Exception as e:
            pass
        return folders

    def update_treeview(self):
        self.mapping_tree.delete(*self.mapping_tree.get_children())
        if hasattr(self, 'base_folder') and self.base_folder:
            root_name = os.path.basename(self.base_folder)
            root_id = self.mapping_tree.insert('', 'end', text=root_name)
            self.fill_treeview(root_id, self.mappings)
        else:
            self.fill_treeview('', self.mappings)

    def fill_treeview(self, parent, folders):
        for folder_name, subfolders in folders.items():
            item_id = self.mapping_tree.insert(parent, 'end', text=folder_name)
            self.fill_treeview(item_id, subfolders)

    def show_context_menu(self, event):
        item = self.mapping_tree.identify_row(event.y)
        if item:
            self.mapping_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def open_configure_panel(self):
        selected_item = self.mapping_tree.selection()
        if not selected_item:
            return

        folder_name = self.get_full_path_from_tree(selected_item[0])

        if folder_name not in self.params:
            self.params[folder_name] = []

        config_window = tk.Toplevel(self.root)
        config_window.title(f"Параметры для {folder_name}")

        params_frame = tk.Frame(config_window)
        params_frame.pack(fill='both', expand=True, pady=(10,0))
        params_listbox = tk.Listbox(params_frame, width=50)
        params_listbox.pack(padx=10, pady=5, fill='both', expand=True)

        def refresh_listbox():
            params_listbox.delete(0, tk.END)
            for param in self.params[folder_name]:
                params_listbox.insert(tk.END, f"Якорь: {param['anchor']}")

        refresh_listbox()

        entry_frame = tk.Frame(config_window)
        entry_frame.pack(pady=5)
        anchor_var = tk.StringVar()


        tk.Label(entry_frame, text="Якорь парсера:").grid(row=1, column=0, padx=5, pady=2, sticky='e')
        anchor_entry = tk.Entry(entry_frame, textvariable=anchor_var, width=20)
        anchor_entry.grid(row=1, column=1, padx=5, pady=2)

        btn_frame = tk.Frame(config_window)
        btn_width = 12
        def add_param():
            if not anchor_var.get():
                messagebox.showwarning("Внимание", "Заполните поле якоря!")
                return
            self.params[folder_name].append({
                "anchor": anchor_var.get()
            })
            anchor_var.set("")
            refresh_listbox()

        def delete_param():
            selection = params_listbox.curselection()
            if selection:
                idx = selection[0]
                del self.params[folder_name][idx]
                refresh_listbox()

        def save_param():
            messagebox.showinfo("Параметры сохранены", "Параметры для папки успешно обновлены.")
            config_window.destroy()

        tk.Button(btn_frame, text="Добавить", width=btn_width, command=add_param).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Удалить", width=btn_width, command=delete_param).grid(row=0, column=1, padx=10)
        tk.Button(btn_frame, text="Сохранить", width=btn_width, command=save_param).grid(row=0, column=2, padx=10)
        btn_frame.pack(pady=10)

    def get_full_path_from_tree(self, item_id):
        path_parts = []
        while item_id:
            node_text = self.mapping_tree.item(item_id, 'text')
            path_parts.insert(0, node_text)
            item_id = self.mapping_tree.parent(item_id)
        if hasattr(self, 'base_folder') and self.base_folder:
            return os.path.join(self.base_folder, *path_parts[1:])
        return os.path.join(*path_parts)

    def save_mapping(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filepath:
            try:
                output = {
                    "structure": self.mappings,
                    "params": self.params
                }
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(output, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("Успех", "Маппинг и параметры успешно сохранены.")
                # После сохранения маппинга автоматически переключаем на вкладку Сборка релиза
                self.notebook.select(self.build_frame)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить маппинг: {e}")

    # --- Сборка релиза ---
    def create_build_tab(self):
        frame = self.build_frame

        param_top = ttk.Frame(frame)
        param_top.pack(fill='x', pady=10)
        ttk.Label(param_top, text="Параметры сборки релиза (шаблон)").pack(side='left', padx=5)
        self.build_params_edit = tk.Text(frame, height=16, width=90)
        self.build_params_edit.pack(fill='x', expand=False, padx=10)
        
        button_bar = ttk.Frame(frame)
        button_bar.pack(fill='x', pady=5)

        ttk.Button(button_bar, text="Загрузить шаблон", command=self.load_build_template).pack(side='left', padx=5)
        self.run_button = ttk.Button(button_bar, text="Запустить сборку", command=self.run_release_build)
        self.run_button.pack(side='right', padx=8)

        self.progress_bar = ttk.Progressbar(frame, orient='horizontal', mode='determinate', length=400)
        self.progress_bar.pack(pady=10)

        self.param_panel = tk.LabelFrame(frame, text="Выбранные параметры", padx=10, pady=8)
        self.param_panel.pack(fill='x', padx=10, pady=8)
        self.param_label = tk.Label(self.param_panel, text="Параметры будут здесь после запуска сборки.")
        self.param_label.pack(fill='x')

    def load_build_template(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files","*.json")], title="Загрузить шаблон параметров")
        if filepath:
            try:
                with open(filepath, 'r', encoding="utf-8") as f:
                    data = json.load(f)
                pretty = json.dumps(data, ensure_ascii=False, indent=4)
                self.build_params_edit.delete('1.0', tk.END)
                self.build_params_edit.insert(tk.END, pretty)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить шаблон: {e}")

    def get_build_params(self):
        txt = self.build_params_edit.get('1.0', tk.END)
        try:
            params = json.loads(txt)
            return params
        except Exception:
            return {}

    def run_release_build(self):
        # Сохраняем параметры выбранные на этой вкладке
        params = self.get_build_params()
        if not params:
            messagebox.showerror("Ошибка", "Некорректный JSON параметров сборки!")
            return

        # Показываем только параметры релиза
        panel_text = "Параметры релиза:\n"
        panel_text += json.dumps(params, ensure_ascii=False, indent=2)
        self.param_label.config(text=panel_text,justify="left")
        self.progress_bar['value'] = 0

        # Запуск в потоке чтобы не блокировать интерфейс
        threading.Thread(target=self.simulate_build_process, args=(params,), daemon=True).start()

    def simulate_build_process(self, params):
        # Имитируем работу парсера и сборку
        steps = 15
        for i in range(steps+1):
            time.sleep(0.09)
            self.progress_bar['value'] = i * 100 / steps
            self.progress_bar.update_idletasks()

        # Для примера:
        messagebox.showinfo("Готово", "Сборка релиза завершена (заглушка)")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

