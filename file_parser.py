#!/usr/bin/env python3

import argparse
import yaml
import os
import re
import sys

class Colors:
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def log_success(msg):
    print(f"{Colors.OKGREEN}[OK]{Colors.ENDC} {msg}")

def log_warn(msg):
    print(f"{Colors.WARNING}[WARN]{Colors.ENDC} {msg}")

def log_error(msg):
    print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {msg}")

def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_dirs(filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

def parse_blocks_from_release(release_lines, block_patterns):
    blocks = []
    i = 0
    while i < len(release_lines):
        for pat in block_patterns:
            beg_pat = re.compile(pat['begin'])
            m = beg_pat.match(release_lines[i])
            if m:
                params = {}
                if 'params' in pat:
                    for idx, pname in enumerate(pat['params'], 1):
                        params[pname] = m.group(idx)
                content = []
                i += 1
                end_pat = re.compile(pat['end'])
                while i < len(release_lines) and not end_pat.match(release_lines[i]):
                    content.append(release_lines[i])
                    i += 1
                blocks.append({
                    "type": pat["name"],
                    "params": params,
                    "content": '\n'.join(content).strip()
                })
                if i < len(release_lines) and end_pat.match(release_lines[i]):
                    i += 1
                break
        else:
            i += 1
    return blocks

def object_type_from_ddl(ddl_content):
    m = re.search(r'create\s+(table|view|materialized\s+view|fuction|procedure)\s+', ddl_content, re.IGNORECASE)
    if m:
        return m.group(1).replace(" ", "_").lower()
    return "unknown"

def parse_object_dot(obj):
    parts = obj.split('.')
    if len(parts) != 2:
        return 'unknown', obj
    return parts[0], parts[1]

def render_path(pattern, **kwargs):
    for k, v in kwargs.items():
        pattern = pattern.replace(f"{{{k}}}", str(v))
    return pattern

def main():
    parser = argparse.ArgumentParser(description="DWH Release Parser")
    parser.add_argument('--config', '-c', required=True, help="Путь к dwh_config.yaml")
    args = parser.parse_args()

    config = load_yaml(args.config)
    options = config.get("options", {})

    block_patterns_path = options.get("block_patterns_path")
    if not block_patterns_path:
        log_error("В dwh_config.yaml не найден ключ options.block_patterns_path")
        sys.exit(1)

    release_path = config.get("input_release_path")
    if not release_path:
        log_error("В dwh_config.yaml не найден ключ input_release_path")
        sys.exit(1)

    block_patterns = load_yaml(block_patterns_path)["block_patterns"]

    with open(release_path, encoding=options.get("encoding", "utf-8")) as f:
        lines = [line.rstrip('\n') for line in f]

    output_base = config.get("output_base_path", "./khd/ddl")
    dag_folder = config.get("dag_output_path", "./dags")
    obj_map = config.get("object_type_map", {})

    patterns = config["patterns"]
    parse_block_types = set(config["parse_blocks"])

    blocks = parse_blocks_from_release(lines, block_patterns)

    for block in blocks:
        btype = block["type"]
        params = block["params"]
        content = block["content"]

        if btype not in parse_block_types:
            continue

        if btype == "ddl":
            schema, object_name = parse_object_dot(params["object"])
            object_type = object_type_from_ddl(content)
            subfolder = obj_map.get(object_type, object_type)
            out_path = render_path(
                patterns["ddl_path"],
                base=output_base,
                schema=schema,
                object_type=subfolder,
                object_name=object_name,
            )
        elif btype == "model":

            schema, object_name = parse_object_dot(params["object"])
            dag_id = params["dag_id"]
            out_path = render_path(
                patterns["model_path"],
                base=output_base,
                dag_id=dag_id,
                schema=schema,
                object_name=object_name,
            )
        elif btype == "loader":
            schema, object_name = parse_object_dot(params["object"])
            dag_id = params.get("dag_id", "unknown")
            out_path = render_path(
                patterns["loader_path"],
                base=output_base,
                dag_id=dag_id,
                schema=schema,
                object_name=object_name,
            )
        elif btype == "dag":
            dag_id = params.get("dag_id", "unknown")
            out_path = render_path(
                patterns["dag_python_file"],
                dag_folder=dag_folder,
                dag_id=dag_id
            )
        else:
            continue

        ensure_dirs(out_path)
        with open(out_path, "w", encoding=options.get("encoding", "utf-8")) as outf:
            outf.write(content.strip() + '\n')
        log_success(f"{btype} → {out_path}")

if __name__ == "__main__":
    main()
