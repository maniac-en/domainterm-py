#!/usr/bin/env node

import dotenv from "dotenv";
dotenv.config();

import * as yargs from "yargs";
import unidecode from "unidecode";
import OpenAI from "openai";
import whois from "whois-json";
import dns from "dns";

import { translate } from "./utils/translate";
import { languages } from "./utils/languages";
import { Translation, TranslationWithWebifiedWords } from "./types";

const { CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID } = process.env;

const openai = new OpenAI({
  baseURL: "http://localhost:1234/v1",
  apiKey: "sk-9q3f1s3d3s3d3s3d3s3d3s3d3s3d3s3d",
});

(yargs as any)
  .scriptName("domain-tx-cli")
  .usage("$0 get [args]")
  .command(
    "get [word]",
    "get translated domains available",
    (yargs) => {
      yargs.positional("word", {
        type: "string",
        default: "guardian",
        describe: "the word to translate",
      });
    },
    async function (argv) {
      try {
        // lookup translations via google translate api
        const translations = await getTranslations(argv.word);

        // use an llm to webify the words: eg Walter to Waltr
        console.log("Getting webified words");
        console.log("");
        const initialTotal = translations.length;
        let current = 0;
        const webifiedTranslations = await Promise.all(
          translations.map(async (translation) => {
            const webifiedWords = await getWebifiedWords(translation);
            current++;
            process.stdout.clearLine(0);
            process.stdout.cursorTo(0);
            process.stdout.write(`${current}/${initialTotal}`);
            return {
              ...translation,
              webifiedWords,
            };
          })
        );

        process.stdout.write("\n");

        // for each, translation lookup whois info
        console.log("Checking availability");

        const availableDomains: any = [];
        const intervalId = setInterval(async () => {
          const translation = webifiedTranslations.shift();

          if (!translation) {
            clearInterval(intervalId);
            console.log("No more translations to check");
            process.exit(0);
            return;
          }
          const availability = await checkDomainAvailability(translation);
          if (availability && availability.length > 0) {
            availability.forEach((domain) => {
              console.log(
                "Available:",
                domain.domain,
                "(",
                domain.language.name,
                ")",
                "(original word:",
                domain.word,
                ")"
              );
            });

            availableDomains.push(...availability);
          }
        }, 3000);
        process.stdout.write("\n");
      } catch (error) {
        console.error(error);
      }

      // for each available domain. lookup via LLM the existence of a product with the name. use RAG to parse google results/
      // output available domains and the metadata around the word like the country of origin and original word if different from the webification
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
      model: "llama-3.2-3b-instruct",
      messages: [
        {
          role: "user",
          content: `Convert the following word into a Web 2.0 style SaaS name by removing random vowels. Return the output as a JS string array. Do not output any text other than the array

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
    return JSON.parse(response.choices[0].message.content);
  } catch (error) {
    return [];
  }
}

async function checkDomainAvailability({
  language,
  translation: { raw, cleaned },
  webifiedWords,
}: TranslationWithWebifiedWords) {
  const words = [cleaned, ...webifiedWords].filter((word) => word.length > 0);

  const responses = await Promise.all(
    words.map(async (word) => {
      const spacelessWord = word.replace(/\s/g, "");
      const domain = `${spacelessWord}.com`;

      const dnsLookup = await dns.promises.lookup(domain).catch(() => {});

      if (dnsLookup) {
        return null;
      }

      const whoisResponse = await fetch(
        `https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/intel/whois?domain=${domain}`,
        {
          headers: {
            Authorization: `Bearer ${CLOUDFLARE_API_TOKEN}`,
          },
        }
      );

      const data = await whoisResponse.json().catch(() => {});

      if (!data?.success) {
        console.log("Failed looking up domain", domain);
        return null;
      }

      if (data.result.found) {
        return null;
      } else {
        return {
          language,
          word: cleaned,
          domain,
        };
      }
    })
  );

  const filtered = responses.filter((response) => response !== null);

  return filtered;
}
