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

## Prerequisites

You must have the following installed.

- A locally available LLM with an OPENAI compatible API at http://localhost:1234
- Node.js 18+
- A Cloudflare API token and account ID. Rename the `.env.example` file to `.env` and fill in the values.

## Running the tool

To run the tool, you must first create a file called `base-words.txt` in the root of the project.

You can run the command `pnpm dev run` to start the tool. It can take quite some time to finish.

## Other Commands

### `pnpm dev run social [name]`

To run the `social` command you must have the tool, [sherlock](https://github.com/sherlock-project/sherlock) installed locally.

This command will check if the provided name is available on several major social media platforms. [Bitbucket, GitHub, GitLab, and LinkedIn] are used to check for availability.

## License

MIT License

Copyright 2025 Chris Griffing

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
