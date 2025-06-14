# !/usr/bin/env python3

import argparse
import logging
import yaml
import os
import re
import sys
from logger import log
from typing import List, Dict, Any, Optional, Pattern


def load_yaml(path):
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"File not found: {path}")
        return None
    except yaml.YAMLError as e:
        print(f"YAML error: {e}")
        return None


def env_subst(item: Any, context: dict) -> Any:
    """Заменяет ${...} в строках на значения из context (рекурсивно)."""
    if isinstance(item, str):
        def repl(m):
            keys = m.group(1).split(".")
            val = context
            for key in keys:
                val = val.get(key)
                if val is None:
                    break
            return str(val) if val is not None else m.group(0)

        return re.sub(r"\${([a-zA-Z0-9_.]+)}", repl, item)
    elif isinstance(item, dict):
        return {k: env_subst(v, context) for k, v in item.items()}
    elif isinstance(item, list):
        return [env_subst(v, context) for v in item]
    else:
        return item


def ensure_dirs(filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)


def read_file_lines(path, encoding="utf-8"):
    with open(path, encoding=encoding) as f:
        return [line.rstrip('\n') for line in f]


def object_type_from_ddl(ddl_content, object_type_map):
    """
    Определяет тип объекта из DDL по блоку в parsing_config.yaml object_type_map .
    Возвращает имя папки для сохранения файла согласно map.
    """
    ddl_content_nospace = ddl_content.replace("or replace", "")
    # Ключи из user yaml могут быть с пробелами (external table), формируем regexp
    types_pattern = '|'.join([
        key.replace("_", r"\s+") for key in object_type_map.keys()
    ])
    regexp = r'create\s+(' + types_pattern + r')\s+'
    m = re.search(regexp, ddl_content_nospace, re.IGNORECASE)
    if m:
        ddl_type = m.group(1).replace(" ", "_").lower()
        # Приводим map к такому же виду, чтобы искать ключ без багов
        for k, v in object_type_map.items():
            if ddl_type == k.replace(" ", "_").lower():
                return v
    return "unknown"


def parse_object_dot(obj):
    if obj and '.' in obj:
        return obj.split('.', 1)
    return 'unknown', obj


def get_block_patterns(blocks_conf):
    patterns = []
    for block in blocks_conf:
        patterns.append({
            "name": block['name'],
            "begin": re.compile(block['begin']),
            "end": re.compile(block['end']),
            "block_conf": block
        })
    return patterns


def render_path(template, **kwargs):
    # простая подстановка параметры вида {name}
    for k, v in kwargs.items():
        template = template.replace(f"{{{k}}}", str(v))
    return template


def apply_template(path, params, encoding="utf-8"):
    if not path or not os.path.exists(path):
        return ""
    with open(path, encoding=encoding) as f:
        template = f.read()
    for k, v in params.items():
        template = template.replace(f"{{{k}}}", str(v))
    return template


def parse_template(template, line):
    if not isinstance(template, str):
        # Исправление ошибки
        logging.error(f"Expected a string for template, but got {type(template).__name__}")
        raise TypeError(f"Expected a string for template, but got {type(template).__name__}")

    # 1. Найти все {var} в шаблоне
    var_matches = list(re.finditer(r"\{([^}]+)\}", template))

    if not var_matches:
        return {}

    # Простая реализация парсинга строки для соответствия шаблону
    result = {}
    match_start = 0

    for vm in var_matches:
        # Получаем имя переменной
        var_name = vm.group(1)

        # Ожидаем, что мы найдем соответствующую часть строки
        # Захватываем до следующего совпадения
        segment = template[match_start:vm.start()]
        match_end = line.find(segment, match_start)

        if match_end == -1:
            logging.error(f"Segment {segment} not found in line.")
            raise ValueError(f"Segment {segment} not found in line.")

        match_start = match_end + len(segment)
        # Извлечение значений после совпадения
        if match_start < len(line):
            next_segment = template[vm.end():]
            next_pos = line.find(next_segment, match_start)
            value = line[match_start:next_pos] if next_pos != -1 else line[match_start:]
            result[var_name] = value.strip()
        else:
            result[var_name] = None

    return result


