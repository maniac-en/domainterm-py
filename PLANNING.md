Done:

- implement caching
- watch a file containing base words for changes and update the queues
- reorganize code to use daemons (long running intervals that pop items off their respective queues)
- search for translations of the base words
- create webified versions of all words including translated
- perform whois lookup
- add queue for doing search lookup
  - fetch("https://search.brave.com/search?q=kalita").then(response => response.text()).then((text) => console.log(text))
  - still unsure of how to do the search. Maybe an API or maybe even just scraping the google results page via playwright?
- add a queue for asking LLM to evaluate available domains
- add a queue for synonym lookups (local llm)

Pending:

- add a queue to perform social lookups
  - linkedin
  - github
  - gitlab
  - bitbucket
  - github org lookup via API
- create command to print results

Nice to have:

- switch to using 'debug' instead of console.log for debugging
- add a queue for npm package availability (maybe through a flag)
- add a queue for trademark lookup
- create command to clear the db

// Turn this into a blog post

- Intro
- About proficionym
- The inspiration for this tool (zustand, valtio, jotai all meaning "state" in other langs)
- What makes a good domain name and product name
  - things to check
- How I wanted to build it (TUI using ink)
- Abandoning ink
- The current state of the tool

aartra
