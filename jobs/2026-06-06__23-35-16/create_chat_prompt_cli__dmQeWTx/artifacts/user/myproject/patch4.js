const fs = require('fs');
let content = fs.readFileSync('/usr/lib/node_modules/langfuse-cli/openapi.yml', 'utf8');

const search = `    CreatePromptRequest:
      title: CreatePromptRequest
      type: object
      properties:
        name:
          type: string
        prompt:
          type: string
        config:
          type: string
        type:
          type: string
        labels:
          type: string
        tags:
          type: string
        commitMessage:
          type: string
      required:
        - name
        - prompt
        - type`;

const replace = `    CreatePromptRequest:
      title: CreatePromptRequest
      type: object
      properties:
        name:
          type: string
        prompt:
          type: array
          items:
            type: object
        config:
          type: object
        type:
          type: string
        labels:
          type: array
          items:
            type: string
        tags:
          type: array
          items:
            type: string
        commitMessage:
          type: string
      required:
        - name
        - prompt
        - type`;

if (content.includes(search)) {
  content = content.replace(search, replace);
  fs.writeFileSync('/usr/lib/node_modules/langfuse-cli/openapi.yml', content);
  console.log('Patched openapi.yml fourth time');
} else {
  console.log('Not found');
}
