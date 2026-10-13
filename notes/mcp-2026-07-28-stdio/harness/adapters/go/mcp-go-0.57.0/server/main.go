// mcp-stdio-cross-era server adapter: github.com/mark3labs/mcp-go, README default path
// (server.NewMCPServer + mcp.NewTool + server.ServeStdio).
package main

import (
	"context"
	"fmt"
	"os"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func main() {
	s := server.NewMCPServer(
		"echo-server",
		"1.0.0",
		server.WithToolCapabilities(false),
	)
	tool := mcp.NewTool("echo",
		mcp.WithDescription("Echo the message"),
		mcp.WithString("message", mcp.Required()),
	)
	s.AddTool(tool, echoHandler)
	if err := server.ServeStdio(s); err != nil {
		// README prints to stdout; stderr here so stdout carries protocol traffic only.
		fmt.Fprintf(os.Stderr, "Server error: %v\n", err)
	}
}

func echoHandler(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	msg, err := request.RequireString("message")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	return mcp.NewToolResultText("echo:" + msg), nil
}