def main():
    parser = argparse.ArgumentParser(description="DWH Release Builder")
    parser.add_argument('--config', '-c', required=True, help="Путь к release_config.yaml")
    args = parser.parse_args()

    config_full = load_yaml(args.config)
    if 'release_config' not in config_full or 'blocks' not in config_full:
        log("release_config и blocks должны быть в корне yaml", "ERROR")
        sys.exit(1)
    release_config = config_full['release_config']
    blocks_conf = config_full['blocks']

    # Контекст для env_subst
    context = dict(release_config)
    context["release_config"] = release_config

    # Подставим переменные окружения во всех полях конфигурации блоков
    blocks_conf = env_subst(blocks_conf, context)
    block_patterns = get_block_patterns(blocks_conf)

    input_release_path = release_config['input_release_path']
    options = release_config.get("options", {})
    encoding = options.get("encoding", "utf-8")

    # Чтение строк исходного SQL-релиза
    lines = read_file_lines(input_release_path, encoding)
    n = len(lines)
    i = 0

    while i < n:
        matched = False
        for i, line in enumerate(lines):
            print(line)
            logging.info(f"Processing line {i}: {line.strip()}")
            for pat in block_patterns:
                try:
                    match_vars = parse_template(pat['begin'].pattern, line.strip())
                    if match_vars:
                        matched = True
                        block_conf = pat['block_conf']
                        block_name = block_conf['name']
                        content_lines = []
                        i += 1
                        # Ищем конец блока
                        while i < n and not parse_template(pat['end'].template, lines[i].strip()):
                            content_lines.append(lines[i])
                            i += 1
                        # Пропускаем END метку, если есть
                        if i < n and parse_template(pat['end'].template, lines[i].strip()):
                            i += 1
                        content = "\n".join(content_lines).strip()

                        # Формируем параметры для путей
                        base_params = {
                            "base": release_config.get("output_base_path", ""),
                            "dag_folder": release_config.get("dag_output_path", ""),
                        }
                        params = dict(base_params)
                        params.update(match_vars)

                        # Подставляем object_type_map если нужно
                        if "object_type_map" in block_conf and "object_type" in match_vars:
                            ot_map = block_conf["object_type_map"]
                            ot_raw = match_vars["object_type"].strip().lower()
                            params["object_type"] = ot_map.get(ot_raw, ot_raw)

                        # Формируем путь к итоговому файлу
                        output_path_template = block_conf['output_path']['template']
                        # Собираем значения для параметров шаблона
                        output_path_param_values = []
                        for pname in block_conf['output_path']['params']:
                            output_path_param_values.append(params.get(pname, ""))
                        # Делаем render
                        output_path = output_path_template
                        for pname, pval in zip(block_conf['output_path']['params'], output_path_param_values):
                            output_path = output_path.replace("{" + pname + "}", pval)
                        output_path = output_path.replace("//", "/")
                        ensure_dirs(output_path)

                        # Собираем header/footer, если есть
                        header = ""
                        header_template_path = block_conf.get("header_template_path")
                        if header_template_path:
                            header = apply_template(header_template_path, params)
                        footer = ""
                        footer_template_path = block_conf.get("footer_template_path")
                        if footer_template_path:
                            footer = apply_template(footer_template_path, params)

                        # Записываем результат в файл
                        with open(output_path, "w", encoding=encoding) as f:
                            if header:
                                f.write(header + "\n")
                            f.write(content + "\n")
                            if footer:
                                f.write("\n" + footer)
                        log(f"{block_name}  {output_path}", "INFO")
                        break
                    if not matched:
                        i += 1
                    print(match_vars)
                except ValueError as e:
                    logging.warning(str(e))


if __name__ == "__main__":
    main()