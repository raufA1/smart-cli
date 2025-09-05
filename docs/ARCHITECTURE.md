# Smart CLI Architecture Documentation

## System Overview

Smart CLI is an enterprise-grade AI-powered development assistant built with a modular, extensible architecture. The system combines intelligent request classification, multi-agent orchestration, and specialized operational modes to provide a comprehensive development environment.

## 🏗️ Core Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[Command Line Interface]
        UI[Rich Terminal UI]
    end
    
    subgraph "Request Processing Layer"
        ER[Enhanced Request Router]
        IC[Intelligent Classifier]
        MM[Mode Manager]
    end
    
    subgraph "Core Services Layer"
        CM[Context Manager]
        SM[Session Manager]
        CH[Command Handler]
        FM[File Manager]
    end
    
    subgraph "AI & Orchestration Layer"
        AIC[AI Client]
        ORC[Orchestrator]
        MA[Multi-Agent System]
    end
    
    subgraph "Integration Layer"
        GH[GitHub Integration]
        GM[Git Manager]
        TM[Terminal Manager]
    end
    
    subgraph "Configuration Layer"
        Config[Configuration Manager]
        MC[Mode Config Manager]
        PP[Project Profiles]
    end
    
    CLI --> ER
    UI --> ER
    ER --> IC
    ER --> MM
    ER --> CH
    
    MM --> CM
    CM --> SM
    CH --> FM
    
    ER --> AIC
    AIC --> ORC
    ORC --> MA
    
    CH --> GH
    CH --> GM
    CH --> TM
    
    Config --> MC
    Config --> PP
```

## 📦 Module Structure

### Core Modules

```
src/
├── core/                           # Core system components
│   ├── __init__.py                 # Package exports
│   ├── session_manager.py          # Session lifecycle management
│   ├── file_manager.py             # File system operations
│   ├── command_handler.py          # Command processing
│   ├── request_router.py           # Original request routing
│   ├── enhanced_request_router.py  # Enhanced mode-aware routing
│   ├── intelligent_request_classifier.py  # AI request classification
│   ├── mode_manager.py             # Mode system management
│   ├── context_manager.py          # Context isolation & sharing
│   ├── mode_config_manager.py      # Mode configuration system
│   ├── mode_integration_manager.py # System integration
│   └── mode_system_activator.py    # Mode system activation
├── agents/                         # AI agent implementations
│   ├── orchestrator.py             # Multi-agent orchestration
│   ├── architect_agent.py          # System architecture agent
│   └── meta_learning_agent.py      # Learning and adaptation
├── handlers/                       # Specialized request handlers
│   ├── base_handler.py             # Handler base class
│   ├── cost_handler.py             # Cost management
│   ├── file_handler.py             # File operations
│   ├── git_handler.py              # Git operations
│   ├── github_handler.py           # GitHub integration
│   ├── implementation_handler.py   # Code implementation
│   ├── project_handler.py          # Project management
│   └── terminal_handler.py         # Terminal operations
├── integrations/                   # External service integrations
│   ├── github_client.py            # GitHub API client
│   └── github_manager.py           # GitHub management
└── utils/                          # Utility modules
    ├── config.py                   # Configuration management
    ├── simple_ai_client.py         # AI service client
    └── error_handler.py            # Error handling
```

## 🎭 Enhanced Mode System Architecture

### Mode System Components

The Enhanced Mode System introduces a sophisticated operational model:

```mermaid
graph LR
    subgraph "Mode Management"
        MM[Mode Manager]
        MC[Mode Configs]
        MH[Mode History]
    end
    
    subgraph "Context System"
        CM[Context Manager]
        MI[Mode Isolation]
        CS[Context Sharing]
        CR[Cross References]
    end
    
    subgraph "Request Processing"
        ER[Enhanced Router]
        IC[Intelligent Classifier]
        MP[Mode Processor]
    end
    
    subgraph "Integration"
        IM[Integration Manager]
        SA[System Activator]
        PH[Processing Hooks]
    end
    
    MM --> MC
    MM --> MH
    CM --> MI
    CM --> CS
    CM --> CR
    ER --> IC
    ER --> MP
    IM --> SA
    IM --> PH
    
    MM <--> CM
    ER <--> MM
    IM <--> ER
