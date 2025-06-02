# DomainTerm-Py

A Python rewrite of [Chris Griffing's DomainTerm](https://github.com/cmgriffing/domainterm) by [maniac-en](https://github.com/maniac-en) - an intelligent domain name discovery tool that finds available domain names using AI translation, synonyms, and "webification" techniques.

## Table of Contents

- [Why This Python Rewrite?](#why-this-python-rewrite)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Quick Setup](#quick-setup)
- [Usage](#usage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Credits & Inspiration](#credits--inspiration)
- [License](#license)

## Why This Python Rewrite?

- **Zero Dependencies**: Uses only Python standard library
- **Cross-Platform**: Works on Windows, macOS, Linux
- **Better Logging**: Detailed file logging with minimal console output

## How It Works

1. **Input**: Provide base words (like "payment", "invoice", "wallet")
2. **Translation**: Translates words into 100+ languages using Google Translate
3. **Synonyms**: AI generates synonyms for each base word
4. **Webification**: AI creates "Web 2.0" style names (removing vowels: "payment" → "pymnt")
5. **Domain Check**: Tests .com availability via DNS + Cloudflare WHOIS
6. **Additional Checks**: NPM packages, social media handles, AI rating
7. **Results**: Ranked list of available, brandable domain names

## Prerequisites

- **Python 3.7+**
- **Local LLM**: [LM Studio](https://lmstudio.ai/) with OpenAI-compatible API
- **Cloudflare Account**: For domain availability checking
- **Sherlock** (Optional): For enhanced social media checking
  ```bash
  pip install sherlock-project
  ```

## Quick Setup

### 1. Clone Repository
```bash
git clone https://github.com/maniac-en/domainterm-py
cd domainterm-py
```

### 2. LLM Setup
1. Install [LM Studio](https://lmstudio.ai/)
2. Download model: `mistralai/mistral-nemo-instruct-2407`
3. Start local server (default: `http://127.0.0.1:1234`)

### 3. Cloudflare API Setup

**API Token:**
1. Visit [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Create Custom Token with `Intel:Read` permissions for all accounts
3. [Official documentation](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/)

**Account ID:**
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Find "Account ID" in right sidebar (main dashboard or any domain page)

### 4. Configuration
```bash
cp env.example .env
# Edit .env with your values
```

Required `.env` variables:
```env
LLM_MODEL=mistralai/mistral-nemo-instruct-2407
CLOUDFLARE_API_TOKEN=your_token_here
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
```

### 5. Create Word List
Create `base-words.txt`:
```
payment
invoice
wallet
reminder
```

## Usage

```bash
# Start domain finder
python domainterm.py run

# Custom length limits
python domainterm.py run --min 4 --max 8

# View results
python domainterm.py results

# Check social media availability
python domainterm.py social mycompanyname
```

Example results:
```
=== TOP AVAILABLE DOMAINS ===
 1. pymnt           | Rating:  87.2 | NPM: ✓ | Social: 3/4
 2. invce           | Rating:  82.1 | NPM: ✓ | Social: 4/4
 3. wllt            | Rating:  79.8 | NPM: ✗ | Social: 2/4
```

## Configuration

Key settings in script constants:
```python
TRANSLATION_INTERVAL = 3.0    # Translation processing speed
WHOIS_INTERVAL = 0.5          # Domain checking speed
RATING_INTERVAL = 0.3         # AI rating speed
```

## Troubleshooting

**Script won't start:** Check `.env` has required variables and LLM is running

**No translations:** Google Translate rate-limiting - increase `TRANSLATION_INTERVAL`

**Domain checks failing:** Verify Cloudflare token permissions and Account ID

**LLM errors:** Ensure local server is running and model supports JSON mode

## Credits & Inspiration

This project is a Python rewrite of the original [DomainTerm](https://github.com/cmgriffing/domainterm) created by Chris Griffing. The original concept, methodology, and core algorithms are his brilliant work.

🙏 **Full credit goes to Chris Griffing** for the innovative approach of using:
- Multi-language translation for domain discovery
- AI-powered synonym generation
- "Web 2.0" style word transformation
- Comprehensive availability checking

**Support Chris:**
- ⭐ Star his [original repo](https://github.com/cmgriffing/domainterm)
- 📺 Follow him on [Twitch](https://www.twitch.tv/cmgriffing)

## License

MIT License

Copyright 2025 Chris Griffing (Original - [DomainTerm](https://github.com/cmgriffing/domainterm)) <br>
Copyright 2025 Shivam Mehta (Python Rewrite - [DomainTerm-Py](https://github.com/maniac-en/domainterm-py))

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
