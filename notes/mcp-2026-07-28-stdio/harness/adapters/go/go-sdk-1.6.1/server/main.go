// mcp-stdio-cross-era server adapter: github.com/modelcontextprotocol/go-sdk, README default path
// (mcp.NewServer(impl, nil) + mcp.AddTool + server.Run(ctx, &mcp.StdioTransport{})).
package main

import (
	"context"
	"log"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

type echoInput struct {
	Message string `json:"message"`
}

func echo(ctx context.Context, req *mcp.CallToolRequest, in echoInput) (*mcp.CallToolResult, any, error) {
	return &mcp.CallToolResult{Content: []mcp.Content{&mcp.TextContent{Text: "echo:" + in.Message}}}, nil, nil
}

func main() {
	server := mcp.NewServer(&mcp.Implementation{Name: "echo-server", Version: "1.0.0"}, nil)
	mcp.AddTool(server, &mcp.Tool{Name: "echo", Description: "Echo the message"}, echo)
	// log writes to stderr; stdout carries protocol traffic only.
	if err := server.Run(context.Background(), &mcp.StdioTransport{}); err != nil {
		log.Fatal(err)
	}
}