```

### Mode Lifecycle

```mermaid
sequenceDiagram
    participant U as User
    participant ER as Enhanced Router
    participant MM as Mode Manager
    participant CM as Context Manager
    participant P as Processor
    
    U->>ER: Request Input
    ER->>MM: Get Current Mode
    MM->>ER: Mode Info
    ER->>CM: Get Mode Context
    CM->>ER: Context Data
    ER->>P: Process in Mode
    P->>CM: Update Context
    P->>ER: Response
    ER->>U: Final Response
```

## 🧠 Intelligent Classification System

### Request Classification Flow

```mermaid
flowchart TD
    A[User Input] --> B[Text Analysis]
    B --> C{Command Check}
    C -->|Command| D[System Command]
    C -->|Not Command| E[Pattern Analysis]
    
    E --> F[Azerbaijani Patterns]
    E --> G[English Patterns]
    E --> H[Technical Context]
    
    F --> I[Classification Engine]
    G --> I
    H --> I
    
    I --> J{Confidence > 0.5}
    J -->|Yes| K[Classified Type]
    J -->|No| L[Additional Analysis]
    
    L --> M[Context Boost]
    M --> N[Final Classification]
    
    K --> O[Route to Processor]
    N --> O
```

### Classification Categories

1. **COMMAND**: System commands (`/mode`, `/help`, etc.)
2. **DEVELOPMENT**: Code creation, modification, building
3. **UTILITY**: File operations, Git commands, terminal tasks
4. **CONVERSATION**: General AI chat, questions
5. **LEARNING**: Educational content, explanations
6. **ANALYSIS**: Code review, debugging, investigation

## 🤖 Multi-Agent Orchestration

### Orchestrator Architecture

```mermaid
graph TB
    subgraph "Orchestrator Core"
        TC[Task Classifier]
        EP[Execution Planner]
        AC[Agent Coordinator]
    end
    
    subgraph "Specialized Agents"
        AA[Architect Agent]
        CA[Code Analyzer]
        CM[Code Modifier]
        TA[Testing Agent]
        RA[Review Agent]
        MLA[MetaLearning Agent]
    end
    
    subgraph "Support Systems"
        CO[Cost Optimizer]
        UI[Terminal UI]
        FM[File Manager]
    end
    
    TC --> EP
    EP --> AC
    AC --> AA
    AC --> CA
    AC --> CM
    AC --> TA
    AC --> RA
    AC --> MLA
    
    AA --> FM
    CA --> FM
    CM --> FM
    
    AC --> CO
    AC --> UI
```

### Agent Collaboration Model

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant A as Architect
    participant C as Code Modifier
    participant T as Testing Agent
    participant R as Review Agent
    
    O->>A: Plan Architecture
    A->>O: Architecture Plan
    O->>C: Implement Code
    C->>O: Implementation
    O->>T: Run Tests
    T->>O: Test Results
    O->>R: Review Code
    R->>O: Review Report
    O->>O: Consolidate Results
```

## 🔧 Configuration Architecture

### Configuration Hierarchy

```mermaid
graph TD
    A[Global Config] --> B[User Config]
    B --> C[Project Config]
    C --> D[Runtime Config]
    
    A --> E[~/.smart_cli_modes.yaml]
    B --> F[~/.smart_cli/config]
    C --> G[.smartcli]
    D --> H[Session State]
    
    I[Environment Variables] --> D
    J[Command Line Args] --> D
```

### Configuration Sources

1. **Global Configuration**: `~/.smart_cli_modes.yaml`
   - System-wide defaults
   - Global mode preferences
   - User-specific settings

2. **Project Configuration**: `.smartcli`
   - Project-specific mode settings
   - Team collaboration settings
   - Integration configurations

3. **Runtime Configuration**
   - Session-specific overrides
   - Temporary settings
   - Dynamic adjustments

## 🔄 Request Processing Flow

### Enhanced Request Processing

