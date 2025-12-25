<div align="center">
    <h1>【 Octopi Watch 】</h1>
    <h3></h3>
</div>

<div align="center"> 

![](https://img.shields.io/github/last-commit/FalconiZzare/octopi-watch?&style=for-the-badge&color=8ad7eb&logo=git&logoColor=D9E0EE&labelColor=1E202B)
![](https://img.shields.io/github/stars/FalconiZzare/octopi-watch?style=for-the-badge&logo=andela&color=86dbd7&logoColor=D9E0EE&labelColor=1E202B)
![](https://img.shields.io/github/repo-size/FalconiZzare/octopi-watch?color=86dbce&label=SIZE&logo=protondrive&style=for-the-badge&logoColor=D9E0EE&labelColor=1E202B)

</div>

## Getting Started

First, install Python [3.12.8](https://www.python.org/downloads/release/python-3130/) and [Agentic Radar](https://github.com/splx-ai/agentic-radar)

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
