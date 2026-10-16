import openapiTS, { astToString, COMMENT_HEADER } from "openapi-typescript";
import { readFile } from "node:fs/promises";
import { format } from "prettier";

const ast = await openapiTS(
  new URL("../schemas/openapi.json", import.meta.url),
);
const expected = await format(COMMENT_HEADER + astToString(ast), {
  parser: "typescript",
});
const actual = await readFile(
  new URL("src/api.generated.ts", import.meta.url),
  "utf8",
);
if (actual !== expected) {
  throw new Error(
    "Generated TypeScript schema drift; run npm run types, then format and review",
  );
}
console.log("Generated TypeScript matches backend OpenAPI");