```mermaid
flowchart TD
    A[User Input] --> B{Mode Command?}
    B -->|Yes| C[Handle Mode Command]
    B -->|No| D[Get Enhanced Context]
    
    D --> E[Current Mode Check]
    E --> F{Smart Mode?}
    
    F -->|Yes| G[Intelligent Classification]
    F -->|No| H[Mode-Specific Processing]
    
    G --> I[Route by Classification]
    H --> J[Execute in Mode Context]
    
    I --> K[Update Context]
    J --> K
    
    K --> L[Execute Hooks]
    L --> M[Return Response]
    
    C --> N[Mode System Update]
    N --> O[Context Update]
    O --> M
```

### Context Management Flow

```mermaid
graph LR
    subgraph "Context Isolation"
        A[Mode A Context]
        B[Mode B Context]
        C[Mode C Context]
    end
    
    subgraph "Shared Layer"
        SM[Shared Memory]
        CR[Cross References]
        GS[Global State]
    end
    
    subgraph "Flow Control"
        FR[Flow Rules]
        TF[Transform Functions]
        PC[Permission Control]
    end
    
    A --> SM
    B --> SM
    C --> SM
    
    SM --> CR
    CR --> GS
    
    FR --> TF
    TF --> PC
    PC --> SM
```

## 📊 Performance Architecture

### Performance Monitoring

```mermaid
graph TB
    subgraph "Metrics Collection"
        MC[Mode Metrics]
        TC[Timing Metrics]
        CC[Cost Metrics]
        UC[Usage Metrics]
    end
    
    subgraph "Analysis Engine"
        PA[Performance Analyzer]
        TR[Trend Recognition]
        AA[Anomaly Detection]
    end
    
    subgraph "Reporting"
        RT[Real-time Dashboard]
        HR[Historical Reports]
        RG[Recommendation Generator]
    end
    
    MC --> PA
    TC --> PA
    CC --> PA
    UC --> PA
    
    PA --> TR
    PA --> AA
    
    TR --> RT
    AA --> HR
    PA --> RG
```

### Cost Optimization

```mermaid
graph TD
    A[Request Analysis] --> B[Cost Estimation]
    B --> C{Budget Check}
    C -->|Within Budget| D[Execute Request]
    C -->|Over Budget| E[Cost Optimization]
    
    E --> F[Model Selection]
    E --> G[Context Reduction]
    E --> H[Request Batching]
    
    F --> I[Re-estimate Cost]
    G --> I
    H --> I
    
    I --> J{Acceptable?}
    J -->|Yes| D
    J -->|No| K[User Approval]
    
    K --> L{Approved?}
    L -->|Yes| D
    L -->|No| M[Request Rejected]
```

## 🔒 Security Architecture

### Security Layers

```mermaid
graph TB
    subgraph "Input Security"
        IS[Input Sanitization]
        IV[Input Validation]
        IC[Injection Prevention]
    end
    
    subgraph "Access Control"
        AM[Authentication Manager]
        PM[Permission Manager]
        RM[Role Manager]
    end
    
    subgraph "Operation Security"
        OS[Operation Sandboxing]
        FL[File Access Control]
        NL[Network Limitations]
    end
    
    subgraph "Data Security"
        DE[Data Encryption]
        AL[Audit Logging]
        SI[Sensitive Info Detection]
    end
    
    IS --> IV
    IV --> IC
    
    AM --> PM
    PM --> RM
    
    OS --> FL
    FL --> NL
    
    DE --> AL
    AL --> SI
```

### Mode-Based Security

- **Analysis Mode**: Read-only access, no file modifications
- **Learning Mode**: Restricted tool access, safe exploration
- **Code Mode**: Full access with confirmation requirements
- **Fast Mode**: Auto-approval for safe operations only

## 🔌 Integration Architecture

### External Integrations

```mermaid
graph LR
    subgraph "Smart CLI Core"
        SC[Smart CLI]
    end
    
    subgraph "AI Services"
        AC[Anthropic Claude]
        OAI[OpenAI]
        OR[OpenRouter]
    end
    
    subgraph "Development Tools"
        GH[GitHub]
        GT[Git]
        TM[Terminal]
    end
    
    subgraph "External APIs"
        REST[REST APIs]
        WS[WebSockets]
        DB[Databases]
    end
    
    SC --> AC
    SC --> OAI
    SC --> OR
    
    SC --> GH
    SC --> GT
    SC --> TM
    
    SC --> REST
    SC --> WS
    SC --> DB
```

