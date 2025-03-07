import { Low } from "lowdb";
import { JSONFile } from "lowdb/node";
import lodash from "lodash";
import * as remeda from "remeda";
import {
  SearchEvaluation,
  Translation,
  TranslationWithWebifiedWords,
} from "../types";

type Data = {
  // Google translate results
  translationCache: Record<string, Translation[]>;
  // LLM webification results
  webifiedCache: Record<string, TranslationWithWebifiedWords>;
  // WHOIS lookup results
  whoisCache: Record<string, boolean | undefined>;
  // Evaluated Search Results
  searchEvaluationCache: Record<string, SearchEvaluation>;
  // LLM name rating results
  ratingsCache: Record<string, number>;
  // Synonym lookup results
  synonymsCache: Record<string, string[]>;

  // --------------------------------------

  npmCache: Record<string, boolean>;
  trademarkCache: Record<string, boolean>;
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
  searchEvaluationCache: {},
  ratingsCache: {},
  synonymsCache: {},
  npmCache: {},
  trademarkCache: {},
};
const adapter = new JSONFile<Data>("db.json");

export const db = new LowWithLodash(adapter, defaultData);
