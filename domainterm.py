#!/usr/bin/env python3

import asyncio
import json
import os
import sys
import socket
import urllib.request
import urllib.parse
import urllib.error
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Optional

def load_env_file(filename=".env"):
    """Load environment variables from .env file"""
    env_vars = {}
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip('"\'')
        except Exception:
            pass  # Silently ignore .env file errors, as we handle it later!
    return env_vars

def check_required_env_vars(env_vars, required_vars):
    """Check if all required environment variables are present and non-empty"""
    missing_vars = []
    for var in required_vars:
        if not env_vars.get(var):
            missing_vars.append(var)

    if missing_vars:
        print("Error: Missing required environment variables in .env file:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease create a .env file with these variables set.")
        sys.exit(1)

# Load environment variables
env_vars = load_env_file()

# Required environment variables
REQUIRED_ENV_VARS = [
    "LLM_MODEL",
    "CLOUDFLARE_API_TOKEN",
    "CLOUDFLARE_ACCOUNT_ID"
]

# Check required variables
check_required_env_vars(env_vars, REQUIRED_ENV_VARS)

# Constants
LLM_BASE_URL = env_vars.get("LLM_BASE_URL", "http://127.0.0.1:1234/v1")
LLM_API_KEY = env_vars.get("LLM_API_KEY", "lm-studio")
LLM_MODEL = env_vars["LLM_MODEL"]
CLOUDFLARE_API_TOKEN = env_vars["CLOUDFLARE_API_TOKEN"]
CLOUDFLARE_ACCOUNT_ID = env_vars["CLOUDFLARE_ACCOUNT_ID"]
BASE_WORDS_FILE = "base-words.txt"
DB_FILE = "db.json"
LOG_DIR = "logs"

# Processing intervals (in seconds)
TRANSLATION_INTERVAL = 3.0
SYNONYM_INTERVAL = 1.0
WEBIFICATION_INTERVAL = 1.0
WHOIS_INTERVAL = 0.5
SEARCH_INTERVAL = 30.0
RATING_INTERVAL = 0.3
STATUS_INTERVAL = 10.0
BASE_WORDS_CHECK_INTERVAL = 3.0

