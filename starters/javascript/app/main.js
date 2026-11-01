// Node's built-in "readline" module gives you prompts, line editing, a TAB
// completer and history, which covers most of what the later stages need.
const readline = require("node:readline");

const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: true });

// Stage 1: show the prompt. Uncomment the next two lines, then run ./smith test
// rl.setPrompt("$ ");
// rl.prompt();

// Stage 2 onwards: handle each line the user types.
// rl.on("line", (line) => { ...; rl.prompt(); });

rl.close();
