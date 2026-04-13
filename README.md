[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/aignostics/tme-studio/blob/main/LICENSE)
[![CI](https://github.com/aignostics/tme-studio/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/aignostics/tme-studio/actions/workflows/ci-cd.yml)
[![Dependabot](https://img.shields.io/badge/dependabot-active-brightgreen?style=flat-square&logo=dependabot)](https://github.com/aignostics/tme-studio/security/dependabot)
[![Renovate enabled](https://img.shields.io/badge/renovate-enabled-brightgreen.svg)](https://github.com/aignostics/tme-studio/issues?q=is%3Aissue%20state%3Aopen%20Dependency%20Dashboard)
[![codecov](https://codecov.io/gh/aignostics/tme-studio/graph/badge.svg)](https://codecov.io/gh/aignostics/tme-studio)
[![Ruff](https://img.shields.io/badge/style-Ruff-blue?color=D6FF65)](https://github.com/aignostics/tme-studio/blob/main/noxfile.py)
[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-orange.json)](https://github.com/aignostics/foundry-python)
[![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/notebooks/nb_xdh9jVAHevMspKQ11WX4LJ/app)

# 🎨 TME Studio

Welcome to TME Studio! This readme explains the content of TME Studio, and the dataset it is built on:  [OpenTME](https://huggingface.co/datasets/Aignostics/OpenTME).

New to TME Studio? Want to try out the notebooks right away without any set up required? [Try out our interactive demo via molab](https://molab.marimo.io/notebooks/nb_zKsoeRqM31YZ9srzLAcZ1x/app). 
Make sure you have [access to OpenTME on Hugging Face](#hugging-face-access), then open the link and start exploring. 


Already familiar with TME Studio? You want to edit the notebooks and adapt them to your needs? 
You can choose to either 
* follow the setup instructions to [fork the notebooks into your molab workspace](#edit-notebooks-in-molab) OR
* follow the setup instructions to [run the notebooks locally](#edit-notebooks-locally) .

## Content
- [What is OpenTME?](#what-is-opentme)
- [What is TME Studio?](#what-is-tme-studio)
- [Setup instructions](#setup-instructions)


## What is OpenTME?
OpenTME is an open-source project by [Aignostics](https://aignostics.com) that provides academic researchers with pre-computed quantitative TME (Tumor Micro-Environment) features across H&E-stained Whole-Slide Images (WSIs) from The Cancer Genome Atlas (TCGA). It provides comprehensive spatial outputs characterizing key cellular and tissue components of the TME, including cancer cells, immune cells, and stromal features, as well as their relationships within the tissue architecture.

All outputs were generated using [Atlas H&E-TME](https://www.aignostics.com/products/he-tme-profiling-product), Aignostics' AI-powered computational pathology application for the automated identification and quantification of TME features in FFPE H&E-stained tissue samples. 


## What is TME Studio?

TME Studio contains a set of tutorials and example notebooks to help you explore [OpenTME](https://huggingface.co/datasets/Aignostics/OpenTME). TME Studio is provided as an entry point into OpenTME, and intended to accelerate research output from the OpenTME data.


### Content

The structure of the notebooks in this repo looks as follows:

```
tme_studio/
|-- src/
    |-- aignostics_tme_studio/
        |-- notebooks/
            |-- demo/
            |-- examples/
            |-- tutorials/
```


* **Tutorials:** Step-by-step notebooks to help users get started, covering foundational tasks such as loading and exploring the dataset, and providing a guide through the OpenTME features.

* **Examples:** Concise notebooks demonstrating specific analysis types, such as tumor immune phenotype classification and Kaplan–Meier survival plots. The examples showcase what types of analyses might be possible with OpenTME. Note that these are examples that may be used as a starting point for your own analysis.

* **Demo:** contains a demo notebook showcasing all features in OpenTME and some example analyses.

If you are unfamiliar with the OpenTME dataset, we suggest beginning at `src/aignostics_tme_studio/notebooks/tutorials/1_getting_started.py`. To get a feeling for all the different features you can find in OpenTME, have a look at the demo notebook `src/aignostics_tme_studio/notebooks/demo/demo.py`.


# Setup instructions 
## Hugging Face access
However you decide to run the notebooks, you will need to get access to OpenTME on Hugging Face 🤗. 
### Creating an access token
1. Make sure you have a Hugging Face account. If you don't have one, you can create one for free at [hf.co/join](https://hf.co/join).
2. Get access to the dataset by going to https://huggingface.co/datasets/Aignostics/OpenTME and clicking "Access"

> Note: You will eceive an email from Hugging Face as soon as your access request has been reviewed. This may take a few working days.

> Note: No need to download the dataset! The tutorials will show you how to access the dataset via the Hugging Face API. 

3. Create an access token by going to https://huggingface.co/settings/tokens

### Authenticating with your token
You can now use your token in two ways:
1. Enter it in the designated box for it inside each notebook. This is how you authenticate when you are running a notebook in molab. You will have to repeat this action each time you open a notebook. 
2. Log in via the Hugging Face CLI (only when running notebooks locally). In this case your token will be stored and you won't have to enter your token each time you open a notebook.

    1. Download the [Hugging Face CLI](https://huggingface.co/docs/huggingface_hub/en/guides/cli)
    2. Log into hugging face by calling
```
hf auth login
```
and log in with your access token.

> Note: If you invalidated your token, you can force logging in with a new token by calling `hf auth login \--force`


## Edit notebooks in molab 
To edit your own copy of these TME Studio notebooks in molab, do the following:
1. Open the notebook in github.
2. Replace github.com by molab.marimo.io/github.com in the notebook URL to open it in molab.
3. Click the "fork" button.
> Note: to run your own copy of the notebooks in molab you will need to create a molab account. 


## Edit notebooks locally
To run the TME Studio notebooks on your local machine, follow these installation instructions:

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [mise](https://mise.jdx.dev/) | latest | Task runner & tool version manager |
| Git | latest | Version control |

### Installing mise

[mise](https://mise.jdx.dev/) manages tool versions (Python, uv, trivy, etc.) and runs all project tasks. Install it first:

```shell
curl https://mise.run | sh

# activate mise in the current shell and add to shell config for future sessions
echo 'eval "$(mise activate --shims bash)"' >> ~/.bashrc
source ~/.bashrc
```

For .zsh users:
```shell
echo 'eval "$(mise activate --shims zsh)"' >> ~/.zshrc
source ~/.zshrc
```

For other shells, see [mise installation docs](https://mise.jdx.dev/installing-mise.html).


Verify the installation:

```shell
mise --version

# Check path - mise shims should be first in the PATH to ensure the correct tool versions are used
echo $PATH

which uv # Path should contain the `mise/shims/uv` shim, not a system-wide uv installation; please do not install uv in the same directory as `mise` to avoid conflicts
```


### Cloning the repository

Authenticate with GitHub using the Github CLI to clone the repository:

```shell
gh auth login

gh repo clone aignostics/tme-studio

cd tme-studio
mise trust
gh auth setup-git
```


### Installation

```shell
# Install all dev dependencies, pre-commit hooks, and keyring tooling
mise run install

# Verify everything works
mise run lint

# List all existing mise tasks
mise tasks
```

This runs `uv sync --all-extras` to install all dependencies, then sets up pre-commit hooks.

### Starting Marimo
You are now ready to explore the notebooks! 🎨

Start marimo by calling the following command and opening the URL in your browser:
```
uv run marimo edit
```
Use the marimo UI opened in your browser to navigate to the notebooks. 

Alternatively, you can run
```
uv run marimo edit path/to/notebook.py
```
to open a specific notebook directly.  



## Further Reading

- [Security policy](SECURITY.md) - Documentation of security checks, tools, and principles
- [Release notes](https://github.com/aignostics/tme-studio/releases) - Complete log of improvements and changes
- [Attributions](ATTRIBUTIONS.md) - Open source projects this project builds upon
