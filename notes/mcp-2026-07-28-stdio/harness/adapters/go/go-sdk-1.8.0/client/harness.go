// Shared, SDK-free bookkeeping for the mcp-stdio-cross-era Go client adapters (stdlib only).
// Identical copy in every <impl>/client directory; mirrors adapters/py/_harness.py.
//
// Parses `-- SERVER_CMD [ARGS...]`, reads MCP_TOOL / MCP_ARGS, keeps cumulative monotonic
// timings and prints the single result JSON line required by CONTRACT.md. Each adapter
// supplies run(rec, cmd, tool, args), which drives its SDK's default path with
// context.Background(); the 40 s deadline is an external watchdog, never passed to an SDK.
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"sort"
	"sync"
	"time"
)

const deadline = 40 * time.Second // harness guard only (outer harness kills at 45 s)

type result struct {
	Impl        string            `json:"impl"`
	ConnectOK   bool              `json:"connect_ok"`
	ListOK      bool              `json:"list_ok"`
	CallOK      bool              `json:"call_ok"`
	Tools       []string          `json:"tools"`
	CallText    *string           `json:"call_text"`
	CallIsError *bool             `json:"call_is_error"`
	Negotiated  *string           `json:"negotiated"`
	ServerInfo  map[string]string `json:"server_info"`
	TConnectMs  *float64          `json:"t_connect_ms"`
	TListMs     *float64          `json:"t_list_ms"`
	TCallMs     *float64          `json:"t_call_ms"`
	ErrorStage  *string           `json:"error_stage"`
	ErrorType   *string           `json:"error_type"`
	ErrorMsg    *string           `json:"error_msg"`
}

type recorder struct {
	mu    sync.Mutex
	t0    time.Time // carries Go's monotonic clock reading
	stage string
	out   result
	final bool
}

// start is called immediately before the SDK connect call.
func (r *recorder) start() {
	r.mu.Lock()
	r.t0 = time.Now()
	r.mu.Unlock()
}

func (r *recorder) ms() *float64 {
	v := float64(time.Since(r.t0).Microseconds()/100) / 10
	return &v
}

func (r *recorder) done(stage, next string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.final {
		return
	}
	switch stage {
	case "connect":
		r.out.ConnectOK, r.out.TConnectMs = true, r.ms()
	case "list":
		r.out.ListOK, r.out.TListMs = true, r.ms()
	case "call":
		r.out.CallOK, r.out.TCallMs = true, r.ms()
	}
	if next != "" {
		r.stage = next
	}
}

// set mutates the result under the lock (ignored once the line is final).
func (r *recorder) set(f func(o *result)) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if !r.final {
		f(&r.out)
	}
}

func (r *recorder) failLocked(typ, msg string) {
	if r.out.ErrorStage != nil {
		return
	}
	st := r.stage
	if len(msg) > 500 {
		msg = msg[:500]
	}
	r.out.ErrorStage, r.out.ErrorType, r.out.ErrorMsg = &st, &typ, &msg
}

func (r *recorder) fail(err error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.final {
		return
	}
	r.failLocked(leafType(err), errMsg(err))
}

// leafType reports the dynamic type of the innermost error of a single Unwrap chain.
func leafType(err error) string {
	for {
		next := errors.Unwrap(err)
		if next == nil {
			return fmt.Sprintf("%T", err)
		}
		err = next
	}
}

// errCode lets an adapter prefix a JSON-RPC error code, like the Python harness.
var errCode func(error) (int64, bool)

func errMsg(err error) string {
	msg := err.Error()
	if errCode != nil {
		if c, ok := errCode(err); ok {
			msg = fmt.Sprintf("[%d] %s", c, msg)
		}
	}
	return msg
}

func (r *recorder) emit() {
	r.mu.Lock()
	r.final = true
	b, err := json.Marshal(r.out)
	r.mu.Unlock()
	if err != nil {
		fmt.Fprintln(os.Stderr, "harness: marshal:", err)
		os.Exit(3)
	}
	os.Stdout.Write(append(b, '\n'))
}

func sortedNames(names []string) []string {
	out := append([]string{}, names...)
	sort.Strings(out)
	return out
}

func strp(s string) *string { return &s }

func harnessMain(impl string, run func(r *recorder, cmd []string, tool string, args map[string]any)) {
	argv := os.Args[1:]
	if len(argv) < 2 || argv[0] != "--" {
		fmt.Fprintf(os.Stderr, "usage: %s -- SERVER_CMD [ARGS...]\n", os.Args[0])
		os.Exit(2)
	}
	cmd := argv[1:]
	tool := os.Getenv("MCP_TOOL")
	if tool == "" {
		tool = "echo"
	}
	rawArgs := os.Getenv("MCP_ARGS")
	if rawArgs == "" {
		rawArgs = `{"message":"hello-re13340"}`
	}
	var args map[string]any
	if err := json.Unmarshal([]byte(rawArgs), &args); err != nil {
		fmt.Fprintln(os.Stderr, "harness: MCP_ARGS:", err)
		os.Exit(2)
	}
	r := &recorder{stage: "connect", out: result{Impl: impl}}
	r.t0 = time.Now()

	finished := make(chan struct{})
	go func() {
		defer close(finished)
		defer func() {
			if p := recover(); p != nil {
				r.fail(fmt.Errorf("panic: %v", p))
				r.set(func(o *result) { o.ErrorType = strp("panic") })
			}
		}()
		run(r, cmd, tool, args)
	}()
	select {
	case <-finished:
	case <-time.After(deadline):
		r.mu.Lock()
		if !r.final && r.out.ErrorStage == nil {
			r.failLocked("HarnessDeadline", fmt.Sprintf("harness deadline %gs", deadline.Seconds()))
		}
		r.mu.Unlock()
	}
	r.emit()
	os.Exit(0)
}