# Language codes for translation
LANGUAGES = [
    {"name": "Abkhaz", "code": "ab"},
    {"name": "Acehnese", "code": "ace"},
    {"name": "Afrikaans", "code": "af"},
    {"name": "Albanian", "code": "sq"},
    {"name": "Amharic", "code": "am"},
    {"name": "Arabic", "code": "ar"},
    {"name": "Armenian", "code": "hy"},
    {"name": "Assamese", "code": "as"},
    {"name": "Aymara", "code": "ay"},
    {"name": "Azerbaijani", "code": "az"},
    {"name": "Bambara", "code": "bm"},
    {"name": "Basque", "code": "eu"},
    {"name": "Belarusian", "code": "be"},
    {"name": "Bengali", "code": "bn"},
    {"name": "Bhojpuri", "code": "bho"},
    {"name": "Bosnian", "code": "bs"},
    {"name": "Bulgarian", "code": "bg"},
    {"name": "Catalan", "code": "ca"},
    {"name": "Cebuano", "code": "ceb"},
    {"name": "Chinese (Simplified)", "code": "zh-CN"},
    {"name": "Chinese (Traditional)", "code": "zh-TW"},
    {"name": "Corsican", "code": "co"},
    {"name": "Croatian", "code": "hr"},
    {"name": "Czech", "code": "cs"},
    {"name": "Danish", "code": "da"},
    {"name": "Dutch", "code": "nl"},
    {"name": "English", "code": "en"},
    {"name": "Esperanto", "code": "eo"},
    {"name": "Estonian", "code": "et"},
    {"name": "Finnish", "code": "fi"},
    {"name": "French", "code": "fr"},
    {"name": "Frisian", "code": "fy"},
    {"name": "Galician", "code": "gl"},
    {"name": "Georgian", "code": "ka"},
    {"name": "German", "code": "de"},
    {"name": "Greek", "code": "el"},
    {"name": "Gujarati", "code": "gu"},
    {"name": "Haitian Creole", "code": "ht"},
    {"name": "Hausa", "code": "ha"},
    {"name": "Hawaiian", "code": "haw"},
    {"name": "Hebrew", "code": "iw"},
    {"name": "Hindi", "code": "hi"},
    {"name": "Hmong", "code": "hmn"},
    {"name": "Hungarian", "code": "hu"},
    {"name": "Icelandic", "code": "is"},
    {"name": "Igbo", "code": "ig"},
    {"name": "Indonesian", "code": "id"},
    {"name": "Irish", "code": "ga"},
    {"name": "Italian", "code": "it"},
    {"name": "Japanese", "code": "ja"},
    {"name": "Javanese", "code": "jw"},
    {"name": "Kannada", "code": "kn"},
    {"name": "Kazakh", "code": "kk"},
    {"name": "Khmer", "code": "km"},
    {"name": "Korean", "code": "ko"},
    {"name": "Kurdish", "code": "ku"},
    {"name": "Kyrgyz", "code": "ky"},
    {"name": "Lao", "code": "lo"},
    {"name": "Latin", "code": "la"},
    {"name": "Latvian", "code": "lv"},
    {"name": "Lithuanian", "code": "lt"},
    {"name": "Luxembourgish", "code": "lb"},
    {"name": "Macedonian", "code": "mk"},
    {"name": "Malagasy", "code": "mg"},
    {"name": "Malay", "code": "ms"},
    {"name": "Malayalam", "code": "ml"},
    {"name": "Maltese", "code": "mt"},
    {"name": "Maori", "code": "mi"},
    {"name": "Marathi", "code": "mr"},
    {"name": "Mongolian", "code": "mn"},
    {"name": "Myanmar (Burmese)", "code": "my"},
    {"name": "Nepali", "code": "ne"},
    {"name": "Norwegian", "code": "no"},
    {"name": "Odia (Oriya)", "code": "or"},
    {"name": "Pashto", "code": "ps"},
    {"name": "Persian", "code": "fa"},
    {"name": "Polish", "code": "pl"},
    {"name": "Portuguese", "code": "pt"},
    {"name": "Punjabi", "code": "pa"},
    {"name": "Romanian", "code": "ro"},
    {"name": "Russian", "code": "ru"},
    {"name": "Samoan", "code": "sm"},
    {"name": "Sanskrit", "code": "sa"},
    {"name": "Scots Gaelic", "code": "gd"},
    {"name": "Serbian", "code": "sr"},
    {"name": "Sesotho", "code": "st"},
    {"name": "Shona", "code": "sn"},
    {"name": "Sindhi", "code": "sd"},
    {"name": "Sinhala", "code": "si"},
    {"name": "Slovak", "code": "sk"},
    {"name": "Slovenian", "code": "sl"},
    {"name": "Somali", "code": "so"},
    {"name": "Spanish", "code": "es"},
    {"name": "Sundanese", "code": "su"},
    {"name": "Swahili", "code": "sw"},
    {"name": "Swedish", "code": "sv"},
    {"name": "Tajik", "code": "tg"},
    {"name": "Tamil", "code": "ta"},
    {"name": "Tatar", "code": "tt"},
    {"name": "Telugu", "code": "te"},
    {"name": "Thai", "code": "th"},
    {"name": "Turkish", "code": "tr"},
    {"name": "Turkmen", "code": "tk"},
    {"name": "Ukrainian", "code": "uk"},
    {"name": "Urdu", "code": "ur"},
    {"name": "Uyghur", "code": "ug"},
    {"name": "Uzbek", "code": "uz"},
    {"name": "Vietnamese", "code": "vi"},
    {"name": "Welsh", "code": "cy"},
    {"name": "Xhosa", "code": "xh"},
    {"name": "Yiddish", "code": "yi"},
    {"name": "Yoruba", "code": "yo"},
    {"name": "Zulu", "code": "zu"},
]

class Logger:
    def __init__(self, console_level="info"):
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(LOG_DIR, f"domainterm_{timestamp}.log")
        self.console_level = console_level
        self.level_priority = {"debug": 0, "info": 1, "error": 2}

    def log(self, level: str, message: str, show_console: bool = None, **kwargs):
        timestamp = datetime.now().isoformat()
        log_entry = f'time="{timestamp}" level={level} msg="{message}"'

        for key, value in kwargs.items():
            if isinstance(value, str):
                log_entry += f' {key}="{value}"'
            else:
                log_entry += f' {key}={value}'

        # Always log to file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

        # Console output logic
        if show_console is None:
            show_console = self.level_priority.get(level, 1) >= self.level_priority.get(self.console_level, 1)

        if show_console:
            print(log_entry)

    def info(self, message: str, show_console: bool = None, **kwargs):
        self.log("info", message, show_console, **kwargs)

    def error(self, message: str, show_console: bool = None, **kwargs):
        self.log("error", message, show_console, **kwargs)

    def debug(self, message: str, show_console: bool = None, **kwargs):
        self.log("debug", message, show_console, **kwargs)

logger = Logger()

