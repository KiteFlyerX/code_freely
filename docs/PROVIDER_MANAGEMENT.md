# Provider Management System

## Overview

CodeTraceAI includes a flexible provider management system inspired by [cc-switch](https://github.com/farion1231/cc-switch). This system allows you to configure and switch between multiple AI providers seamlessly.

## Features

- **Multi-Provider Support**: Claude, OpenAI, DeepSeek, and custom OpenAI-compatible APIs
- **Preset Configurations**: 50+ ready-to-use provider presets
- **Runtime Switching**: Switch providers without restarting the application
- **Import/Export**: Backup and restore your provider configurations
- **Proxy Support**: Configure proxy settings for each provider
- **Custom Parameters**: Extensible configuration for provider-specific options

## Available Providers

### Official Providers

| ID | Name | Type | Models |
|---|---|---|---|
| `claude-official` | Claude Official | Claude | claude-opus-4-6, claude-sonnet-4-6 |
| `openai-official` | OpenAI Official | OpenAI | gpt-4o, gpt-4o-mini |
| `deepseek-official` | DeepSeek Official | DeepSeek | deepseek-chat, deepseek-coder |

### Cloud Platforms

| ID | Name | Description |
|---|---|---|
| `claude-aws-bedrock` | AWS Bedrock | Amazon Bedrock Claude |
| `openai-azure` | Azure OpenAI | Microsoft Azure OpenAI Service |

### Third-Party Relay Services

Multiple third-party relay services are supported, including:
- PackyCode (`packycode`)
- SiliconFlow (`siliconflow`)
- AIGoCode (`aigocode`)
- And many more...

## CLI Commands

### List All Providers

```bash
codetrace provider list
```

### Show Provider Details

```bash
codetrace provider show claude-official
```

### List Available Presets

```bash
codetrace provider presets
```

### Import from Preset

```bash
codetrace provider import
# Interactive prompt will ask for preset ID and API key
```

Or with arguments:

```bash
codetrace provider import -p claude-official -k sk-ant-xxx
```

### Switch Active Provider

```bash
codetrace provider switch claude-official
```

### Add Custom Provider

```bash
codetrace provider add
# Interactive prompt for all configuration options
```

### Delete Provider

```bash
codetrace provider delete claude-official
# With confirmation prompt
```

Or skip confirmation:

```bash
codetrace provider delete claude-official --confirm
```

### Export Providers

```bash
codetrace provider export
# Exports to providers.json
```

Or specify output file:

```bash
codetrace provider export -o backup.json
```

### Import Providers from File

```bash
codetrace provider import-file backup.json
```

## Python API

### Basic Usage

```python
from src.services import (
    provider_manager,
    ProviderConfig,
    ProviderType,
    get_ai_client
)
from src.database import init_database

# Initialize database
init_database()

# Get active provider
active_provider = provider_manager.get_active_provider()

# Get AI client for active provider
ai_client = get_ai_client()

# Use the client
response = await ai_client.chat(messages, config)
```

### Add Custom Provider

```python
from src.services import ProviderConfig, ProviderType, provider_manager

config = ProviderConfig(
    id="my-custom-provider",
    name="My Custom Provider",
    provider_type=ProviderType.OPENAI,
    api_key="sk-xxx",
    api_endpoint="https://api.example.com/v1",
    model="gpt-4",
    temperature=0.7,
    max_tokens=4096,
)

provider_manager.add_provider(config)
```

### Switch Provider

```python
# Switch to a different provider
provider_manager.switch_provider("claude-official")

# Get the new active provider
active = provider_manager.get_active_provider()
print(f"Active provider: {active.name}")
```

### Import from Preset

```python
# Import from preset
config = provider_manager.import_from_preset(
    preset_id="claude-official",
    api_key="sk-ant-xxx"
)

# Customize if needed
config.name = "My Claude Instance"

# Add to database
provider_manager.add_provider(config)
```

### Export/Import

```python
# Export all providers
json_data = provider_manager.export_providers()
with open("backup.json", "w") as f:
    f.write(json_data)

# Import providers
with open("backup.json", "r") as f:
    json_data = f.read()
count = provider_manager.import_providers(json_data)
print(f"Imported {count} providers")
```

## Provider Configuration

Each provider configuration includes:

- **Basic Settings**
  - `id`: Unique identifier
  - `name`: Display name
  - `provider_type`: Type (CLAUDE, OPENAI, DEEPSEEK, CUSTOM)

- **API Configuration**
  - `api_key`: API key for authentication
  - `api_endpoint`: API endpoint URL
  - `model`: Model name

- **Generation Parameters**
  - `temperature`: Sampling temperature (0.0-1.0)
  - `max_tokens`: Maximum tokens to generate
  - `top_p`: Nucleus sampling parameter

- **Proxy Settings**
  - `proxy_url`: Proxy URL
  - `proxy_enabled`: Enable/disable proxy

- **Status**
  - `is_active`: Currently active provider
  - `is_enabled`: Provider is enabled

- **Custom Parameters**
  - `custom_params`: Dictionary for provider-specific options

## Database Storage

Provider configurations are stored in the `system_configs` table with keys prefixed by `provider_`:

```sql
SELECT * FROM system_configs WHERE key LIKE 'provider_%';
```

Active provider is stored separately:

```sql
SELECT * FROM system_configs WHERE key = 'active_provider_id';
```

## Integration with Services

### Conversation Service

The `ConversationService` automatically uses the active provider:

```python
from src.services import conversation_service

# No need to specify provider - uses active provider
response = await conversation_service.send_message(
    conversation_id=1,
    content="Hello!"
)
```

### Custom AI Client Creation

```python
from src.services import ai_client_factory, ProviderConfig

# Create client from specific config
config = ProviderConfig(...)
client = ai_client_factory.create_client(config)

# Or get client by provider ID
client = ai_client_factory.get_client_by_id("claude-official")
```

## Examples

### Example 1: Setup Multiple Providers

```python
from src.services import provider_manager, ProviderConfig, ProviderType

# Add Claude official
provider_manager.import_from_preset("claude-official", "sk-ant-xxx")

# Add OpenAI official
provider_manager.import_from_preset("openai-official", "sk-xxx")

# Add DeepSeek official
provider_manager.import_from_preset("deepseek-official", "sk-xxx")

# Switch between them as needed
provider_manager.switch_provider("claude-official")
```

### Example 2: Use Relay Service

```python
# Import from preset (e.g., PackyCode)
config = provider_manager.import_from_preset(
    "packycode",
    "your-api-key"
)
provider_manager.add_provider(config)
provider_manager.switch_provider("packycode")
```

### Example 3: Custom Provider with Proxy

```python
config = ProviderConfig(
    id="custom-proxy",
    name="Custom with Proxy",
    provider_type=ProviderType.OPENAI,
    api_key="sk-xxx",
    api_endpoint="https://api.example.com/v1",
    model="gpt-4",
    proxy_url="http://proxy.example.com:8080",
    proxy_enabled=True,
)

provider_manager.add_provider(config)
```

## Troubleshooting

### No Active Provider

If you get "No active provider" error:

```bash
# Check available providers
codetrace provider list

# Switch to a provider
codetrace provider switch <provider-id>
```

### Invalid API Key

Make sure the API key is set:

```bash
# Show provider details
codetrace provider show <provider-id>

# Re-import with correct key
codetrace provider import -p <preset-id> -k <api-key>
```

### Provider Not Working

Test the provider:

```python
from src.services import get_ai_client

client = get_ai_client()
if client:
    print(f"Active client: {type(client).__name__}")
else:
    print("No active client - check provider configuration")
```

## Migration from Old Config

If you were using the old `config_service` AI configuration:

```python
# Old way (still works but deprecated)
from src.services.config_service import config_service
config = config_service.get_config()

# New way (recommended)
from src.services import provider_manager
provider = provider_manager.get_active_provider()
```

The new provider system is backward compatible - old configurations will still work, but you're encouraged to migrate to the new provider system for better flexibility.
