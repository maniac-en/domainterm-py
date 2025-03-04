#!/usr/bin/env node

import dotenv from "dotenv";
dotenv.config();

import * as yargs from "yargs";
import unidecode from "unidecode";
import OpenAI from "openai";
import dns from "dns";
import fs from "fs/promises";
import { db } from "./data/db";

import { translate } from "./utils/translate";
import { languages } from "./utils/languages";
import { Translation, TranslationWithWebifiedWords } from "./types";
import { render } from "ink";

const { CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID } = process.env;

const openai = new OpenAI({
  // Using LMStudio locally
  baseURL: "http://localhost:1234/v1",
  // WARNING: This is a fake API key. Do not use in production.
  apiKey: "sk-9q3f1s3d3s3d3s3d3s3d3s3d3s3d3s3d",
});

(yargs as any)
  .scriptName("domain-tx-cli")
  .usage("$0 get [args]")
  .command(
    "run",
    "run the daemons to scan for domains",
    (yargs) => {
      // yargs.positional("word", {
      //   type: "string",
      //   default: "guardian",
      //   describe: "the word to translate",
      // });
    },
    async function (argv) {
      try {
        // Load the database
        await db.read();

        const localBaseWordCache: Record<string, boolean> = {};

        const translationQueue: Set<string> = new Set();
        const webificationQueue: Set<Translation> = new Set();
        const whoisQueue: Set<string> = new Set();
        const searchQueue: string[] = [];
        const ratingQueue: string[] = [];

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
            console.log("Getting translations for", word);
            translations = await getTranslations(word);
            db.data.translationCache[word] = translations;
            await db.write();
          }

          translations.forEach((translation) => {
            webificationQueue.add(translation);
            if (translation.translation.cleaned) {
              whoisQueue.add(translation.translation.cleaned);
            }
          });
        }, 3000);

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
              console.log(
                "Getting webified words for",
                word.translation.cleaned
              );
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

            console.log("word in whois queue", word);

            if (!word) {
              console.log("whoisQueue is empty", whoisQueue);
              return;
            }

            whoisQueue.delete(word);

            let availability = db.chain.get("whoisCache").get(word).value();

            console.log("Cached availability for", word, "is", availability);

            if (availability === undefined) {
              console.log("Checking whois availability for", word);
              const availability = await checkDomainAvailability(word);

              if (word === "wallet") {
                console.log(availability);
              }

              // await db.chain.get("whoisCache").set(word, availability);
              db.data.whoisCache[word] = availability;
              await db.write();
            }

            if (availability) {
              console.log("Available:", word);
            }
          } catch (error) {
            console.error("Error checking whois availability", error);
          }
        }, 500);

        setInterval(async () => {
          console.log(`
            
---Diagnostics---
Translations: ${Array.from(translationQueue).length}
Webifications: ${Array.from(webificationQueue).length}
Whois: ${Array.from(whoisQueue).length}
            
            `);
        }, 10000);
      } catch (error) {
        console.error(error);
      }
    }
  )
  .help().argv;

async function getTranslations(word: string): Promise<Translation[]> {
  const responses = await Promise.all(
    languages.map(async (language) => {
      const response = await translate(word, language.code);

      if (!response) {
        return null;
      }

      return {
        word: unidecode(word).toLowerCase(),
        language,
        translation: {
          raw: response?.[0]?.[0]?.[0],
          cleaned: unidecode(response?.[0]?.[0]?.[0])
            .replace(/[^a-zA-Z]/g, "")
            .toLowerCase(),
        },
      };
    })
  );

  return (
    responses
      .filter((response) => response !== null)
      .filter((response) => Boolean(response?.translation)) || []
  );
}

async function getWebifiedWords({
  translation,
}: Translation): Promise<string[]> {
  // console.log("Webifying words for", translation.cleaned);
  const response = await openai.chat.completions
    .create({
      model: "qwen2.5-7b-instruct-1m",
      messages: [
        {
          role: "user",
          content: `Convert the following word into a list of Web 2.0 style SaaS name by removing a single vowel each time. Return the output as a JS string array. If there is only one result make sure the array has only one element. Do not output any text other than the array

word: ${translation.cleaned}`,
        },
      ],
    })
    .catch((error) => {
      console.log("Error generating response", error);
      return {} as any;
    });

  if (!response?.choices[0]?.message?.content) {
    return [];
  }

  try {
    return JSON.parse(response.choices[0].message.content.toLowerCase()).filter(
      (webified) =>
        Boolean(webified) &&
        !Array.isArray(webified) &&
        webified.indexOf(" ") === -1
    );
  } catch (error) {
    return [];
  }
}

async function checkDomainAvailability(word: string) {
  if (Array.isArray(word)) {
    word = word.join("");
  }

  const spacelessWord = word.replace(/\s/g, "");
  const domain = `${spacelessWord}.com`;

  const dnsLookup = await dns.promises.lookup(domain).catch(() => {});

  if (dnsLookup) {
    return false;
  }

  const whoisResponse = await fetch(
    `https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/intel/whois?domain=${domain}`,
    {
      headers: {
        Authorization: `Bearer ${CLOUDFLARE_API_TOKEN}`,
      },
    }
  );

  const data = await whoisResponse.json().catch((error) => {
    console.log("Error looking up whois for", domain, error);
  });

  if (domain === "wallet.com" || word === "wallet") {
    console.error("Raw reponse for wallet.com", data);
  }

  if (!data?.success) {
    console.error("Failed looking up domain", domain);
    return undefined;
  }

  // console.log({ data });

  return Boolean(!data?.result?.found);
}
