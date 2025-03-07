# domain-tx (or domainterm, not sure yet)

This repo is for a CLI tool used to find new product names. It uses a combination of LLMs and other techniques to find new product names that are not already taken as domain names and products.

## How it works (Step by Step)

1.  **Base Words** The tool watches a file of initial base words for changes and updates the queues
2.  **Synonyms** The tool searches for synonyms of the base words.
3.  **Translations** The tool searches for translations of the base words
4.  **Webification** The tool creates webified versions of all words including translated words and synonyms.
    - The tool uses a local LLM to create a list of web 2.0 style SaaS names by removing a single vowel each time.
5.  **Domain Availability** The tool checks if the word is available as a domain name. (.com only)
    - A DNS check is done first to cut down on WHOIS lookups
6.  ~~**Search Results** The tool checks if the word is being used as a product name in the tech industry using a Brave Search~~
7.  **Rating** The tool uses a local LLM to rate the word based on the above results
