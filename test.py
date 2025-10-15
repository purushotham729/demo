### Improved Multi-Agent Spring Boot Application

Based on a deeper analysis of the `multiagent-openmanus` example, which implements a true multi-agent system using Spring AI Alibaba Graph (inspired by LangGraph), I've refactored the application to mirror it more closely. The example uses:

- **StateGraph** for orchestration: A directed graph with nodes for each agent, conditional edges based on a router (e.g., supervisor decides next agent or END), and state management (e.g., a custom `AgentState` holding messages and next route).
- **Agents**: Defined as callable functions that take the state, append user messages, use `ChatClient` (with tools via functions) to generate responses, and update state (e.g., add AI message, set next if needed).
- **Supervisor**: A special agent that routes to other agents using a conditional edge. It uses a system prompt to output JSON with "next" field (e.g., {"next": "ba_agent"} or {"next": "FINISH"}).
- **Tools**: Registered as `FunctionCallback` beans, bound to agents via `ChatClient.functions()`.
- **Workflow**: Starts at supervisor, loops through agents (each using tools as needed), back to supervisor until FINISH. State persists messages for context.
- **Key Features from Example**: Hierarchical coordination, reflection (agents can self-reflect), delegation (supervisor delegates tasks). Uses Alibaba's DashScope for LLM, but I've adapted to OpenAI as per your request. Graph built with `StateGraph.builder()`, `addNode()`, `addEdge(START, "supervisor")`, `addConditionalEdges("supervisor", router)`, and agent edges back to supervisor.
- **Dependencies**: Includes `spring-ai-langgraph-java` (or equivalent for graph support; assume added via BOM).

This creates a fresh app: **brd-multiagent-orchestrator**. It's now a proper multi-agent loop with supervisor coordination. Tools are invoked by agents (e.g., BAAgent uses extraction and analysis tools). For testing, I've created 5 tools as described (mocks; extend for real impl).

Run via REST endpoint: Upload BRD, graph runs, returns final state/output.

### Directory Structure
(Updated for graph/state classes)
```
brd-multiagent-orchestrator/
├── pom.xml
├── src/
│   └── main/
│       ├── java/
│       │   └── com/
│       │       └── example/
│       │           └── brdmultiagent/
│       │               ├── BrdMultiagentOrchestratorApplication.java
│       │               ├── config/
│       │               │   └── AppConfig.java  // Replaces OpenAiConfig; includes beans
│       │               ├── agent/
│       │               │   ├── SupervisorAgent.java
│       │               │   ├── BAAgent.java
│       │               │   ├── DevAgent.java
│       │               │   └── CodingAgent.java
│       │               ├── tool/
│       │               │   ├── DocumentExtractorTool.java
│       │               │   ├── OpenAIAnalysisTool.java
│       │               │   ├── JsonGeneratorTool.java
│       │               │   ├── MicroserviceCallerTool.java
│       │               │   └── JenkinsApiCallerTool.java
│       │               ├── graph/
│       │               │   ├── BrdWorkflowGraph.java
│       │               │   └── AgentState.java  // Custom state
│       │               └── controller/
│       │                   └── UploadController.java  // Replaces service
│       └── resources/
│           └── application.yml
└── README.md
```