class Database:
    def __init__(self, filename: str):
        self.filename = filename
        self.data = {
            "translation_cache": {},
            "webified_cache": {},
            "whois_cache": {},
            "search_evaluation_cache": {},
            "ratings_cache": {},
            "synonyms_cache": {},
            "npm_cache": {},
            "trademark_cache": {},
            "social_cache": {}
        }
        self.load()

    def load(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    self.data.update(saved_data)
                cache_stats = {key: len(cache) for key, cache in self.data.items()}
                logger.info("Database loaded", show_console=False, file=self.filename, **cache_stats)
        except Exception as e:
            logger.error("Failed to load database", error=str(e))

    def save(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save database", error=str(e))

def clean_word(word: str) -> str:
    """Clean word by removing non-alphabetic characters and converting to lowercase"""
    return re.sub(r'[^a-zA-Z]', '', word).lower()

def unidecode_simple(text: str) -> str:
    """Simple ASCII transliteration"""
    if not text:
        return ""

    # Basic character mappings
    char_map = {
        'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
        'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
        'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
        'ñ': 'n', 'ç': 'c',
        'ß': 'ss',
        'æ': 'ae', 'œ': 'oe',
    }

    result = ""
    for char in text.lower():
        if char in char_map:
            result += char_map[char]
        elif ord(char) < 128:  # ASCII
            result += char
        # Skip non-ASCII characters not in mapping

    return result

async def http_request(url: str, method: str = "GET", headers: Dict = None, data: bytes = None) -> Optional[Dict]:
    """Simple HTTP request function"""
    try:
        req = urllib.request.Request(url, data=data, method=method)

        if headers:
            for key, value in headers.items():
                req.add_header(key, value)

        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8')
            return json.loads(content)

    except Exception as e:
        logger.debug("HTTP request failed", url=url, error=str(e))
        return None

async def translate_word(word: str, language_code: str) -> Optional[Dict]:
    """Translate word using Google Translate"""
    try:
        encoded_word = urllib.parse.quote(word)
        url = f"https://translate.google.com/translate_a/single?client=gtx&sl=en&tl={language_code}&dt=t&q={encoded_word}"

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data

    except Exception as e:
        logger.debug("Translation failed", word=word, lang=language_code, error=str(e))
        return None

async def get_translations(word: str) -> List[Dict]:
    """Get translations for a word in multiple languages"""
    logger.info("Getting translations", show_console=False, word=word)
    translations = []
    successful_langs = []
    failed_langs = []

    for language in LANGUAGES:
        try:
            response = await translate_word(word, language["code"])
            if response and response[0] and response[0][0] and response[0][0][0]:
                translated_text = response[0][0][0]

                translation = {
                    "word": clean_word(unidecode_simple(word)),
                    "language": language,
                    "translation": {
                        "raw": translated_text,
                        "cleaned": clean_word(unidecode_simple(translated_text))
                    }
                }

                if translation["translation"]["cleaned"]:
                    translations.append(translation)
                    successful_langs.append(language["name"])
                    logger.debug("Translation success", show_console=False, word=word, lang=language["name"],
                               original=translated_text, cleaned=translation["translation"]["cleaned"])

        except Exception as e:
            failed_langs.append(language["name"])
            logger.debug("Translation error", show_console=False, word=word, lang=language["name"], error=str(e))
            continue

    logger.info("Translation complete", show_console=False, word=word, total_translations=len(translations),
               successful_languages=len(successful_langs), failed_languages=len(failed_langs))

    if successful_langs:
        logger.debug("Successful translations", show_console=False, word=word, languages=", ".join(successful_langs[:10]))

    return translations

async def llm_request(messages: List[Dict], response_format: Dict = None) -> Optional[str]:
    """Make request to local LLM"""
    try:
        payload = {
            "model": LLM_MODEL,
            "messages": messages
        }

        if response_format:
            payload["response_format"] = response_format

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}"
        }

        data = json.dumps(payload).encode('utf-8')
        response = await http_request(f"{LLM_BASE_URL}/chat/completions", "POST", headers, data)

        if response and "choices" in response and response["choices"]:
            content = response["choices"][0]["message"]["content"]
            logger.debug("LLM request successful", response_length=len(content) if content else 0)
            return content

        logger.error("LLM request failed", reason="no_choices_in_response")
        return None

    except Exception as e:
        logger.error("LLM request failed", error=str(e))
        return None

async def get_webified_words(translation: Dict) -> List[str]:
    """Generate webified versions of a word"""
    cleaned_word = translation["translation"]["cleaned"]
    logger.info("Webifying word", show_console=False, word=cleaned_word)

    messages = [{
        "role": "user",
        "content": f"""Convert the following word into a list of Web 2.0 style SaaS name by removing a single vowel each time. Return the output as a JS string array. If there is only one result make sure the array has only one element. Do not output any text other than the array

word: {cleaned_word}"""
    }]

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "webified",
            "strict": True,
            "schema": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }

    response = await llm_request(messages, response_format)

    if not response:
        logger.error("Webification failed", show_console=False, word=cleaned_word, reason="no_llm_response")
        return []

    try:
        webified_list = json.loads(response.lower())
        filtered_list = [w for w in webified_list if w and isinstance(w, str) and " " not in w]
        logger.info("Webification complete", show_console=False, word=cleaned_word,
                   generated_count=len(webified_list), filtered_count=len(filtered_list),
                   webified_words=", ".join(filtered_list[:10]))
        return filtered_list
    except Exception as e:
        logger.error("Webification parsing failed", word=cleaned_word, error=str(e), raw_response=response)
        return []

