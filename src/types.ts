export interface Translation {
  word: string;
  language: { name: string; code: string };
  translation: { raw: string; cleaned: string };
}

export interface TranslationWithWebifiedWords extends Translation {
  webifiedWords: string[];
}
