import os
import ast
import re
import json


class MCPSCanner:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.results = {
            "is_mcp_repo": False,
            "language": None,
            "tools": [],
            "prompts": [],
            "resources": [],
            "resource_templates": []
        }

    def scan(self):
        self._check_dependencies()

        if self.results["language"] == "python":
            self._scan_python_files()
        elif self.results["language"] in ["javascript", "typescript"]:
            self._scan_js_files()

        return self.results

    def _check_dependencies(self):
        for root, _, files in os.walk(self.repo_path):
            # Check Python
            if "requirements.txt" in files or "pyproject.toml" in files:
                content_parts = []
                if "requirements.txt" in files:
                    try:
                        with open(os.path.join(root, "requirements.txt"), 'r', errors='ignore') as f:
                            content_parts.append(f.read())
                    except:
                        pass

                if "pyproject.toml" in files:
                    try:
                        with open(os.path.join(root, "pyproject.toml"), 'r', errors='ignore') as f:
                            content_parts.append(f.read())
                    except:
                        pass

                full_content = "\n".join(content_parts)
                if "mcp" in full_content or "fastmcp" in full_content:
                    self.results["is_mcp_repo"] = True
                    self.results["language"] = "python"
                    return

            # Check JS/TS
            if "package.json" in files:
                try:
                    with open(os.path.join(root, "package.json"), 'r', errors='ignore') as f:
                        data = json.load(f)
                        deps = json.dumps(data.get("dependencies", {}) or {})
                        dev_deps = json.dumps(data.get("devDependencies", {}) or {})
                        if "@modelcontextprotocol/sdk" in deps or "@modelcontextprotocol/sdk" in dev_deps:
                            self.results["is_mcp_repo"] = True
                            self.results["language"] = "typescript" if any(f.endswith(".ts") for f in files) else "javascript"
                            return
                except:
                    pass

    def _scan_python_files(self):
        """Parses Python AST to find tools, prompts, resources, and resource templates."""
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            tree = ast.parse(f.read())

                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                for decorator in node.decorator_list:
                                    # 1. UNWRAP DECORATOR
                                    decorator_args = []
                                    decorator_keywords = {}

                                    if isinstance(decorator, ast.Call):
                                        func = decorator.func
                                        decorator_args = decorator.args
                                        for k in decorator.keywords:
                                            if isinstance(k.value, ast.Constant):
                                                decorator_keywords[k.arg] = k.value.value
                                    else:
                                        func = decorator

                                    # 2. IDENTIFY TYPE
                                    attr_name = ""
                                    if isinstance(func, ast.Attribute):
                                        attr_name = func.attr
                                    elif isinstance(func, ast.Name):
                                        attr_name = func.id

                                    # 3. EXTRACT METADATA
                                    docstring = ast.get_docstring(node)
                                    item_name = node.name
                                    description = docstring.strip() if docstring else "No description"
                                    if "description" in decorator_keywords:
                                        description = decorator_keywords["description"]

                                    # --- TOOL ---
                                    if attr_name == "tool":
                                        if "name" in decorator_keywords:
                                            item_name = decorator_keywords["name"]
                                        self.results["tools"].append({
                                            "name": item_name,
                                            "description": description,
                                            "file": file
                                        })

                                    # --- RESOURCE / TEMPLATE ---
                                    elif attr_name == "resource":
                                        uri_pattern = item_name
                                        if decorator_args and isinstance(decorator_args[0], ast.Constant):
                                            uri_pattern = decorator_args[0].value

                                        item_data = {
                                            "uri": uri_pattern,
                                            "name": item_name,
                                            "description": description,
                                            "file": file
                                        }

                                        # If URI contains { }, it's a template
                                        if "{" in uri_pattern and "}" in uri_pattern:
                                            self.results["resource_templates"].append(item_data)
                                        else:
                                            self.results["resources"].append(item_data)

                                    # --- PROMPT ---
                                    elif attr_name == "prompt":
                                        if "name" in decorator_keywords:
                                            item_name = decorator_keywords["name"]
                                        self.results["prompts"].append({
                                            "name": item_name,
                                            "description": description,
                                            "file": file
                                        })

                    except Exception:
                        continue

    def _scan_js_files(self):
        """Uses Regex to find patterns in JS/TS"""

        # Tools
        tool_pattern = re.compile(
            r'\.tool\s*\(\s*["\']([^"\']+)["\']\s*,\s*(?:["\']([^"\']+)["\']|{[^}]*description:\s*["\']([^"\']+)["\'])',
            re.MULTILINE | re.DOTALL
        )

        # Resources (captures URI)
        resource_pattern = re.compile(
            r'\.resource\s*\(\s*["\']([^"\']+)["\']',
            re.MULTILINE | re.DOTALL
        )

        # Prompts
        prompt_pattern = re.compile(
            r'\.prompt\s*\(\s*["\']([^"\']+)["\']\s*,\s*(?:["\']([^"\']+)["\']|{[^}]*description:\s*["\']([^"\']+)["\'])',
            re.MULTILINE | re.DOTALL
        )

        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith((".js", ".ts")):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()

                            # Tools
                            for match in tool_pattern.findall(content):
                                desc = match[1] if match[1] else match[2]
                                self.results["tools"].append({
                                    "name": match[0],
                                    "description": desc,
                                    "file": file
                                })

                            # Resources & Templates
                            for match in resource_pattern.findall(content):
                                uri = match
                                item = {
                                    "uri": uri,
                                    "name": "Unknown (Regex Limit)",
                                    "description": "Detected via regex",
                                    "file": file
                                }
                                # Check for { } to distinguish template
                                if "{" in uri and "}" in uri:
                                    self.results["resource_templates"].append(item)
                                else:
                                    self.results["resources"].append(item)

                            # Prompts
                            for match in prompt_pattern.findall(content):
                                desc = match[1] if match[1] else match[2]
                                self.results["prompts"].append({
                                    "name": match[0],
                                    "description": desc,
                                    "file": file
                                })

                    except Exception:
                        continue


# --- RUNNING THE SCANNER ---
repo = "../tmp/gitlab-mcp"

if os.path.exists(repo):
    scanner = MCPSCanner(repo)
    report = scanner.scan()

    print(f"IS MCP Server: {report['is_mcp_repo']}")
    print(f"Language: {report['language']}")
    print("-" * 40)

    print(f"TOOLS ({len(report['tools'])}):")
    for t in report['tools']:
        print(f" - {t['name']}")

    print(f"\nRESOURCES (Static) ({len(report['resources'])}):")
    for r in report['resources']:
        print(f" - {r['uri']}")

    print(f"\nRESOURCE TEMPLATES (Dynamic) ({len(report['resource_templates'])}):")
    for rt in report['resource_templates']:
        print(f" - {rt['uri']}")

    print(f"\nPROMPTS ({len(report['prompts'])}):")
    for p in report['prompts']:
        print(f" - {p['name']}")

else:
    print("Repo path does not exist")