async def get_synonyms(word: str) -> List[str]:
    """Get synonyms for a word"""
    logger.info("Getting synonyms", show_console=False, word=word)

    messages = [{
        "role": "user",
        "content": f"""Find synonyms for the provided word. Provide at least 10 synonyms. Return the output as a JS string array. If there is only one result make sure the array has only one element. Do not output any text other than the array

word: {word}"""
    }]

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "synonyms",
            "strict": True,
            "schema": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }

    response = await llm_request(messages, response_format)

    if not response:
        logger.error("Synonym lookup failed", show_console=False, word=word, reason="no_llm_response")
        return []

    try:
        synonyms_list = json.loads(response.lower())
        filtered_list = [s for s in synonyms_list if s and isinstance(s, str) and " " not in s]
        logger.info("Synonym lookup complete", show_console=False, word=word,
                   generated_count=len(synonyms_list), filtered_count=len(filtered_list),
                   synonyms=", ".join(filtered_list[:10]))
        return filtered_list
    except Exception as e:
        logger.error("Synonym parsing failed", word=word, error=str(e), raw_response=response)
        return []

async def rate_name(word: str) -> float:
    """Rate a name for business potential"""
    logger.info("Rating name", show_console=False, word=word)

    messages = [{
        "role": "user",
        "content": f"""Given the following word, rate its potential for a good product/business name. This should include how easy it would be to pronounce for an english speaker and how easy it would be to spell. Output the rating as a number between 0 and 100 where 0 is bad and 100 is good.

word: {word}"""
    }]

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "rating",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {"rating": {"type": "number"}},
                "required": ["rating"]
            }
        }
    }

    response = await llm_request(messages, response_format)

    if not response:
        logger.error("Name rating failed", show_console=False, word=word, reason="no_llm_response")
        return -1

    try:
        rating_data = json.loads(response)
        rating = float(rating_data.get("rating", -1))
        logger.info("Name rating complete", show_console=False, word=word, rating=rating)
        return rating
    except Exception as e:
        logger.error("Rating parsing failed", word=word, error=str(e), raw_response=response)
        return -1

async def check_dns_availability(domain: str) -> bool:
    """Check if domain resolves via DNS"""
    try:
        socket.gethostbyname(domain)
        logger.debug("DNS check", domain=domain, result="taken", reason="resolves")
        return False  # Domain exists
    except socket.gaierror:
        logger.debug("DNS check", domain=domain, result="available", reason="no_resolution")
        return True  # Domain doesn't exist

async def check_whois_availability(domain: str) -> Optional[bool]:
    """Check domain availability using Cloudflare WHOIS API"""
    if not CLOUDFLARE_API_TOKEN or not CLOUDFLARE_ACCOUNT_ID:
        logger.error("WHOIS check skipped", domain=domain, reason="no_cloudflare_credentials")
        return None

    try:
        headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}
        url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/intel/whois?domain={domain}"

        logger.debug("WHOIS API request", domain=domain)
        response = await http_request(url, headers=headers)

        if not response:
            logger.error("WHOIS API request failed", domain=domain, reason="no_response")
            return None

        if not response.get("success"):
            errors = response.get("errors", [])
            logger.error("WHOIS API returned error", domain=domain, errors=errors)
            return None

        # Domain is available if not found in WHOIS
        found = response.get("result", {}).get("found", True)
        result = not found
        logger.info("WHOIS check complete", domain=domain, available=result, whois_found=found)
        return result

    except Exception as e:
        logger.error("WHOIS check failed", domain=domain, error=str(e))
        return None

async def check_domain_availability(word: str) -> Optional[bool]:
    """Check if domain is available using DNS and WHOIS"""
    if isinstance(word, list):
        word = "".join(word)

    domain = f"{word.replace(' ', '')}.com"
    logger.info("Checking domain availability", show_console=False, word=word, domain=domain)

    # First check DNS (faster)
    dns_available = await check_dns_availability(domain)
    if not dns_available:
        logger.info("Domain check complete", show_console=False, word=word, domain=domain,
                   available=False, method="dns", reason="domain_resolves")
        return False

    # Then check WHOIS for confirmation
    whois_result = await check_whois_availability(domain)
    logger.info("Domain check complete", show_console=False, word=word, domain=domain,
               available=whois_result, dns_available=True, whois_available=whois_result)
    return whois_result

