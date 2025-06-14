#!/usr/bin/env python3

import argparse
import colorama
import yaml
import os
import re
import sys

from logger import log
from typing import List, Dict, Any, Optional, Pattern


class BlockPattern:
    def __init__(self, name: str, begin: str, end: str, params: Optional[List[str]] = None):
        self.name = name
        self.begin_pattern: Pattern = re.compile(begin)
        self.end_pattern: Pattern = re.compile(end)
        self.params = params or []


    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        return cls(
            name=d["name"],
            begin=d["begin"],
            end=d["end"],
            params=d.get("params")
        )


def build_block_patterns(patterns_conf: List[Dict[str, Any]]) -> List[BlockPattern]:
    return [BlockPattern.from_dict(p) for p in patterns_conf]


def parse_blocks_from_release(release_lines: List[str], block_patterns: List[BlockPattern]) -> List[Dict[str, Any]]:
    blocks = []
    i = 0
    n = len(release_lines)

    while i < n:
        matched = False
        for pat in block_patterns:
            m = pat.begin_pattern.match(release_lines[i])
            if m:
                params = {}
                for idx, pname in enumerate(pat.params, 1):
                    params[pname] = m.group(idx)
                content_lines = []
                i += 1
                while i < n and not pat.end_pattern.match(release_lines[i]):
                    content_lines.append(release_lines[i])
                    i += 1
                blocks.append({
                    "type": pat.name,
                    "params": params,
                    "content": '\n'.join(content_lines).strip()
                })
                # перепрыгиваем конец блока если встретили
                if i < n and pat.end_pattern.match(release_lines[i]):
                    i += 1
                matched = True
                break
        if not matched:
            i += 1
    return blocks


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs(filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)



def object_type_from_ddl(ddl_content):
    m = re.search(r'create\s+(table|external\s+ table|writable\s+ external\s+ table|view|materialized\s+view|fuction|procedure)\s+',  ddl_content.replace("or replace", ''), re.IGNORECASE)
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
        log("В dwh_config.yaml не найден ключ options.block_patterns_path","ERROR")
        sys.exit(1)

    release_path = config.get("input_release_path")
    if not release_path:
        log("В dwh_config.yaml не найден ключ input_release_path","ERROR")
        sys.exit(1)

    raw_patterns = load_yaml(block_patterns_path).get("block_patterns", [])
    block_patterns = build_block_patterns(raw_patterns)

    lines = read_file_lines(release_path, options.get("encoding", "utf-8"))
    blocks = parse_blocks_from_release(lines, block_patterns)

    output_base = config.get("output_base_path", "./output")
    dag_folder = config.get("dag_output_path", "./output")
    obj_map = config.get("object_type_map", {})

    patterns = config["patterns"]
    parse_block_types = set(config["parse_blocks"])

    for block in blocks:
        btype = block.get("type")
        params = block.get("params", {})
        content = block.get("content", "")

        if btype not in parse_block_types:
            continue

        out_path = resolve_output_path(btype, params, content, patterns, output_base, dag_folder, obj_map)
        if not out_path:
            continue

        ensure_dirs(out_path)
        write_file(out_path, content.strip() + '\n', options.get("encoding", "utf-8"))

        if "unknown" in out_path:
            log(f"{btype} → {out_path} Проверьте корректность кода создания объекта!","WARNING")
        else:
            log(f"{btype} → {out_path}")


def read_file_lines(path, encoding):
    with open(path, encoding=encoding) as f:
        return [line.rstrip('\n') for line in f]


def write_file(path, content, encoding):
    with open(path, "w", encoding=encoding) as outf:
        outf.write(content)


def resolve_output_path(btype, params, content, patterns, output_base, dag_folder, obj_map):
    if btype == "ddl":
        schema, object_name = parse_object_dot(params["object"])
        object_type = object_type_from_ddl(content)
        subfolder = obj_map.get(object_type, object_type)
        return render_path(
            patterns["ddl_path"],
            base=output_base,
            schema=schema,
            object_type=subfolder,
            object_name=object_name,
        )
    elif btype == "model":
        schema, object_name = parse_object_dot(params["object"])
        dag_id = params["dag_id"]
        return render_path(
            patterns["model_path"],
            base=output_base,
            dag_id=dag_id,
            schema=schema,
            object_name=object_name,
        )
    elif btype == "loader":
        schema, object_name = parse_object_dot(params["object"])
        dag_id = params.get("dag_id", "unknown")
        return render_path(
            patterns["loader_path"],
            base=output_base,
            dag_id=dag_id.upper(),
            schema=schema,
            object_name=object_name,
        )
    elif btype == "dag":
        dag_id = params.get("dag_id", "unknown")
        return render_path(
            patterns["dag_python_file"],
            dag_folder=dag_folder,
            dag_id=dag_id.upper()
        )
    return None


if __name__ == "__main__":
    main()

