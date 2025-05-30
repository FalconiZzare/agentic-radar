## Getting Started

First, install Python [3.12.8](https://www.python.org/downloads/release/python-3130/)

Then to create the virtual environment, run:

```bash
python -m venv .venv  
```

After that, to install the dependencies, run:

```bash
pip3 install -r requirements.txt
# or
pip install -r requirements.txt
```

Finally open a terminal window in project root and run:

```bash
.venv/Scripts/activate
```

Now that the virtual environment is ready and running, you can now run:

```bash
python main.py
```

This will start the pipeline and show you the prompt result.

Update the datasets in given formats to enrich the knowledge base.

If your GPU supports CUDA, then make sure to download and install CUDA Toolkits.