async def check_search_results(word: str) -> Dict:
    """Check search results to determine if name is taken"""
    logger.info("Checking search results", word=word)

    try:
        # Get search results from Brave
        encoded_word = urllib.parse.quote(word)
        url = f"https://search.brave.com/search?q={encoded_word}"

        logger.debug("Fetching search results", word=word, search_url=url)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as response:
            search_results = response.read().decode('utf-8')

        logger.debug("Search results fetched", word=word, content_length=len(search_results))

        # Analyze with LLM
        messages = [{
            "role": "user",
            "content": f"""Given the following search results, determine if the word is a good product/business name or not. It is a bad name if there is an existing product or business by the same or similar name in the Tech/Software industry. Output the result as a json that looks like '{{"isAvailable": true, "confidence": 42}}' where true is replaced with the actual result of it being a good or bad name. true for good, false for bad. confidence is a rating between 0 and 100 where 0 is the lowest confidence and 100 is the highest confidence. Do not output any text other than the raw json. That means no markdown syntax.

word: {word}

search results: {search_results[:5000]}"""  # Limit search results length
        }]

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "rating",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "isAvailable": {"type": "boolean"},
                        "confidence": {"type": "number"}
                    },
                    "required": ["isAvailable", "confidence"]
                }
            }
        }

        response = await llm_request(messages, response_format)

        if response:
            result = json.loads(response)
            logger.info("Search evaluation complete", word=word,
                       available=result.get("isAvailable"),
                       confidence=result.get("confidence"))
            return result

        logger.error("Search evaluation failed", word=word, reason="no_llm_response")
        return {"isAvailable": False, "confidence": 0}

    except Exception as e:
        logger.error("Search check failed", word=word, error=str(e))
        return {"isAvailable": False, "confidence": 0}

async def check_npm_availability(word: str) -> bool:
    """Check if NPM package name is available"""
    logger.info("Checking NPM availability", word=word)

    try:
        url = f"https://registry.npmjs.org/{word}"
        req = urllib.request.Request(url)

        with urllib.request.urlopen(req, timeout=10) as response:
            available = response.status == 404
            logger.info("NPM check complete", word=word, available=available,
                       status_code=response.status)
            return available

    except urllib.error.HTTPError as e:
        available = e.code == 404
        logger.info("NPM check complete", word=word, available=available,
                   status_code=e.code)
        return available
    except Exception as e:
        logger.error("NPM check failed", word=word, error=str(e))
        return False  # Assume taken if error

async def check_social_availability(word: str) -> Dict[str, bool]:
    """Check social media availability using sherlock-like approach"""
    logger.info("Checking social media availability", word=word)

    social_platforms = {
        "github": f"https://github.com/{word}",
        "gitlab": f"https://gitlab.com/{word}",
        "twitter": f"https://twitter.com/{word}",
        "linkedin": f"https://linkedin.com/in/{word}",
    }

    availability = {}

    for platform, url in social_platforms.items():
        try:
            logger.debug("Checking social platform", word=word, platform=platform, url=url)
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                available = response.status == 404
                availability[platform] = available
                logger.debug("Social platform check", word=word, platform=platform,
                           available=available, status_code=response.status)
        except urllib.error.HTTPError as e:
            available = e.code == 404
            availability[platform] = available
            logger.debug("Social platform check", word=word, platform=platform,
                        available=available, status_code=e.code)
        except Exception as e:
            availability[platform] = False
            logger.debug("Social platform check failed", word=word, platform=platform, error=str(e))

    available_count = sum(1 for avail in availability.values() if avail)
    logger.info("Social media check complete", word=word,
               platforms_available=available_count, total_platforms=len(availability),
               **{f"{k}_available": v for k, v in availability.items()})

    return availability

