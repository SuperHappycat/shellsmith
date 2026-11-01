use std::io::{self, Write};

fn main() {
    // Stage 1: print the prompt and flush stdout (Rust buffers it).
    // Uncomment the next two lines, then run: shellsmith test
    // print!("$ ");
    // io::stdout().flush().unwrap();

    // Stage 2 onwards: read a line.
    // let mut line = String::new();
    // io::stdin().read_line(&mut line).unwrap();
    let _ = io::stdout().flush();
}
