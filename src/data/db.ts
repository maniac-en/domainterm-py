import { Low } from "lowdb";
import { JSONFile } from "lowdb/node";
import lodash from "lodash";
import * as remeda from "remeda";
import { Translation, TranslationWithWebifiedWords } from "../types";

type Data = {
  // Google translate results
  translationCache: Record<string, Translation[]>;
  // LLM webification results
  webifiedCache: Record<string, TranslationWithWebifiedWords>;
  // WHOIS lookup results
  whoisCache: Record<string, boolean | undefined>;

  // --------------------------------------

  // Google search results
  searchResultsCache: Record<string, string>;
  // Evaluated Search Results
  searchEvaluationCache: Record<
    string,
    { confidence: number; isAvailable: boolean }
  >;
  // LLM name rating results
  ratingsCache: Record<string, number>;
};

// Extend Low class with a new `chain` field
class LowWithLodash<T> extends Low<T> {
  chain: lodash.ExpChain<this["data"]> = lodash.chain(this).get("data");
}

// class LowWithRemeda<T> extends Low<T> {
//   chain: remeda.Chain<Data> = remeda.chain(this).get("data");
// }

const defaultData: Data = {
  whoisCache: {},
  webifiedCache: {},
  translationCache: {},
  searchResultsCache: {},
  searchEvaluationCache: {},
  ratingsCache: {},
};
const adapter = new JSONFile<Data>("db.json");

export const db = new LowWithLodash(adapter, defaultData);