class DomainTerm:
    def __init__(self, min_length: int = 3, max_length: int = 10):
        self.min_length = min_length
        self.max_length = max_length
        self.db = Database(DB_FILE)
        self.base_word_cache = set()

        # Queues
        self.translation_queue = set()
        self.webification_queue = set()
        self.synonym_queue = set()
        self.whois_queue = set()
        self.search_queue = set()
        self.rating_queue = set()
        self.npm_queue = set()
        self.social_queue = set()

        self.running = True

    async def load_base_words(self):
        """Load base words from file"""
        if not os.path.exists(BASE_WORDS_FILE):
            logger.error(f"Base words file not found: {BASE_WORDS_FILE}")
            logger.info("Create base-words.txt with a line-separated list of words to translate.")
            sys.exit(1)

        try:
            with open(BASE_WORDS_FILE, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]

            new_words = set(words) - self.base_word_cache

            for word in new_words:
                self.base_word_cache.add(word)
                self.translation_queue.add(word)
                self.whois_queue.add(word)
                self.synonym_queue.add(word)
                logger.info("Added base word to queues", word=word)

            if new_words:
                logger.info("Base words file processed", total_words=len(words),
                           new_words=len(new_words), cached_words=len(self.base_word_cache))

        except Exception as e:
            logger.error("Failed to load base words", error=str(e))

    async def process_translations(self):
        """Process translation queue"""
        while self.running:
            if not self.translation_queue:
                await asyncio.sleep(TRANSLATION_INTERVAL)
                continue

            word = self.translation_queue.pop()
            logger.info("Processing translation", show_console=False, word=word, queue_size=len(self.translation_queue))

            if word in self.db.data["translation_cache"]:
                translations = self.db.data["translation_cache"][word]
                logger.info("Translation cache hit", show_console=False, word=word, cached_translations=len(translations))
            else:
                translations = await get_translations(word)
                self.db.data["translation_cache"][word] = translations
                self.db.save()
                logger.info("Translation cached", show_console=False, word=word, new_translations=len(translations))

            added_to_queues = 0
            for translation in translations:
                cleaned = translation["translation"]["cleaned"]
                self.webification_queue.add(json.dumps(translation))
                if cleaned:
                    self.whois_queue.add(cleaned)
                    added_to_queues += 1

            logger.info("Translation processing complete", show_console=False, word=word,
                       words_added_to_queues=added_to_queues)
            await asyncio.sleep(TRANSLATION_INTERVAL)

    async def process_synonyms(self):
        """Process synonym queue"""
        while self.running:
            if not self.synonym_queue:
                await asyncio.sleep(SYNONYM_INTERVAL)
                continue

            word = self.synonym_queue.pop()
            logger.info("Processing synonyms", word=word, queue_size=len(self.synonym_queue))

            if word in self.db.data["synonyms_cache"]:
                synonyms = self.db.data["synonyms_cache"][word]
                logger.info("Synonym cache hit", word=word, cached_synonyms=len(synonyms))
            else:
                synonyms = await get_synonyms(word)
                self.db.data["synonyms_cache"][word] = synonyms
                self.db.save()
                logger.info("Synonyms cached", word=word, new_synonyms=len(synonyms))

            added_to_queues = 0
            for synonym in synonyms:
                if synonym:
                    self.whois_queue.add(synonym)
                    # Create translation object for webification
                    translation = {
                        "word": synonym,
                        "language": {"name": "English", "code": "en"},
                        "translation": {"raw": synonym, "cleaned": synonym}
                    }
                    self.webification_queue.add(json.dumps(translation))
                    added_to_queues += 1

            logger.info("Synonym processing complete", word=word,
                       synonyms_added_to_queues=added_to_queues)
            await asyncio.sleep(SYNONYM_INTERVAL)

    async def process_webifications(self):
        """Process webification queue"""
        while self.running:
            if not self.webification_queue:
                await asyncio.sleep(WEBIFICATION_INTERVAL)
                continue

            translation_json = self.webification_queue.pop()
            translation = json.loads(translation_json)
            cleaned_word = translation["translation"]["cleaned"]

            logger.info("Processing webification", word=cleaned_word,
                       queue_size=len(self.webification_queue))

            if cleaned_word in self.db.data["webified_cache"]:
                webified_data = self.db.data["webified_cache"][cleaned_word]
                webified_words = webified_data.get("webifiedWords", [])
                logger.info("Webification cache hit", word=cleaned_word,
                           cached_webified_words=len(webified_words))
            else:
                webified_words = await get_webified_words(translation)
                self.db.data["webified_cache"][cleaned_word] = {
                    **translation,
                    "webifiedWords": webified_words
                }
                self.db.save()
                logger.info("Webification cached", word=cleaned_word,
                           new_webified_words=len(webified_words))

            words_to_check = [cleaned_word] + webified_words
            added_to_whois = 0
            for word in words_to_check:
                if word:
                    self.whois_queue.add(word)
                    added_to_whois += 1

            logger.info("Webification processing complete", original_word=cleaned_word,
                       words_added_to_whois=added_to_whois)
            await asyncio.sleep(WEBIFICATION_INTERVAL)

    async def process_whois(self):
        """Process WHOIS queue"""
        while self.running:
            if not self.whois_queue:
                await asyncio.sleep(WHOIS_INTERVAL)
                continue

            word = self.whois_queue.pop()
            logger.info("Processing WHOIS", show_console=False, word=word, queue_size=len(self.whois_queue))

            if len(word) < self.min_length or len(word) > self.max_length:
                logger.debug("WHOIS skipped", show_console=False, word=word, reason="length_filter",
                           length=len(word), min_length=self.min_length, max_length=self.max_length)
                continue

            if word in self.db.data["whois_cache"]:
                availability = self.db.data["whois_cache"][word]
                logger.info("WHOIS cache hit", show_console=False, word=word, cached_result=availability)
            else:
                availability = await check_domain_availability(word)
                self.db.data["whois_cache"][word] = availability
                self.db.save()

            if availability:
                self.search_queue.add(word)
                self.rating_queue.add(word)
                self.npm_queue.add(word)
                self.social_queue.add(word)
                logger.info("Domain available - added to all queues", show_console=False, word=word)
            else:
                logger.info("Domain unavailable - skipping further checks", show_console=False, word=word)

            await asyncio.sleep(WHOIS_INTERVAL)

    async def process_search(self):
        """Process search evaluation queue"""
        while self.running:
            if not self.search_queue:
                await asyncio.sleep(SEARCH_INTERVAL)
                continue

            word = self.search_queue.pop()
            logger.info("Processing search evaluation", word=word, queue_size=len(self.search_queue))

            if word in self.db.data["search_evaluation_cache"]:
                logger.info("Search evaluation cache hit", word=word)
                continue

            evaluation = await check_search_results(word)
            self.db.data["search_evaluation_cache"][word] = evaluation
            self.db.save()

            await asyncio.sleep(SEARCH_INTERVAL)

    async def process_ratings(self):
        """Process rating queue"""
        while self.running:
            if not self.rating_queue:
                await asyncio.sleep(RATING_INTERVAL)
                continue

            word = self.rating_queue.pop()
            logger.info("Processing rating", word=word, queue_size=len(self.rating_queue))

            if word in self.db.data["ratings_cache"]:
                rating = self.db.data["ratings_cache"][word]
                logger.info("Rating cache hit", word=word, cached_rating=rating)
                continue

            rating = await rate_name(word)
            self.db.data["ratings_cache"][word] = rating
            self.db.save()

            await asyncio.sleep(RATING_INTERVAL)

    async def process_npm(self):
        """Process NPM availability queue"""
        while self.running:
            if not self.npm_queue:
                await asyncio.sleep(1.0)
                continue

            word = self.npm_queue.pop()
            logger.info("Processing NPM check", word=word, queue_size=len(self.npm_queue))

            if word in self.db.data["npm_cache"]:
                availability = self.db.data["npm_cache"][word]
                logger.info("NPM cache hit", word=word, cached_result=availability)
                continue

            availability = await check_npm_availability(word)
            self.db.data["npm_cache"][word] = availability
            self.db.save()

            await asyncio.sleep(1.0)

    async def process_social(self):
        """Process social media availability queue"""
        while self.running:
            if not self.social_queue:
                await asyncio.sleep(2.0)
                continue

            word = self.social_queue.pop()
            logger.info("Processing social media check", word=word, queue_size=len(self.social_queue))

            if word in self.db.data["social_cache"]:
                availability = self.db.data["social_cache"][word]
                available_count = sum(1 for avail in availability.values() if avail)
                logger.info("Social media cache hit", word=word,
                           platforms_available=available_count)
                continue

            availability = await check_social_availability(word)
            self.db.data["social_cache"][word] = availability
            self.db.save()

            await asyncio.sleep(2.0)

    async def status_reporter(self):
        """Report queue status"""
        while self.running:
            queue_sizes = {
                "translations": len(self.translation_queue),
                "synonyms": len(self.synonym_queue),
                "webifications": len(self.webification_queue),
                "whois": len(self.whois_queue),
                "search": len(self.search_queue),
                "ratings": len(self.rating_queue),
                "npm": len(self.npm_queue),
                "social": len(self.social_queue),
            }

            # Get cache statistics (file only)
            cache_stats = {}
            for cache_name, cache_data in self.db.data.items():
                if isinstance(cache_data, dict):
                    cache_stats[f"{cache_name}_cached"] = len(cache_data)

            # Count available domains
            available_domains = 0
            rated_domains = 0
            for word, available in self.db.data.get("whois_cache", {}).items():
                if available:
                    available_domains += 1
                    if word in self.db.data.get("ratings_cache", {}):
                        rated_domains += 1

            # Detailed logging to file
            logger.info("Status report", show_console=False,
                       **queue_sizes,
                       **cache_stats,
                       available_domains=available_domains,
                       rated_domains=rated_domains)

            # Simple console status
            total_queue_items = sum(queue_sizes.values())
            if total_queue_items > 0:
                print(f"Processing... {total_queue_items} items in queues | {available_domains} domains available | {rated_domains} rated")
            else:
                print(f"Monitoring... {available_domains} domains found, {rated_domains} rated")

            await asyncio.sleep(STATUS_INTERVAL)

    async def base_words_monitor(self):
        """Monitor base words file for changes"""
        while self.running:
            await self.load_base_words()
            await asyncio.sleep(BASE_WORDS_CHECK_INTERVAL)

    async def run(self):
        """Run the domain term finder"""
        logger.info("Starting DomainTerm", min_length=self.min_length, max_length=self.max_length)

        # Initial load of base words
        await self.load_base_words()

        # Start all processing tasks
        tasks = [
            self.base_words_monitor(),
            self.process_translations(),
            self.process_synonyms(),
            self.process_webifications(),
            self.process_whois(),
            self.process_search(),
            self.process_ratings(),
            self.process_npm(),
            self.process_social(),
            self.status_reporter(),
        ]

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Stopping DomainTerm")
            self.running = False

    def show_results(self):
        """Show current results"""
        logger.info("Showing results")

        ratings = self.db.data.get("ratings_cache", {})
        whois = self.db.data.get("whois_cache", {})
        npm = self.db.data.get("npm_cache", {})
        social = self.db.data.get("social_cache", {})
        search_eval = self.db.data.get("search_evaluation_cache", {})

        # Filter for available domains with ratings
        available_domains = []

        for word, rating in ratings.items():
            if (whois.get(word) and  # Domain available
                isinstance(rating, (int, float)) and rating > 0):

                search_data = search_eval.get(word, {})
                social_data = social.get(word, {})
                social_count = sum(1 for available in social_data.values() if available) if social_data else 0

                entry = {
                    "word": word,
                    "rating": rating,
                    "domain_available": whois.get(word, False),
                    "npm_available": npm.get(word, False),
                    "social_available": social_count,
                    "search_available": search_data.get("isAvailable", None),
                    "search_confidence": search_data.get("confidence", None),
                }
                available_domains.append(entry)

        # Sort by rating
        available_domains.sort(key=lambda x: x["rating"], reverse=True)

        print("\n=== TOP AVAILABLE DOMAINS ===")
        for i, entry in enumerate(available_domains[:50], 1):
            search_info = ""
            if entry["search_available"] is not None:
                search_info = f" | Search: {'✓' if entry['search_available'] else '✗'} ({entry['search_confidence']:.0f}%)"

            print(f"{i:2d}. {entry['word']:15s} | Rating: {entry['rating']:5.1f} | "
                  f"NPM: {'✓' if entry['npm_available'] else '✗'} | "
                  f"Social: {entry['social_available']}/4{search_info}")

        print(f"\nTotal available domains: {len(available_domains)}")

        # Show cache statistics
        cache_stats = {}
        for cache_name, cache_data in self.db.data.items():
            if isinstance(cache_data, dict):
                cache_stats[cache_name] = len(cache_data)

        print("\n=== CACHE STATISTICS ===")
        for cache_name, count in cache_stats.items():
            print(f"{cache_name}: {count} entries")

