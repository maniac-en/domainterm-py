#!/usr/bin/env node

import * as yargs from "yargs";
import OpenAI from "openai";
import fs from "fs/promises";
import { spawnSync } from "child_process";
import { db } from "./data/db";

import { getTranslations } from "./utils/translate";
import { checkDomainAvailability } from "./utils/domains";
import {
  checkSearchResults,
  getSynonyms,
  getWebifiedWords,
  rateName,
} from "./utils/llms";
import { Translation, TranslationWithWebifiedWords } from "./types";

(yargs as any)
  .scriptName("domain-tx-cli")
  // .usage("$0 get [args]")
  .command(
    "run",
    "run the daemons to scan for domains",
    (yargs) => {
      yargs.option("min", {
        alias: "min-length",
        demandOption: true,
        default: 3,
        describe: "The minimum length of the names to consider",
        type: "number",
      });

      yargs.option("max", {
        alias: "max-length",
        demandOption: true,
        default: 10,
        describe: "The maximum length of the names to consider",
        type: "number",
      });
    },
    async function (argv) {
      try {
        const minLength = argv.min;
        const maxLength = argv.max;

        console.log({ minLength, maxLength });

        // Load the database
        await db.read();

        const localBaseWordCache: Record<string, boolean> = {};

        const translationQueue: Set<string> = new Set();
        const webificationQueue: Set<Translation> = new Set();
        const synonymQueue: Set<string> = new Set();
        const whoisQueue: Set<string> = new Set();
        const searchQueue: Set<string> = new Set();
        const ratingQueue: Set<string> = new Set();

        // Watch the domain file for changes
        setInterval(async () => {
          try {
            const baseWordsFileExists = await fs
              .stat("base-words.txt")
              .catch(() => {});

            if (!baseWordsFileExists) {
              console.log(
                "base-words.txt not found. Exiting. Create it with a line separate list of words to translate."
              );
              process.exit(0);
              return;
            }

            const baseWordsFileContents = await fs.readFile(
              "base-words.txt",
              "utf8"
            );
            const baseWords = baseWordsFileContents.split("\n");

            // for each base word, add it to the queue
            baseWords.forEach(async (baseWord) => {
              if (!localBaseWordCache[baseWord]) {
                localBaseWordCache[baseWord] = true;
                translationQueue.add(baseWord);
                whoisQueue.add(baseWord);
                synonymQueue.add(baseWord);
              }
            });
          } catch (error) {
            console.error(error);
          }
        }, 3000);

        setInterval(async () => {
          const translationQueueArray = Array.from(translationQueue);

          let word = translationQueueArray.shift();

          if (!word) {
            return;
          }

          translationQueue.delete(word);

          let translations = db.chain.get("translationCache").get(word).value();

          if (!translations) {
            // console.log("Getting translations for", word);
            translations = await getTranslations(word);
            db.data.translationCache[word] = translations;
            await db.write();
          }

          translations.forEach((translation) => {
            const { cleaned } = translation.translation;
            webificationQueue.add(translation);
            if (cleaned) {
              whoisQueue.add(cleaned);
            }
          });
        }, 3000);

        setInterval(async () => {
          try {
            const synonymQueueArray = Array.from(synonymQueue);

            const word = synonymQueueArray.shift();

            if (!word) {
              return;
            }

            synonymQueue.delete(word);

            let synonyms = db.chain.get("synonymsCache").get(word).value();

            if (!synonyms) {
              console.log("Getting synonyms for", word);
              synonyms = await getSynonyms(word);
              db.data.synonymsCache[word] = synonyms;
              await db.write();
            }

            synonyms.filter(Boolean).forEach((_word) => {
              whoisQueue.add(_word);
              webificationQueue.add({
                word: _word,
                language: { name: "English", code: "en" },
                translation: {
                  raw: _word,
                  cleaned: _word,
                },
              });
            });
          } catch (error) {
            console.error("Error getting synonyms", error);
          }
        }, 1000);

        setInterval(async () => {
          try {
            const webificationQueueArray = Array.from(webificationQueue);

            const word = webificationQueueArray.shift();

            if (!word) {
              return;
            }

            webificationQueue.delete(word);

            let webifiedTranslations = db.chain
              .get("webifiedCache")
              .get(word.translation.cleaned)
              .value();

            let webifiedWords = webifiedTranslations?.webifiedWords;

            if (!webifiedWords) {
              // console.log(
              //   "Getting webified words for",
              //   word.translation.cleaned
              // );
              webifiedWords = await getWebifiedWords(word);
              db.data.webifiedCache[word.translation.cleaned] = {
                ...word,
                webifiedWords,
              } as TranslationWithWebifiedWords;
              await db.write();
            }

            [word.translation.cleaned, ...webifiedWords]
              .filter(Boolean)
              .forEach((_word) => {
                whoisQueue.add(_word);
              });
          } catch (error) {
            console.error("Error webifying word", error);
          }
        }, 1000);

        setInterval(async () => {
          try {
            const whoisQueueArray = Array.from(whoisQueue);

            const word = whoisQueueArray.shift();

            // console.log("word in whois queue", word);

            if (!word) {
              // console.log("whoisQueue is empty", whoisQueue);
              return;
            }

            whoisQueue.delete(word);

            if (word.length < minLength || word.length > maxLength) {
              return;
            }

            let availability = db.chain.get("whoisCache").get(word).value();

            // console.log("Cached availability for", word, "is", availability);

            if (availability === undefined) {
              // console.log("Checking whois availability for", word);
              const availability = await checkDomainAvailability(word);

              if (word === "wallet") {
                // console.log(availability);
              }

              // await db.chain.get("whoisCache").set(word, availability);
              db.data.whoisCache[word] = availability;
              await db.write();
            }

            if (availability) {
              // searchQueue.add(word);
              ratingQueue.add(word);
            }
          } catch (error) {
            console.error("Error checking whois availability", error);
          }
        }, 500);

        // TODO: figure out how to make search more reliable
        // setInterval(async () => {
        //   try {
        //     const searchQueueArray = Array.from(searchQueue);

        //     const word = searchQueueArray.shift();

        //     if (!word) {
        //       // console.log("searchQueue is empty", searchQueue);
        //       return;
        //     }

        //     searchQueue.delete(word);

        //     let evaluation = db.chain
        //       .get("searchEvaluationCache")
        //       .get(word)
        //       .value();

        //     // console.log("Cached evaluation for", word, "is", evaluation);

        //     if (evaluation === undefined) {
        //       const evaluation = await checkSearchResults(word);

        //       if (word === "miksah") {
        //         console.log({ evaluation });
        //       }

        //       db.data.searchEvaluationCache[word] = evaluation;
        //       await db.write();
        //     }
        //   } catch (error) {
        //     console.error("Error checking search availability", error);
        //   }
        // }, 30000);

        // TODO: figure out how to make rating more reliable. it seems to pick a lot of the same numbers
        setInterval(async () => {
          try {
            const ratingQueueArray = Array.from(ratingQueue);

            const word = ratingQueueArray.shift();

            if (!word) {
              // console.log("ratingQueue is empty", ratingQueue);
              return;
            }

            ratingQueue.delete(word);

            let rating = db.chain.get("ratingsCache").get(word).value();

            if (rating === undefined) {
              const rating = await rateName(word);

              db.data.ratingsCache[word] = rating;
              await db.write();
            }
          } catch (error) {
            console.error("Error rating name", error);
          }
        }, 300);

        setInterval(async () => {
          const translationQueueLength = Array.from(translationQueue).length;
          const webificationQueueLength = Array.from(webificationQueue).length;
          const synonymQueueLength = Array.from(synonymQueue).length;
          const whoisQueueLength = Array.from(whoisQueue).length;
          const searchQueueLength = Array.from(searchQueue).length;
          const ratingQueueLength = Array.from(ratingQueue).length;

          console.log(`
            
---Items in Queues---
Translations: ${translationQueueLength}
Synonyms: ${synonymQueueLength}
Webifications: ${webificationQueueLength}
Whois: ${whoisQueueLength}
Search: ${searchQueueLength}
Ratings: ${ratingQueueLength}
            
            `);

          if (
            translationQueueLength === 0 &&
            webificationQueueLength === 0 &&
            synonymQueueLength === 0 &&
            whoisQueueLength === 0 &&
            searchQueueLength === 0 &&
            ratingQueueLength === 0
          ) {
            //TODO: Print results
            process.exit(0);
          }
        }, 10000);
      } catch (error) {
        console.error(error);
      }
    }
  )

  .command(
    "social [name]",
    "show results from the current instance of the db file",
    (yargs) => {
      yargs.positional("name", {
        type: "string",
        required: true,
        describe: "the name to lookup",
      });
    },
    async function (argv) {
      try {
        const name = argv.name;

        const sherlockResult = spawnSync("sherlock", [
          "--output",
          "./social.txt",
          "--site",
          "GitHub",
          "--site",
          "GitLab",
          "--site",
          "Bitbucket",
          "--site",
          "LinkedIn",
          name,
        ]);

        if (sherlockResult.status !== 0) {
          console.error("Sherlock failed to run");
          console.log(sherlockResult.stderr.toString());
          process.exit(1);
        }

        const fileContents = await fs.readFile("social.txt", "utf8");

        if (fileContents.split("\n").filter(Boolean).length > 1) {
          console.error("Name seems taken on at least one platform");
          console.log(fileContents);
          process.exit(1);
        } else {
          console.log("Name seems available on all checked platforms");
        }
      } catch (error) {
        console.error(error);
      }
    }
  )
  .command(
    "results",
    "show results from the current instance of the db file",
    (yargs) => {},
    async function () {
      try {
        // Load the database
        await db.read();

        const ratings = db.chain.get("ratingsCache").value();

        const entries = Object.entries(ratings);

        entries.sort((a, b) => b[1] - a[1]);

        // console.log("Top 42: \n", entries.slice(0, 42));

        console.log("Entries", entries);
      } catch (error) {
        console.error(error);
      }
    }
  )
  .help().argv;

function printResults(db: any) {
  console.log("Printing results");
}
