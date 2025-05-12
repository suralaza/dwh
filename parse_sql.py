import json
import os
import sys
import re

def log_warning(anchor):
    print(f"{anchor} WARNING: проверьте правильность формирования релизного файла и раскладки", file=sys.stderr)

def main():
    print("Старт работы парсера SQL скриптов.")

    # Загрузка параметров
    try:
        with open("params.json", encoding="utf-8") as f:
            params = json.load(f)
        print("Параметры успешно загружены из params.json")
    except Exception as e:
        print(f"Ошибка загрузки params.json: {e}")
        sys.exit(1)

    # Сохраняем параметры в переменные (независимо от регистра)
    def get_param(name):
        for k, v in params.items():
            if k.lower() == name.lower():
                return v
        return None

    author = get_param("Author")
    date = get_param("Date")
    duration = get_param("Duration")
    task = get_param("Task")
    model_dir = get_param("Model dir name")
    model_schema = get_param("Model schema")
    script_path = get_param("Path to script")
    parsing_anchor = get_param("Parsing anchor")
    storage = get_param("Storage")
    db_name = get_param("Db name")
    obj_owner = get_param("Object owner")
    contour = get_param("Contour name")

    print(f"Путь к скриптам: {script_path}")
    print(f"Якоря для разбора: {parsing_anchor}")

    # Преобразуем якоря в словарь (ключи - строчные)
    try:
        anchor_dicts = parsing_anchor
    except Exception as e:
        print(f"Ошибка при разборе якорей: {e}")
        sys.exit(1)

    anchor_to_dir = {}
    allowed_anchors = set()
    for dct in anchor_dicts:
        for k, v in dct.items():
            anchor_to_dir[k.strip().lower()] = v.strip()
            allowed_anchors.add(k.strip().lower())
    print(f"Разрешённые якоря: {allowed_anchors}")

    DDL_WORDS = ["drop", "alter", "truncate", "delete", "exchange", "analyze", "vacuum"]

    ddl_patterns = [re.compile(rf"\b{word}\b", re.IGNORECASE) for word in DDL_WORDS]

    # Получаем список файлов для парсинга
    files = [f for f in os.listdir(script_path) if os.path.isfile(os.path.join(script_path, f))]
    print(f"Найдено файлов для обработки: {len(files)}")
    for filename in files:
        print(f"Обработка файла: {filename}")
        full_path = os.path.join(script_path, filename)

        try:
            with open(full_path, encoding='utf-8') as file:
                lines = file.readlines()
            print(f"Файл {filename} успешно прочитан ({len(lines)} строк)")
        except Exception as e:
            print(f"Ошибка чтения файла {filename}: {e}")
            continue

        i = 0
        current_anchor = None
        buffer = []
        out_files = []
        while i < len(lines):
            line = lines[i].rstrip('\n')
            stripped = line.strip()
            # Если комментарий-якорь
            if stripped.startswith('--'):
                parts = stripped.split()
                if not parts:
                    i += 1
                    continue
                anchor = parts[0].lower()
                # Если это допустимый якорь
                if anchor in allowed_anchors:
                    print(f"Найден якорь {anchor} в строке {i+1}")
                    if current_anchor and buffer:
                        relative_path = anchor_to_dir.get(current_anchor)
                        if relative_path != "WARNING":
                            project_root = os.path.abspath(
                                os.path.join(script_path, "..", "..")
                            )
                            out_dir = os.path.normpath(os.path.join(project_root, relative_path))
                            os.makedirs(out_dir, exist_ok=True)
                            fname = f"{task}_{current_anchor[2:]}_{len(out_files)+1}.sql"
                            with open(os.path.join(out_dir, fname), 'w', encoding="utf-8") as fhout:
                                fhout.write('\n'.join(buffer).strip()+"\n")
                            out_files.append(fname)

                            print(f"Создан файл: {os.path.join(out_dir, fname)} (строк: {len(buffer)})")

                            # Проверка на опасные DDL/DML
                            joined_buffer = ' '.join(buffer).lower()
                            for pat, word in zip(ddl_patterns, DDL_WORDS):
                                if pat.search(joined_buffer):
                                    print(f"ВНИМАНИЕ: в блоке {fname} найдено потенциально опасное слово: {word.upper()}")

                        buffer = []
                    current_anchor = anchor
                else:
                    print(f"В файле {filename} обнаружен неизвестный якорь: {anchor}")
                    log_warning(anchor)
                    current_anchor = None
                    buffer = []
                i += 1
                continue

            if current_anchor:
                buffer.append(line)
            i += 1
        # Сохранение оставшегося буфера
        if current_anchor and buffer:
            relative_path = anchor_to_dir.get(current_anchor)
            if relative_path != "WARNING":
                project_root = os.path.abspath(
                    os.path.join(script_path, "..", "..")
                )
                out_dir = os.path.normpath(os.path.join(project_root, relative_path))
                os.makedirs(out_dir, exist_ok=True)
                fname = f"{task}_{current_anchor[2:]}_{len(out_files)+1}.sql"
                with open(os.path.join(out_dir, fname), 'w', encoding="utf-8") as fhout:
                    fhout.write('\n'.join(buffer).strip()+"\n")
                out_files.append(fname)
                print(f"Финальный блок: создан файл: {os.path.join(out_dir, fname)} (строк: {len(buffer)})")

                joined_buffer = ' '.join(buffer).lower()
                for pat, word in zip(ddl_patterns, DDL_WORDS):
                    if pat.search(joined_buffer):
                        print(f"ВНИМАНИЕ: в блоке {fname} найдено потенциально опасное слово: {word.upper()}")

        print(f"Завершена обработка файла {filename}, сформировано {len(out_files)} блок(ов).")
    print("Работа парсера завершена.")

if __name__ == '__main__':
    main()
