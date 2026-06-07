const fs = require('fs');
const file = 'node_modules/langfuse-cli/openapi.yml';
let content = fs.readFileSync(file, 'utf8');
content = content.replace(/input:\n\s+nullable: true/g, 'input:\n          type: string\n          nullable: true');
content = content.replace(/expectedOutput:\n\s+nullable: true/g, 'expectedOutput:\n          type: string\n          nullable: true');
fs.writeFileSync(file, content);
console.log("Done");
