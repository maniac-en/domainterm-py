export interface Translation {
  language: { name: string; code: string };
  translation: { raw: string; cleaned: string };
}

export interface TranslationWithWebifiedWords extends Translation {
  webifiedWords: string[];
}
