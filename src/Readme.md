Build me a Java Spring Boot project where:
- There is an MCP server exposing 4 agents:
   1. OrchestratorAgent (master, routes queries using LLM).
   2. DeveloperAgent (with tools: dev_code, dev_debug, dev_review).
   3. BAAgent (with tools: ba_gather_req, ba_clarify, ba_flow).
   4. TestAgent (with tools: test_write, test_exec, test_report).
- Each agent should have @Tool annotated methods.
- The OrchestratorAgent must use Spring AI LLM to decide dynamically which agent/tool to invoke (no hardcoded if-else routing).
- Expose the server endpoints using Spring MVC (`@RestController`) with a single `/mcp` endpoint that accepts JSON-RPC requests and returns JSON-RPC responses.
- Implement the standard MCP methods:
   - initialize
   - tools/list
   - tools/call
- Agents must be able to collaborate: if one agent cannot fully answer, it should internally call another agent's MCP tool via the same protocol.
  For example:
    - DeveloperAgent may call BAAgent if it needs requirement clarification.
    - TestAgent may call DeveloperAgent if it needs debugging help.
    - BAAgent may call DeveloperAgent or TestAgent for feasibility validation.
- Generate a separate Java MCP client that uses HTTP POST to communicate with this server.
- The client should send a user query, receive the orchestrated response, and print it.
