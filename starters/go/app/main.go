package main

import (
	"fmt"
	"os"
)

func main() {
	// Stage 1: print the prompt (fmt.Print to os.Stdout is unbuffered).
	// Uncomment the next line, then run ./smith test
	// fmt.Fprint(os.Stdout, "$ ")

	// Stage 2 onwards: read a line, e.g. with bufio.NewReader(os.Stdin).ReadString('\n')
	_ = fmt.Sprint
	_ = os.Stdout
}
