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