async def check_social_command(name: str):
    """Check social media availability for a specific name"""
    logger.info("Checking social availability", name=name)

    try:
        # Use subprocess to call sherlock if available
        result = subprocess.run([
            "sherlock", "--output", "./social.txt",
            "--site", "GitHub", "--site", "GitLab",
            "--site", "Bitbucket", "--site", "LinkedIn",
            name
        ], capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            if os.path.exists("social.txt"):
                with open("social.txt", 'r', encoding='utf-8') as f:
                    content = f.read()

                if len(content.strip().split('\n')) > 1:
                    print("Name seems taken on at least one platform:")
                    print(content)
                    return False
                else:
                    print("Name seems available on all checked platforms")
                    return True
        else:
            # Fallback to our own implementation
            availability = await check_social_availability(name)
            available_count = sum(1 for avail in availability.values() if avail)
            total_count = len(availability)

            print(f"Social media availability for '{name}':")
            for platform, available in availability.items():
                status = "✓ Available" if available else "✗ Taken"
                print(f"  {platform:10s}: {status}")

            print(f"\nSummary: {available_count}/{total_count} platforms available")
            return available_count == total_count

    except subprocess.TimeoutExpired:
        logger.error("Sherlock command timed out")
        return False
    except FileNotFoundError:
        logger.info("Sherlock not found, using built-in social checker")
        # Use our implementation
        availability = await check_social_availability(name)
        available_count = sum(1 for avail in availability.values() if avail)
        total_count = len(availability)

        print(f"Social media availability for '{name}':")
        for platform, available in availability.items():
            status = "✓ Available" if available else "✗ Taken"
            print(f"  {platform:10s}: {status}")

        print(f"\nSummary: {available_count}/{total_count} platforms available")
        return available_count == total_count

def main():
    import argparse

    parser = argparse.ArgumentParser(description="DomainTerm - An intelligent domain name discovery tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the domain scanner")
    run_parser.add_argument("--min", "--min-length", type=int, default=3,
                           help="Minimum length of names to consider")
    run_parser.add_argument("--max", "--max-length", type=int, default=10,
                           help="Maximum length of names to consider")

    # Results command
    subparsers.add_parser("results", help="Show current results")

    # Social command
    social_parser = subparsers.add_parser("social", help="Check social media availability")
    social_parser.add_argument("name", help="Name to check")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "run":
        domainterm = DomainTerm(args.min, args.max)
        try:
            asyncio.run(domainterm.run())
        except KeyboardInterrupt:
            logger.info("Stopped by user")

    elif args.command == "results":
        domainterm = DomainTerm()
        domainterm.show_results()

    elif args.command == "social":
        try:
            available = asyncio.run(check_social_command(args.name))
            sys.exit(0 if available else 1)
        except KeyboardInterrupt:
            logger.info("Stopped by user")
            sys.exit(1)

if __name__ == "__main__":
    main()
