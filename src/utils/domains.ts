import dotenv from "dotenv";
dotenv.config();

import dns from "dns";

const { CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID } = process.env;

export async function checkDomainAvailability(word: string) {
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
    console.log("Raw response", data);
    return undefined;
  }

  // console.log({ data });

  return Boolean(!data?.result?.found);
}
