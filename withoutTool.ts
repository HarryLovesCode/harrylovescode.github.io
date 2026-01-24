import OpenAI from "openai";
import type { ChatCompletionMessageParam } from "openai/resources";

const client = new OpenAI({
  baseURL: "http://127.0.0.1:1234/v1",
  apiKey: "placeholder",
});

export async function callLLM(messages: ChatCompletionMessageParam[]) {
  const response = await client.chat.completions.create({
    model: "openai/gpt-oss-20b",
    messages,
  });

  const output = response.choices[0]?.message.content || "";
  if (output.includes("<think>")) {
    response.choices[0]!.message.content = output.split("</think>")[1]!.trim();
  }

  return response.choices[0]!.message;
}

export function concatMarkdown(message: string) {
  const regex = /```(?:[a-zA-Z0-9]*)\n([\s\S]*?)```/g;

  let match: RegExpExecArray | null;
  let codeOutput = "";

  while ((match = regex.exec(message)) !== null) {
    codeOutput += `${match[1]}\n`;
  }

  return codeOutput.trim();
}

function formatMessage(
  role: "system" | "assistant" | "user",
  message: string,
  reasoning?: string,
) {
  return {
    role,
    content: message,
    reasoning,
  };
}

const SYSTEM_PROMPT = `You will be given a task to perform.

<OUTPUT>
  - Python code snippet that provides the solution to the task, or a step towards the solution. 
  Any output you want to extract from the code should be printed to the console. Code MUST be output in a fenced code block.
  - Text to be shown directly to the user, if you want to ask for more information or provide the final answer. Do NOT use
  fenced code blocks in this case.
</OUTPUT>

<RULES>
  - Variables defined at the top level of previous code snippets can be referenced in your code.
  - Do not include information about installing or running. This will be handled automatically.
  - Avoid speculating the output. The code output will be provided to you afterwards.
  - You must write code once. Do not respond directly with the answer.
</RULES>

Multi-step problems benefit from planning. To plan or think, use a multi-line string in Python wrapped in a Markdown code block.
Reminder: use Python code snippets to call tools! Assume you have any dependencies referenced by the user already installed.
Follow output and rules guidelines exactly.
`;

const TEST_PROMPT = `Step 1: Find the top post today on HackerNews.
Step 2: Navigate to the article. 
Step 2: Convert article to Markdown.
Step 3: Return the first couple of paragraphs in Markdown max 1024 characters.
Final: Given this return, respond with which operating systems are supported. Use a python multi-line string.

Packages: requests, markdownify, beautifulsoup4 are installed.\n`;

const STDOUT_OR_RETURN_PROMPT = `Code output:`;

async function test() {
  let hasUsedTool = false;
  const MAX_TURNS = 5;
  const history: ChatCompletionMessageParam[] = [
    formatMessage("system", SYSTEM_PROMPT),
    formatMessage("user", TEST_PROMPT),
  ];

  for (let turnIdx = 0; turnIdx < MAX_TURNS; turnIdx++) {
    const out = await callLLM(history);
    const md = concatMarkdown(out.content!);

    if (md.length < 1 && hasUsedTool) {
      // LLM wants to output something to us.
      history.push(formatMessage("assistant", out.content!));
      break;
    } else if (md.length < 1 && !hasUsedTool) {
      // This will happen if the LLM does not output Python on the
      // first call properly.
      continue;
    }

    hasUsedTool = true;

    history.push(out);
    console.log("-".repeat(80));
    console.log("Wrote code:\n");
    console.log(`\t${md.split("\n").join("\n\t")}`);
    console.log("-".repeat(80) + "\n");

    // LLM wants to execute code.

    const execResults = await fetch("http://localhost:3000", {
      method: "POST",
      body: JSON.stringify({
        modules: ["requests", "beautifulsoup4", "markdownify"],
        code: md,
      }),
    });

    const execParse = await execResults.json();
    const execOutput = `${STDOUT_OR_RETURN_PROMPT}\n${execParse.stdout}
- Reflect on the code written and the output. If the output matches expectations, then respond with output without using fenced code blocks.
- If the output is not ready, refine by continuing to write code.`;
    history.push(formatMessage("user", execOutput));
  }

  console.log(`Output:\n${history[history.length - 1]!.content}`);
}

test();
