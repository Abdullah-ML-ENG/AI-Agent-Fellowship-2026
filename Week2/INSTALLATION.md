# Installation Guide - Week 2

This guide will walk you through setting up the Week 2 environment for the AI Agent Fellowship 2026.

## Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.8+** - Download from [python.org](https://www.python.org/)
- **pip** - Usually comes with Python
- **git** - For version control

Verify installations:
```bash
python --version
pip --version
git --version
```

## Step-by-Step Installation

### 1. Clone or Navigate to the Repository

If you haven't cloned the repository yet:
```bash
git clone https://github.com/Abdullah-ML-ENG/AI-Agent-Fellowship-2026.git
cd AI-Agent-Fellowship-2026/Week2
```

Or if you already have it:
```bash
cd AI-Agent-Fellowship-2026/Week2
```

### 2. Create a Virtual Environment

It's highly recommended to use a virtual environment to avoid dependency conflicts.

**On macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**On Windows (Command Prompt):**
```bash
python -m venv venv
venv\Scripts\activate
```

**On Windows (PowerShell):**
```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

You should see `(venv)` in your terminal prompt when activated.

### 3. Upgrade pip

Ensure you have the latest version of pip:
```bash
pip install --upgrade pip
```

### 4. Install Dependencies

Install all required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

This will install:
- AI/LLM libraries (OpenAI, Anthropic)
- Agent frameworks (LangChain, CrewAI)
- Data processing tools (pandas, numpy)
- Testing utilities (pytest)
- And more...

### 5. Set Up Environment Variables

Create a `.env` file in the Week2 directory for API keys and configuration:

```bash
touch .env
```

**Note:** Never commit the `.env` file to version control. Add it to `.gitignore` if not already there.

**Example `.env` structure:**
```
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 6. Verify Installation

Test that everything is installed correctly:

```bash
# Test Python
python -c "import sys; print(f'Python {sys.version}')"

# Test key dependencies
python -c "import openai; print(f'OpenAI: {openai.__version__}')"
python -c "import langchain; print(f'LangChain installed')"
python -c "import pandas; print(f'Pandas: {pandas.__version__}')"
```

Or run the verification script (if available):
```bash
python verify_installation.py
```

## Troubleshooting

### Issue: `venv` activation doesn't work

**Windows PowerShell:** If you get an execution policy error:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: `pip install` fails with permission denied

Try:
```bash
pip install --user -r requirements.txt
```

Or ensure your virtual environment is activated.

### Issue: Module not found after installation

1. Verify virtual environment is activated: `which python` should show the venv path
2. Reinstall requirements:
   ```bash
   pip install --force-reinstall -r requirements.txt
   ```

### Issue: API key errors at runtime

Ensure your `.env` file is properly configured and the keys are valid:
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY', 'NOT SET'))"
```

## Deactivating Virtual Environment

When you're done working, deactivate the virtual environment:
```bash
deactivate
```

## Updating Dependencies

To update all packages to their latest compatible versions:
```bash
pip install --upgrade -r requirements.txt
```

To check for outdated packages:
```bash
pip list --outdated
```

## Next Steps

After installation:
1. Review the [README.md](./README.md) for project overview
2. Explore the implementations in this directory
3. Review any project-specific documentation
4. Start developing and experimenting with agent implementations

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the main repository [README](../README.md)
- Consult the [AI Agent Fellowship 2026](https://github.com/Abdullah-ML-ENG/AI-Agent-Fellowship-2026) project page

---
**Last Updated:** July 14, 2026
