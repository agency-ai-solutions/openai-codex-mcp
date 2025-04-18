#!/usr/bin/env python3
"""
OpenAI Codex MCP Server for use with Claude Code.
This server implements JSON-RPC 2.0 over HTTP to wrap the OpenAI Codex API.
"""

import os
import sys
from openai import OpenAI
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Load API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Please set the OPENAI_API_KEY environment variable.")

# Initialize OpenAI client
try:
    client = OpenAI(api_key=api_key)
except Exception as e:
    print(f"Error initializing OpenAI client: {e}", file=sys.stderr)
    raise

app = FastAPI(
    title="OpenAI Codex MCP Server",
    description="An MCP server to wrap the OpenAI Codex API for use with Claude Code",
    version="0.1.0",
)

@app.post("/", summary="JSON-RPC endpoint")
async def rpc(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    jsonrpc = payload.get("jsonrpc")
    method = payload.get("method")
    id_ = payload.get("id")
    params = payload.get("params", {})

    if jsonrpc != "2.0" or not method or id_ is None:
        raise HTTPException(status_code=400, detail="Invalid JSON-RPC request")

    if method == "complete":
        try:
            # Extract parameters
            model = params.get("model", "gpt-4o-mini")
            prompt = params.get("prompt", "")
            max_tokens = params.get("max_tokens", 150)
            temperature = params.get("temperature", 0.7)
            
            # Create completion using the new OpenAI SDK
            response = client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Convert response to dictionary
            result = {
                "id": response.id,
                "object": "text_completion",
                "created": response.created,
                "model": response.model,
                "choices": [
                    {
                        "text": choice.text,
                        "index": choice.index,
                        "finish_reason": choice.finish_reason
                    } for choice in response.choices
                ]
            }
            
            return JSONResponse({"jsonrpc": "2.0", "id": id_, "result": result})
        except Exception as e:
            error = {"code": -32000, "message": str(e)}
            return JSONResponse({"jsonrpc": "2.0", "id": id_, "error": error}, status_code=500)
    else:
        error = {"code": -32601, "message": f"Method '{method}' not found"}
        return JSONResponse({"jsonrpc": "2.0", "id": id_, "error": error}, status_code=404)

def main():
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()