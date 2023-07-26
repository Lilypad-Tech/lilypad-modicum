package main

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"strings"
)

type MultiWriter struct {
	writers []io.Writer
}

func (mw *MultiWriter) Write(p []byte) (n int, err error) {
	for _, w := range mw.writers {
		if n, err = w.Write(p); err != nil {
			return
		}
		if n != len(p) {
			err = io.ErrShortWrite
			return
		}
	}
	return len(p), nil
}

func NewMultiWriter(writers ...io.Writer) *MultiWriter {
	return &MultiWriter{writers: writers}
}

func runCommand(name string, args []string) error {
	log.Printf("Running %s %s", name, args)
	_, _, err := runCommandWithOutput(name, args)
	return err
}

func writeOutput(out []byte, filename string) {
	file, err := os.OpenFile(filename, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		fmt.Println(err)
		return
	}
	defer file.Close()
	if _, err := file.Write(out); err != nil {
		fmt.Println(err)
	}
}

func findIPFSURL(filename string) (string, error) {
	file, err := os.Open(filename)
	if err != nil {
		return "", err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	buf := make([]byte, 0, 64*1024)
	scanner.Buffer(buf, 1024*1024)

	for scanner.Scan() {
		line := scanner.Text()
		log.Print(line)
		if strings.Contains(line, "ipfs.io") {
			xs := strings.Split(line, " ")
			return xs[len(xs)-1], nil
		}
	}

	if err := scanner.Err(); err != nil {
		return "", err
	}

	return "", fmt.Errorf("no IPFS URL found in %s", filename)
}

func runCommandWithOutput(name string, args []string) (string, string, error) {
	var stdoutBuf, stderrBuf bytes.Buffer
	cmd := exec.Command(name, args...)

	cmd.Stdout = NewMultiWriter(os.Stdout, &stdoutBuf)
	cmd.Stderr = NewMultiWriter(os.Stderr, &stderrBuf)

	if err := cmd.Run(); err != nil {
		return "", "", err
	}

	return stdoutBuf.String(), stderrBuf.String(), nil
}
