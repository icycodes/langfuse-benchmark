const fs = require('fs');
const file = '/usr/lib/node_modules/langfuse-cli/node_modules/specli/dist/cli/runtime/body-flags.js';
let content = fs.readFileSync(file, 'utf8');

// Patch collectFlags
content = content.replace(
  /t === "boolean"\) \{/g,
  't === "boolean" || t === "array" || t === "object") {'
);

// Patch setNestedValue
content = content.replace(
  /else \{\s*current\[finalKey\] = String\(value\);\s*\}/g,
  `else if (type === "array" || type === "object") {
        current[finalKey] = value;
    }
    else {
        current[finalKey] = String(value);
    }`
);

fs.writeFileSync(file, content);
console.log('Patched body-flags.js');
