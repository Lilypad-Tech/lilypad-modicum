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
	// run me from test directory, e.g. `(cd test; go test)` from top level lilypad repo
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
		if err := runCommand("./stack", []string{"build"}); err != nil {
			t.Fatal(err)
		}
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
		"text",
		"hello, testing",
		"/stdout",
	)
}


func TestSDXL(t *testing.T) {
	// only run if gpu on system
	_, err := exec.LookPath("nvidia-smi")
	if err != nil {
		t.Skip("no nvidia-smi on system, skipping test")
	}
	t.Skip("skip")
	testJob(
		t,
		[]string{"submitjob", "sdxl:v0.9-lilypad1", "an astronaut riding on an orange horse"}, 
		"image",
		"",
		"/outputs/image-0.png",
	)
}

func TestLoRA(t *testing.T) {
	// only run if gpu on system
	_, err := exec.LookPath("nvidia-smi")
	if err != nil {
		t.Skip("no nvidia-smi on system, skipping test")
	}
	cid := testJob(
		t,
		[]string{"submitjob", "lora_training:v0.1.7-lilypad1", `{images_cid: "bafybeiah7ib5mhzlckolwlkwquzf772wl6jdbhtbuvnbuo5arq7pcs4ubm", seed: 3}`},
		"", "", "",
	)
	testJob(
		t,
		[]string{"submitjob", "lora_inference:v0.1.7-lilypad1", fmt.Sprintf(`{lora_cid: "%s", seed: 3, prompt: "a tshirt in the style of <s1><s2>, male, hard rim photography"}`, cid)},
		"image", "", "/outputs/image-3.jpg",
	)
}

func TestSDXLColours(t *testing.T) {
	// only run if gpu on system
	_, err := exec.LookPath("nvidia-smi")
	if err != nil {
		t.Skip("no nvidia-smi on system, skipping test")
	}
	t.Skip("skip")
	colours := []string{"gold", "silver", "red", "orange", "yellow", "green", "blue", "orange", "purple"}
	for _, c := range colours {
		testJob(
			t,
			[]string{"submitjob", "sdxl:v0.9-lilypad1", fmt.Sprintf("an astronaut riding on an %s unicorn", c)},
			"image",
			"",
			"/outputs/image-0.png",
		)
	}
}

// TODO: LLM test

func testJob(t *testing.T, args []string, kind string, expectedText string, relPath string) string {
	maybeReset(t)

	if err := os.Remove(filepath.Join(PATH, "out.txt")); err != nil && !os.IsNotExist(err) {
		t.Fatal(err)
	}

	log.Printf("----> STACK %s", args)
	out, err := exec.Command("./stack", args...).CombinedOutput()
	if err != nil {
		t.Fatal(err, string(out))
	}
	writeOutput(out, "out.txt")

	log.Println("----> FINDING IPFS URL")
	ipfsURL, err := findIPFSURL("out.txt")
	if err != nil {
		t.Fatal(err)
	}

	xs := strings.Split(ipfsURL, "/")
	cid := xs[len(xs)-1]

	// download ipfs url with http lib
	resp, err := http.Get(ipfsURL+relPath)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
	if kind == "image" {
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
	} else if kind == "text" {
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
	return cid
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
