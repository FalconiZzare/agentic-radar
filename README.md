## Getting Started

First, install Python [3.12.8](https://www.python.org/downloads/release/python-3130/)

Then, to create the virtual environment, run:

```bash
python -m venv .venv  
```

After that, to install the dependencies, run:

```bash
pip3 install -r requirements.txt
# or
pip install -r requirements.txt
```

Finally, open a terminal window in the project root and run:

```bash
.venv/Scripts/activate
```

Now that the virtual environment is ready and running, you can now run:

```bash
python main.py
```

To check if the server is up and running:
```bash
GET: /
```

To check if the agentic-radar subprocess is working
```bash
GET: /version
```

To scan an agentic workflow for vulnerability
```bash
POST: /scan
```
|   Field   | Type | Accepted |
|:---------:|:----:|:--------:|
|   file    | file |   JSON   |
| framework | str  |   n8n    |