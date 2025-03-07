import OpenAI from "openai";
import { SearchEvaluation, Translation } from "../types";

const openai = new OpenAI({
  // Using LMStudio locally
  baseURL: "http://localhost:1234/v1",
  // WARNING: This is a fake API key. Do not use in production.
  apiKey: "sk-9q3f1s3d3s3d3s3d3s3d3s3d3s3d3s3d",
});

const LLM_MODEL = "mistral-nemo-instruct-2407";

export async function getWebifiedWords({
  translation,
}: Translation): Promise<string[]> {
  // console.log("Webifying words for", translation.cleaned);
  const response = await openai.chat.completions
    .create({
      model: LLM_MODEL,
      messages: [
        {
          role: "user",
          content: `Convert the following word into a list of Web 2.0 style SaaS name by removing a single vowel each time. Return the output as a JS string array. If there is only one result make sure the array has only one element. Do not output any text other than the array

word: ${translation.cleaned}`,
        },
      ],
      response_format: {
        type: "json_schema",
        json_schema: {
          name: "webified",
          strict: true,
          schema: {
            type: "array",
            items: {
              type: "string",
            },
          },
        },
      },
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

export async function checkSearchResults(
  word: string
): Promise<SearchEvaluation> {
  const searchResponse = await fetch(
    `https://search.brave.com/search?q=${word}`
  ).then((response) => response.text());

  const llmResponse = await openai.chat.completions
    .create({
      model: LLM_MODEL,
      messages: [
        {
          role: "user",
          content: `
          Given the following search results, determine if the word is a good product/business name or not. It is a bad name if there is an existing product or business by the same or similar name in the Tech/Software industry. Output the result as a json that looks like '{ "isAvailable": true, "confidence": 42 }' where true is replaced with the actual result of it being a good or bad name. true for good, false for bad. confidence is a rating between 0 and 100 where 0 is the lowest confidence and 100 is the highest confidence. Do not output any text other than the raw json. That means no markdown syntax.
          
          word: ${word}
          
          search results: ${searchResponse}
          
          `,
        },
      ],
      response_format: {
        type: "json_schema",
        json_schema: {
          name: "rating",
          strict: true,
          schema: {
            type: "object",
            properties: {
              isAvailable: {
                type: "boolean",
              },
              confidence: {
                type: "number",
              },
            },
            required: ["isAvailable", "confidence"],
          },
        },
      },
    })
    .catch((error) => {
      console.log("Error generating response", error);
      return {} as any;
    });

  try {
    return JSON.parse(llmResponse?.choices?.[0]?.message?.content);
  } catch (error) {
    console.error("Error parsing search response", error);
    console.log("Raw response", llmResponse?.choices?.[0]?.message?.content);
    return { confidence: 0, isAvailable: false };
  }
}

export async function rateName(word: string) {
  const llmResponse = await openai.chat.completions
    .create({
      model: LLM_MODEL,
      messages: [
        {
          role: "user",
          content: `
          Given the following word, rate its potential for a good product/business name. This should include how easy it would be to pronounce for an english speaker and how easy it would be to spell. Output the rating as a number between 0 and 100 where 0 is bad and 100 is good.

          word: ${word}

          `,
        },
      ],
      response_format: {
        type: "json_schema",
        json_schema: {
          name: "rating",
          strict: true,
          schema: {
            type: "object",
            properties: {
              rating: {
                type: "number",
              },
            },
            required: ["rating"],
          },
        },
      },
    })
    .catch((error) => {
      console.log("Error generating response", error);
      return {} as any;
    });

  try {
    return JSON.parse(llmResponse?.choices?.[0]?.message?.content)
      ?.rating as number;
  } catch (error) {
    console.error("Error parsing rating response", error);
    console.log("Raw response", llmResponse?.choices?.[0]?.message?.content);
    return -1;
  }
}

export async function getSynonyms(word: string) {
  const response = await openai.chat.completions
    .create({
      model: LLM_MODEL,
      messages: [
        {
          role: "user",
          content: `Find synonyms for the provided word. Provide at least 10 synonyms. Return the output as a JS string array. If there is only one result make sure the array has only one element. Do not output any text other than the array

word: ${word}`,
        },
      ],
      response_format: {
        type: "json_schema",
        json_schema: {
          name: "synonyms",
          strict: true,
          schema: {
            type: "array",
            items: {
              type: "string",
            },
          },
        },
      },
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
      (synonym) =>
        Boolean(synonym) &&
        !Array.isArray(synonym) &&
        synonym.indexOf(" ") === -1
    );
  } catch (error) {
    return [];
  }
}
