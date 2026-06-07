const fs = require('fs');
let content = fs.readFileSync('/usr/lib/node_modules/langfuse-cli/openapi.yml', 'utf8');

const search = `    CreatePromptRequest:
      title: CreatePromptRequest
      oneOf:
        - $ref: '#/components/schemas/CreateChatPromptRequest'
        - $ref: '#/components/schemas/CreateTextPromptRequest'`;

const replace = `    CreatePromptRequest:
      title: CreatePromptRequest
      type: object
      properties:
        name:
          type: string
        prompt:
          type: string
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
  console.log('Patched openapi.yml');
} else {
  console.log('Search string not found!');
}