### Integration Manager

```mermaid
sequenceDiagram
    participant SC as Smart CLI
    participant IM as Integration Manager
    participant GH as GitHub
    participant AI as AI Service
    
    SC->>IM: Request Integration
    IM->>IM: Validate Credentials
    IM->>GH: API Call
    GH->>IM: Response
    IM->>AI: Process with AI
    AI->>IM: AI Response
    IM->>SC: Integrated Result
```

## 🚀 Deployment Architecture

### Development Environment

```yaml
development:
  mode_system: enabled
  debug_logging: true
  cost_limits: relaxed
  ai_providers: 
    - anthropic
    - openai
  integrations:
    - github
    - terminal
    - git
```

### Production Environment

```yaml
production:
  mode_system: enabled
  debug_logging: false
  cost_limits: strict
  security: enhanced
  audit_logging: enabled
  performance_monitoring: enabled
```

### Enterprise Deployment

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Load Balancer]
    end
    
    subgraph "Application Tier"
        SC1[Smart CLI Instance 1]
        SC2[Smart CLI Instance 2]
        SC3[Smart CLI Instance 3]
    end
    
    subgraph "Service Tier"
        AIS[AI Service Pool]
        CS[Configuration Service]
        MS[Monitoring Service]
    end
    
    subgraph "Data Tier"
        DB[Configuration DB]
        FS[File Storage]
        LS[Log Storage]
    end
    
    LB --> SC1
    LB --> SC2
    LB --> SC3
    
    SC1 --> AIS
    SC2 --> AIS
    SC3 --> AIS
    
    SC1 --> CS
    SC2 --> CS
    SC3 --> CS
    
    AIS --> MS
    CS --> DB
    MS --> LS
    CS --> FS
```

## 🔄 Data Flow Architecture

### Request-Response Cycle

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI Interface
    participant ER as Enhanced Router
    participant MM as Mode Manager
    participant CM as Context Manager
    participant AI as AI Service
    participant H as Handlers
    
    U->>CLI: Input Command
    CLI->>ER: Process Request
    ER->>MM: Check Current Mode
    MM->>CM: Get Context
    CM->>ER: Context Data
    ER->>AI: AI Processing
    AI->>ER: AI Response
    ER->>H: Handler Processing
    H->>ER: Handler Response
    ER->>CM: Update Context
    ER->>CLI: Final Response
    CLI->>U: Display Result
```

### Context Data Flow

```mermaid
graph TD
    A[User Request] --> B[Mode Context]
    B --> C[Shared Memory]
    C --> D[Cross References]
    D --> E[Global State]
    
    E --> F[Processing]
    F --> G[Context Updates]
    
    G --> H[Mode Context]
    G --> I[Shared Memory]
    G --> J[Cross References]
    G --> K[Global State]
    
    H --> L[Next Request]
    I --> L
    J --> L
    K --> L
```

## 📈 Scalability Architecture

### Horizontal Scaling

- **Stateless Design**: Mode contexts persisted externally
- **Load Distribution**: Multiple CLI instances
- **Service Separation**: AI services, configuration, monitoring
- **Cache Layers**: Context caching, response caching

### Performance Optimization

- **Lazy Loading**: Mode components loaded on demand
- **Context Optimization**: Automatic memory management
- **Request Batching**: Efficient AI service usage
- **Intelligent Caching**: Smart cache invalidation

## 🔮 Future Architecture Considerations

### Planned Enhancements

1. **Distributed Mode System**: Multi-machine mode coordination
2. **Advanced AI Integration**: Custom model training
3. **Plugin Architecture**: Third-party mode extensions
4. **Cloud Integration**: Cloud-based context synchronization
5. **Real-time Collaboration**: Multi-user mode sharing

### Architecture Evolution

The Smart CLI architecture is designed for continuous evolution:

- **Modular Design**: Easy component replacement
- **Interface Stability**: Backwards compatibility
- **Extension Points**: Plugin and integration hooks
- **Configuration Flexibility**: Runtime reconfiguration
- **Performance Monitoring**: Continuous optimization

---

This architecture provides a robust, scalable, and maintainable foundation for the Smart CLI Enhanced Mode System, supporting both current functionality and future growth.