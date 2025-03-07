import unidecode from "unidecode-plus";

import { languages } from "../utils/languages";
import { Translation } from "../types";

export async function translate(
  word: string,
  languageCode: string
): Promise<Translation[]> {
  const response = await fetch(
    `https://translate.google.com/translate_a/single?client=gtx&sl=en&tl=${languageCode}&dt=t&q=${word}`
  );
  const data = await response.json();
  return data;
}

export async function getTranslations(word: string): Promise<Translation[]> {
  const responses = await Promise.all(
    languages.map(async (language) => {
      const response = await translate(word, language.code);

      if (!response) {
        return null;
      }

      // TODO: Consider using iconv instead of unidecode if we still have issues
      return {
        word: unidecode(unidecode(word))
          .replace(/[^a-zA-Z]/g, "")
          .toLowerCase(),
        language,
        translation: {
          raw: response?.[0]?.[0]?.[0],
          cleaned: unidecode(unidecode(response?.[0]?.[0]?.[0]))
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
