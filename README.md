# An Open-source Tool for Fact Verification

## Overview
open-source solution designed to automate the process of verifying factuality. It provides a comprehensive pipeline for dissecting long texts into individual claims, assessing their worthiness for verification, generating queries for evidence search, crawling for evidence, and ultimately verifying the claims. This tool is especially useful for journalists, researchers, and anyone interested in the factuality of information. To stay updated, please subscribe to our newsletter at [our website](https://www.librai.tech/) or join us on [Discord](https://discord.gg/ssxtFVbDdT)!

## Quick Start

uv pip install dotenv psycopg2-binary tiktoken playwright playwright-stealth pandas opencv-python openai nltk httpx Flask bs4 backoff
uv pip install anthropic PyYAML

### Clone the repository and navigate to the project directory
```bash
git clone https://github.com/johntday/OpenFactVerification.git
cd OpenFactVerification
```

### Installation with poetry (option 1)
1. Install Poetry by following it [installation guideline](https://python-poetry.org/docs/).
2. Install all dependencies by running:
```bash
poetry install
```

### Installation with pip (option 2)
1. Create a Python environment at version 3.9 or newer and activate it.

2. Navigate to the project directory and install the required packages:
```bash
pip install -r requirements.txt
```

### Configure API keys

You can choose to export essential api key to the environment

- Example: Export essential api key to the environment
```bash
export SERPER_API_KEY=... # this is required in evidence retrieval if serper being used
export OPENAI_API_KEY=... # this is required in all tasks
```

Alternatively, you configure API keys via a YAML file, see [user guide](docs/user_guide.md) for more details.

## Usage

The main interface of Loki fact-checker located in `factcheck/__init__.py`, which contains the `check_response` method. This method integrates the complete fact verification pipeline, where each functionality is encapsulated in its class as described in the Features section.

#### Used as a Library

```python
from factcheck import FactCheck

factcheck_instance = FactCheck()

# Example text
text = "Your text here"

# Run the fact-check pipeline
# TODO: fix me
results = factcheck_instance.check_response(text)
print(results)
```

#### Used as a Web App
```bash
python webapp.py --api_config demo_data/api_config.yaml
```

#### Multimodal Usage

```bash
# String
python -m factcheck --modal string --input "MBZUAI is the first AI university in the world"
# Text
python -m factcheck --modal text --input demo_data/text.txt
# Speech
python -m factcheck --modal speech --input demo_data/speech.mp3
# Image
python -m factcheck --modal image --input demo_data/image.webp
# Video
python -m factcheck --modal video --input demo_data/video.m4v
```