### pom.xml
(Added langgraph-java for StateGraph; adjust version if needed)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>
    <groupId>com.example</groupId>
    <artifactId>brd-multiagent-orchestrator</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>brd-multiagent-orchestrator</name>
    <description>Multi-agent BRD Orchestrator</description>

    <properties>
        <java.version>17</java.version>
        <spring-ai.version>1.0.0-M1</spring-ai.version>
        <langgraph-java.version>0.1.0</langgraph-java.version> <!-- For StateGraph; use latest -->
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-openai-spring-boot-starter</artifactId>
            <version>${spring-ai.version}</version>
        </dependency>
        <dependency>
            <groupId>dev.langchain4j</groupId>
            <artifactId>langgraph-java</artifactId> <!-- Spring AI Alibaba uses similar -->
            <version>${langgraph-java.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.pdfbox</groupId>
            <artifactId>pdfbox</artifactId>
            <version>3.0.0</version>
        </dependency>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.ai</groupId>
                <artifactId>spring-ai-bom</artifactId>
                <version>${spring-ai.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

### src/main/resources/application.yml
```yaml
spring:
  ai:
    openai:
      api-key: ${OPENAI_API_KEY:your-openai-key-here}
      chat:
        options:
          model: gpt-4o-mini
          temperature: 0.7
logging:
  level:
    root: INFO
    com.example: DEBUG
server:
  port: 8080
```

### src/main/java/com/example/brdmultiagent/BrdMultiagentOrchestratorApplication.java
```java
package com.example.brdmultiagent;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class BrdMultiagentOrchestratorApplication {
    public static void main(String[] args) {
        SpringApplication.run(BrdMultiagentOrchestratorApplication.class, args);
    }
}
```

### config/AppConfig.java
```java
package com.example.brdmultiagent.config;

import com.example.brdmultiagent.tool.*;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.openai.OpenAiChatModel;
import org.springframework.ai.openai.api.OpenAiApi;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.ai.model.function.FunctionCallback;
import org.springframework.ai.model.function.FunctionCallbackWrapper;

@Configuration
public class AppConfig {

    @Value("${spring.ai.openai.api-key}")
    private String openAiApiKey;

    @Bean
    public ChatModel chatModel() {
        return new OpenAiChatModel(new OpenAiApi(openAiApiKey));
    }

    @Bean
    public ChatClient chatClient(ChatModel chatModel) {
        return ChatClient.builder(chatModel).build();
    }

    // Tools as FunctionCallbacks
    @Bean("documentExtractorTool")
    public FunctionCallback documentExtractorTool(DocumentExtractorTool impl) {
        return FunctionCallbackWrapper.builder(impl::extract)
                .withName("documentExtractorTool")
                .withDescription("Extract text from BRD file")
                .withInputType(String.class) // filePath
                .withOutputType(String.class) // extracted text
                .build();
    }

    @Bean("openAIAnalysisTool")
    public FunctionCallback openAIAnalysisTool(OpenAIAnalysisTool impl) {
        return FunctionCallbackWrapper.builder(impl::analyze)
                .withName("openAIAnalysisTool")
                .withDescription("Analyze content with OpenAI and generate scenarios")
                .withInputType(String.class) // content
                .withOutputType(String.class) // scenarios
                .build();
    }

    @Bean("jsonGeneratorTool")
    public FunctionCallback jsonGeneratorTool(JsonGeneratorTool impl) {
        return FunctionCallbackWrapper.builder(impl::generateJson)
                .withName("jsonGeneratorTool")
                .withDescription("Generate JSON from scenarios")
                .withInputType(String.class)
                .withOutputType(String.class)
                .build();
    }

    @Bean("microserviceCallerTool")
    public FunctionCallback microserviceCallerTool(MicroserviceCallerTool impl) {
        return FunctionCallbackWrapper.builder(impl::callMicroservice)
                .withName("microserviceCallerTool")
                .withDescription("Call microservice with JSON to get Excel")
                .withInputType(String.class)
                .withOutputType(String.class) // excel path
                .build();
    }

    @Bean("jenkinsApiCallerTool")
    public FunctionCallback jenkinsApiCallerTool(JenkinsApiCallerTool impl) {
        return FunctionCallbackWrapper.builder(impl::callJenkins)
                .withName("jenkinsApiCallerTool")
                .withDescription("Send Excel to Jenkins API")
                .withInputType(String.class)
                .withOutputType(String.class) // status
                .build();
    }
}
```

### graph/AgentState.java
```java
package com.example.brdmultiagent.graph;

import org.springframework.ai.chat.messages.Message;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class AgentState {
    private List<Message> messages = new ArrayList<>();
    private String next; // For routing

    public List<Message> getMessages() {
        return messages;
    }

    public void addMessage(Message message) {
        messages.add(message);
    }

    public String getNext() {
        return next;
    }

    public void setNext(String next) {
        this.next = next;
    }

    // For final output: last message content
    public String getFinalOutput() {
        if (!messages.isEmpty()) {
            return messages.get(messages.size() - 1).getContent();
        }
        return "";
    }
}
```

### agent/SupervisorAgent.java
```java
package com.example.brdmultiagent.agent;

import com.example.brdmultiagent.graph.AgentState;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.ai.chat.messages.Message;
import org.springframework.ai.chat.messages.SystemMessage;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;

@Component
public class SupervisorAgent {

    private final ChatClient chatClient;

    @Autowired
    public SupervisorAgent(ChatClient chatClient) {
        this.chatClient = chatClient.defaultSystem("""
                You are the Supervisor Agent coordinating BRD processing.
                Agents: ba_agent (extract/analyze BRD, generate scenarios), dev_agent (JSON from scenarios, call microservice for Excel), coding_agent (send Excel to Jenkins).
                Analyze current state and decide next: "ba_agent", "dev_agent", "coding_agent", or "FINISH".
                Respond ONLY with JSON: {"next": "agent_name or FINISH"}
                """);
    }

    public AgentState invoke(AgentState state) {
        // Build prompt with history
        List<Message> promptMessages = new ArrayList<>(state.getMessages());
        promptMessages.add(0, new SystemMessage(chatClient.getDefaultSystemPrompt())); // Ensure system

        String response = chatClient.prompt()
                .messages(promptMessages)
                .call()
                .content();

        // Parse JSON for next
        try {
            Map<String, String> json = new ObjectMapper().readValue(response, Map.class);
            state.setNext(json.getOrDefault("next", "FINISH"));
        } catch (Exception e) {
            state.setNext("FINISH");
        }

        state.addMessage(new AssistantMessage(response));
        return state;
    }
}
```

### agent/BAAgent.java
```java
package com.example.brdmultiagent.agent;

import com.example.brdmultiagent.graph.AgentState;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.ai.chat.messages.SystemMessage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import org.springframework.ai.model.function.FunctionCallback;

@Component
public class BAAgent {

    private final ChatClient baClient;

    @Autowired
    public BAAgent(ChatClient chatClient,
                   @Qualifier("documentExtractorTool") FunctionCallback extractorTool,
                   @Qualifier("openAIAnalysisTool") FunctionCallback analysisTool) {
        this.baClient = chatClient.defaultSystem("""
                You are BA Agent. Extract BRD content, analyze with OpenAI, generate scenarios.
                Use tools: documentExtractorTool, openAIAnalysisTool.
                Reflect if needed, output scenarios.
                """)
                .functions(extractorTool.getName(), analysisTool.getName());
    }

    public AgentState invoke(AgentState state) {
        String response = baClient.prompt()
                .messages(state.getMessages())
                .call()
                .content(); // Handles tool calls internally if response has tools

        state.addMessage(new AssistantMessage(response));
        return state;
    }
}
```

### agent/DevAgent.java
```java
package com.example.brdmultiagent.agent;

import com.example.brdmultiagent.graph.AgentState;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import org.springframework.ai.model.function.FunctionCallback;

@Component
public class DevAgent {

    private final ChatClient devClient;

    @Autowired
    public DevAgent(ChatClient chatClient,
                    @Qualifier("jsonGeneratorTool") FunctionCallback jsonTool,
                    @Qualifier("microserviceCallerTool") FunctionCallback microserviceTool) {
        this.devClient = chatClient.defaultSystem("""
                You are Dev Agent. From scenarios, generate JSON, call microservice for Excel.
                Use tools: jsonGeneratorTool, microserviceCallerTool.
                Output Excel path/content.
                """)
                .functions(jsonTool.getName(), microserviceTool.getName());
    }

    public AgentState invoke(AgentState state) {
        String response = devClient.prompt()
                .messages(state.getMessages())
                .call()
                .content();

        state.addMessage(new AssistantMessage(response));
        return state;
    }
}
```

### agent/CodingAgent.java
```java
package com.example.brdmultiagent.agent;

import com.example.brdmultiagent.graph.AgentState;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import org.springframework.ai.model.function.FunctionCallback;

@Component
public class CodingAgent {

    private final ChatClient codingClient;

    @Autowired
    public CodingAgent(ChatClient chatClient,
                       @Qualifier("jenkinsApiCallerTool") FunctionCallback jenkinsTool) {
        this.codingClient = chatClient.defaultSystem("""
                You are Coding Agent. Send Excel to Jenkins API.
                Use tool: jenkinsApiCallerTool.
                Output job status.
                """)
                .functions(jenkinsTool.getName());
    }

    public AgentState invoke(AgentState state) {
        String response = codingClient.prompt()
                .messages(state.getMessages())
                .call()
                .content();

        state.addMessage(new AssistantMessage(response));
        return state;
    }
}
```

### tool/* (Same as before, but impl as classes with methods)
```java
// DocumentExtractorTool.java (example; others similar)
package com.example.brdmultiagent.tool;

import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.stereotype.Component;

import java.io.File;

@Component
public class DocumentExtractorTool {
    public String extract(String filePath) {
        try (PDDocument doc = PDDocument.load(new File(filePath))) {
            PDFTextStripper stripper = new PDFTextStripper();
            return stripper.getText(doc);
        } catch (Exception e) {
            return "Mock extracted content: BRD requirements..."; // Fallback
        }
    }
}

// OpenAIAnalysisTool.java
package com.example.brdmultiagent.tool;

import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
public class OpenAIAnalysisTool {
    @Autowired
    private ChatModel chatModel;

    public String analyze(String content) {
        Prompt prompt = new Prompt("Generate scenarios from BRD: " + content);
        return chatModel.call(prompt).getResult().getOutput().getContent();
    }
}

// JsonGeneratorTool.java, MicroserviceCallerTool.java, JenkinsApiCallerTool.java (similar mocks as before)
```

### graph/BrdWorkflowGraph.java
```java
package com.example.brdmultiagent.graph;

import com.example.brdmultiagent.agent.BAAgent;
import com.example.brdmultiagent.agent.CodingAgent;
import com.example.brdmultiagent.agent.DevAgent;
import com.example.brdmultiagent.agent.SupervisorAgent;
import dev.langchain4j.langgraph.StateGraph;
import dev.langchain4j.langgraph.StateGraph.Edge;
import dev.langchain4j.langgraph.StateGraph.Node;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.Map;

import static dev.langchain4j.langgraph.StateGraph.END;
import static dev.langchain4j.langgraph.StateGraph.START;

@Component
public class BrdWorkflowGraph {

    private final SupervisorAgent supervisorAgent;
    private final BAAgent baAgent;
    private final DevAgent devAgent;
    private final CodingAgent codingAgent;

    @Autowired
    public BrdWorkflowGraph(SupervisorAgent supervisorAgent, BAAgent baAgent, DevAgent devAgent, CodingAgent codingAgent) {
        this.supervisorAgent = supervisorAgent;
        this.baAgent = baAgent;
        this.devAgent = devAgent;
        this.codingAgent = codingAgent;
    }

    public StateGraph<AgentState> buildGraph() {
        return new StateGraph<>(AgentState::new)
                .addNode("supervisor", state -> supervisorAgent.invoke(state))
                .addNode("ba_agent", state -> baAgent.invoke(state))
                .addNode("dev_agent", state -> devAgent.invoke(state))
                .addNode("coding_agent", state -> codingAgent.invoke(state))
                .addEdge(START, "supervisor")
                .addConditionalEdges("supervisor",
                        state -> state.getNext(), // Router function
                        Map.of("ba_agent", "ba_agent",
                               "dev_agent", "dev_agent",
                               "coding_agent", "coding_agent",
                               "FINISH", END))
                .addEdge("ba_agent", "supervisor")
                .addEdge("dev_agent", "supervisor")
                .addEdge("coding_agent", "supervisor");
    }

    public String run(String initialInput) {
        AgentState initialState = new AgentState();
        initialState.addMessage(new org.springframework.ai.chat.messages.UserMessage(initialInput));

        StateGraph<AgentState> graph = buildGraph();
        AgentState finalState = graph.compile().invoke(initialState);

        return finalState.getFinalOutput();
    }
}
```

### controller/UploadController.java
```java
package com.example.brdmultiagent.controller;

import com.example.brdmultiagent.graph.BrdWorkflowGraph;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.nio.file.Files;
import java.nio.file.Path;

@RestController
public class UploadController {

    @Autowired
    private BrdWorkflowGraph workflowGraph;

    @PostMapping("/upload-brd")
    public ResponseEntity<String> uploadBrd(@RequestParam("file") MultipartFile file) {
        try {
            Path tempPath = Files.createTempFile("brd-", file.getOriginalFilename());
            file.transferTo(tempPath);
            String initialInput = "Process BRD file: " + tempPath.toString();
            String result = workflowGraph.run(initialInput);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error: " + e.getMessage());
        }
    }
}
```

### README.md
```
# BRD Multiagent Orchestrator

Multi-agent system using Spring AI (adapted from Alibaba Graph example).

## Setup
- Set OPENAI_API_KEY.
- mvn spring-boot:run
- POST /upload-brd with 'file' multipart.

## Workflow
- Upload triggers graph.
- Supervisor routes: BA (extract/analyze) -> Dev (JSON/microservice) -> Coding (Jenkins) -> FINISH.
- Agents use tools; state persists messages.

## Notes
- Tools are mocks; implement real PDF extraction, API calls.
- For Alibaba DashScope, replace OpenAiChatModel.
- Debug with logs.
```

This matches the example's multi-agent pattern: supervisor-coordinated loop with tools and conditional routing. Test and extend!
