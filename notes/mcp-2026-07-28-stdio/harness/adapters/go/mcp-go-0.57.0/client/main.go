// mcp-stdio-cross-era client adapter: github.com/mark3labs/mcp-go, documented default stdio path
// (client.NewStdioMCPClient + Initialize with ClientInfo only; ProtocolVersion left empty).
package main

import (
	"context"
	"io"
	"os"
	"strings"

	"github.com/mark3labs/mcp-go/client"
	"github.com/mark3labs/mcp-go/mcp"
)

const impl = "mcp-go-0.57.0"

func main() { harnessMain(impl, run) }

func run(r *recorder, cmd []string, tool string, args map[string]any) {
	ctx := context.Background()

	r.start()
	c, err := client.NewStdioMCPClient(cmd[0], nil, cmd[1:]...) // spawns SERVER_CMD
	if err != nil {
		r.fail(err)
		return
	}
	// Forward server stderr to ours, as in examples/simple_client (keeps the pipe drained).
	if stderr, ok := client.GetStderr(c); ok {
		go func() { _, _ = io.Copy(os.Stderr, stderr) }()
	}

	var initReq mcp.InitializeRequest
	initReq.Params.ClientInfo = mcp.Implementation{Name: "re13340-client", Version: "1.0.0"}
	ir, err := c.Initialize(ctx, initReq)
	if err != nil {
		r.fail(err)
		_ = c.Close()
		return
	}
	r.set(func(o *result) {
		if ir.ProtocolVersion != "" {
			o.Negotiated = strp(ir.ProtocolVersion)
		}
		if ir.ServerInfo.Name != "" || ir.ServerInfo.Version != "" {
			o.ServerInfo = map[string]string{"name": ir.ServerInfo.Name, "version": ir.ServerInfo.Version}
		}
	})
	r.done("connect", "list")

	if ok := func() bool {
		lt, err := c.ListTools(ctx, mcp.ListToolsRequest{})
		if err != nil {
			r.fail(err)
			return false
		}
		names := make([]string, 0, len(lt.Tools))
		for _, t := range lt.Tools {
			names = append(names, t.Name)
		}
		r.set(func(o *result) { o.Tools = sortedNames(names) })
		r.done("list", "call")

		var callReq mcp.CallToolRequest
		callReq.Params.Name = tool
		callReq.Params.Arguments = args
		res, err := c.CallTool(ctx, callReq)
		if err != nil {
			r.fail(err)
			return false
		}
		var sb strings.Builder
		for _, item := range res.Content {
			if tc, ok := mcp.AsTextContent(item); ok {
				sb.WriteString(tc.Text)
			}
		}
		text, isErr := sb.String(), res.IsError
		r.set(func(o *result) { o.CallText, o.CallIsError = &text, &isErr })
		r.done("call", "close")
		return true
	}(); !ok {
		_ = c.Close()
		return
	}

	if err := c.Close(); err != nil {
		r.fail(err)
	}
}
