import Ajv2020 from "ajv/dist/2020.js";
import { glob } from "glob";
import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import YAML from "yaml";

const ajv = new Ajv2020({
  allErrors: true,
  strict: true,
});

function readJson(filePath: string): unknown {
  return JSON.parse(readFileSync(filePath, "utf8"));
}

function readYaml(filePath: string): unknown {
  return YAML.parse(readFileSync(filePath, "utf8"));
}

function schemaPathForSpec(specPath: string): string {
  const relativePath = path.relative("specs", specPath);
  const parsed = path.parse(relativePath);
  return path.join("schemas", parsed.dir, `${parsed.name}.schema.json`);
}

const specFiles = await glob("specs/**/*.yaml", { nodir: true });

if (specFiles.length === 0) {
  throw new Error("No YAML specification files found under specs/.");
}

const failures: string[] = [];

for (const specFile of specFiles.sort()) {
  const schemaFile = schemaPathForSpec(specFile);

  if (!existsSync(schemaFile)) {
    failures.push(`${specFile}: missing schema file ${schemaFile}`);
    continue;
  }

  const schema = readJson(schemaFile);
  const data = readYaml(specFile);
  const validate = ajv.compile(schema);
  const valid = validate(data);

  if (!valid) {
    const errors = validate.errors
      ?.map((error) => {
        const params = Object.keys(error.params).length > 0
          ? ` ${JSON.stringify(error.params)}`
          : "";
        return `${error.instancePath || "/"} ${error.message}${params}`;
      })
      .join("; ");
    failures.push(`${specFile}: ${errors}`);
  }
}

if (failures.length > 0) {
  console.error("Specification validation failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log(`Validated ${specFiles.length} specification file(s).`);
