// mcp-stdio-cross-era client adapter: github.com/modelcontextprotocol/go-sdk, README default path
// (mcp.NewClient + mcp.CommandTransport + Client.Connect(ctx, t, nil)).
package main

import (
	"context"
	"errors"
	"os/exec"
	"strings"

	"github.com/modelcontextprotocol/go-sdk/jsonrpc"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

const impl = "go-sdk-1.8.0"

func main() {
	errCode = func(err error) (int64, bool) {
		var we *jsonrpc.Error
		if errors.As(err, &we) {
			return we.Code, true
		}
		return 0, false
	}
	harnessMain(impl, run)
}

func run(r *recorder, cmd []string, tool string, args map[string]any) {
	ctx := context.Background()
	client := mcp.NewClient(&mcp.Implementation{Name: "re13340-client", Version: "1.0.0"}, nil)
	transport := &mcp.CommandTransport{Command: exec.Command(cmd[0], cmd[1:]...)}

	r.start()
	session, err := client.Connect(ctx, transport, nil)
	if err != nil {
		r.fail(err)
		return
	}
	if ir := session.InitializeResult(); ir != nil {
		r.set(func(o *result) {
			if ir.ProtocolVersion != "" {
				o.Negotiated = strp(ir.ProtocolVersion)
			}
			if ir.ServerInfo != nil {
				o.ServerInfo = map[string]string{"name": ir.ServerInfo.Name, "version": ir.ServerInfo.Version}
			}
		})
	}
	r.done("connect", "list")

	if ok := func() bool {
		lt, err := session.ListTools(ctx, &mcp.ListToolsParams{})
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

		res, err := session.CallTool(ctx, &mcp.CallToolParams{Name: tool, Arguments: args})
		if err != nil {
			r.fail(err)
			return false
		}
		var sb strings.Builder
		for _, c := range res.Content {
			if tc, ok := c.(*mcp.TextContent); ok {
				sb.WriteString(tc.Text)
			}
		}
		text, isErr := sb.String(), res.IsError
		r.set(func(o *result) { o.CallText, o.CallIsError = &text, &isErr })
		r.done("call", "close")
		return true
	}(); !ok {
		_ = session.Close() // close after an earlier-stage failure; outcome already recorded
		return
	}

	if err := session.Close(); err != nil {
		r.fail(err)
	}
}
