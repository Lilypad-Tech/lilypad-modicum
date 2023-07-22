package main

import (
	"bufio"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

var PATH string

func maybeReset(t *testing.T) {
	if PATH == "" {
		path, err := os.Getwd()
		if err != nil {
			t.Fatal(err)
		}
		path = filepath.Dir(path)
		os.Chdir(path)
		PATH = path
	}
	if _, ok := os.LookupEnv("SKIP_RESET"); !ok {
		if err := runCommand("./stack", []string{"reset"}); err != nil {
			t.Fatal(err)
		}
		if err := runCommand("./stack", []string{"start"}); err != nil {
			t.Fatal(err)
		}
		time.Sleep(5 * time.Second)
	}
}

func TestCowsay(t *testing.T) {
	testJob(
		t,
		[]string{"submitjob", "cowsay:v0.0.1", "hello, testing"}, 
		false, 
		"hello, testing",
	)
}


func TestSDXL(t *testing.T) {
	// only run if gpu on system
	_, err := exec.LookPath("nvidia-smi")
	if err != nil {
		t.Skip("no nvidia-smi on system, skipping test")
	}
	testJob(
		t,
		[]string{"submitjob", "sdxl:v0.9-lilypad1", "an astronaut riding on an orange horse"}, 
		true, 
		"",
	)
}


func testJob(t *testing.T, args []string, isImage bool, expectedText string) {
	maybeReset(t)

	if err := os.Remove(filepath.Join(PATH, "out.txt")); err != nil && !os.IsNotExist(err) {
		t.Fatal(err)
	}

	out, err := exec.Command("./stack", args...).CombinedOutput()
	if err != nil {
		t.Fatal(err)
	}
	writeOutput(out, "out.txt")

	fmt.Println("----> FINDING IPFS URL")
	ipfsURL, err := findIPFSURL("out.txt")
	if err != nil {
		t.Fatal(err)
	}
	// download ipfs url with http lib
	resp, err := http.Get(ipfsURL+"/stdout")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
	if isImage {
		// write response body to temporary image file
		f, err := os.Create("out.png")
		if err != nil {
			t.Fatal(err)
		}
		defer f.Close()
		if _, err := f.ReadFrom(resp.Body); err != nil {
			t.Fatal(err)
		}
		// run kitty +kitten icat path/to/some/image.png
		if err := runCommand("kitty", []string{"+kitten", "icat", "out.png"}); err != nil {
			log.Printf("Error running kitty, probably not in image-capable terminal: %s", err)
		}
	} else {
		// read response body
		scanner := bufio.NewScanner(resp.Body)
		found := false
		for scanner.Scan() {
			line := scanner.Text()
			fmt.Println(line)
			if strings.Contains(line, expectedText) {
				found = true
			}
		}
		if !found {
				t.Fatalf("expected line to contain '%s'", expectedText)
		}
		if err := scanner.Err(); err != nil {
			t.Fatal(err)
		}
		fmt.Println(ipfsURL)
	}
}

func runCommand(name string, args []string) error {
	log.Printf("Running %s %s", name, args)
	cmd := exec.Command(name, args...)
	cmd.Dir = PATH
	o, err := cmd.CombinedOutput()
	if err != nil {
		log.Printf("Error from cmd %s %s: %s %s", name, args, err, o)
	}
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
	for scanner.Scan() {
		line := scanner.Text()
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
