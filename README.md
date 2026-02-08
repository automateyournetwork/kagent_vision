# KAgent Vision

A [kagent](https://kagent.dev/) agent with full vision capabilities -- capture photos from your webcam or use existing images, transform them with Nano Banana (AI image generation), animate them into video clips with Veo3, and communicate via American Sign Language.

Built on the kagent framework (CNCF sandbox project) using Google ADK and MCP.

## What It Does

KAgent Vision is an autonomous AI agent that chains together four capabilities:

1. **Camera Control** -- Detect, open, and capture from webcams, iPhones, or USB cameras
2. **Image Files** -- Scan directories for existing photos to use as input
3. **Nano Banana** -- Transform captures into AI-generated artwork via Gemini Image Generation
4. **Veo3 Video** -- Animate images into ~8 second AI video clips via Veo 3
5. **ASL Interpreter** -- Understand American Sign Language from frame sequences, respond in ASL gloss

### Typical Pipeline

```
Webcam/Photo --> Capture --> Nano Banana (AI Image) --> Veo3 (AI Video)
     |
     +--> ASL Burst --> ASL Understand --> Transcript + Reply + Gloss
```

## Project Structure

```
kagent-vision/
|-- kagent_vision/             # Agent package (Google ADK)
|   |-- __init__.py
|   |-- agent.py               # Agent definition + system prompt
|   |-- mcp_tools.py           # MCP server wiring
|   |-- agent-card.json        # A2A protocol card
|
|-- servers/                   # Vision MCP server package
|   |-- vision_mcp/
|   |   |-- __init__.py
|   |   |-- __main__.py        # python -m vision_mcp entry point
|   |   |-- server.py          # FastMCP server (registers all tools)
|   |   |-- camera.py          # Camera control tools
|   |   |-- banana.py          # Nano Banana image generation
|   |   |-- veo.py             # Veo3 video generation
|   |   |-- asl.py             # ASL understanding
|   |   |-- files.py           # Image file detection
|   |-- pyproject.toml         # MCP server dependencies
|   |-- Dockerfile             # MCP server container
|   |-- config.yaml            # Agentgateway config
|
|-- k8s/                       # Kubernetes deployment manifests
|   |-- agent.yaml             # Agent CRD
|   |-- mcp-server.yaml        # MCPServer CRD
|   |-- model-config.yaml      # ModelConfig CRD
|   |-- secret.yaml            # API key secret template
|
|-- kagent.yaml                # kagent project manifest
|-- pyproject.toml             # Agent dependencies
|-- Dockerfile                 # Agent container
|-- docker-compose.yaml        # Local development orchestration
|-- LICENSE                    # Apache 2.0
```

## Prerequisites

- **Python 3.11+**
- **Docker** and **Docker Compose** (for local development)
- **kagent CLI** ([install guide](https://kagent.dev/docs/kagent/getting-started/local-development))
- **Google/Gemini API Key** with access to:
  - Gemini 2.5 Flash Image Preview (for Nano Banana)
  - Veo 3.1 Generate Preview (for video generation)
  - Gemini 2.0 Flash (for ASL understanding)
- **Webcam** (optional -- you can also use static image files)

## Getting Started

### Option A: Local Development with kagent CLI

This is the recommended way to get started.

#### 1. Install kagent CLI

```bash
# Follow the kagent installation guide:
# https://kagent.dev/docs/kagent/getting-started/local-development
```

#### 2. Set your API key

```bash
export GEMINI_API_KEY="your-google-api-key-here"
```

#### 3. Build the project

```bash
cd kagent-vision
kagent build
```

#### 4. Run locally

```bash
kagent run
```

This launches docker-compose with the agent (port 8080) and the MCP server sidecar (port 3000 internal), plus an interactive chat TUI.

#### 5. Talk to the agent

In the chat UI:

```
> List my cameras
> Open camera 0
> Take a photo
> Transform this photo into a cyberpunk portrait
> Make a video clip of this image coming to life
> Stop the camera
```

### Option B: Manual Docker Compose

If you don't have the kagent CLI, you can use docker-compose directly.

#### 1. Set your API key

```bash
export GEMINI_API_KEY="your-google-api-key-here"
```

#### 2. Build and run

```bash
docker compose build
docker compose up
```

The agent will be available at `http://localhost:8080`.

**Note on webcam access**: The `docker-compose.yaml` maps `/dev/video0` into the MCP server container. This works on Linux. On macOS/Windows Docker Desktop, direct webcam passthrough is not supported -- use the `list_images` tool with existing photos in the `./outputs` directory instead.

### Option C: Run MCP Server Standalone (No Docker)

For development or when you need direct webcam access without containers:

#### 1. Set up the MCP server

```bash
cd servers
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

#### 2. Set your API key

```bash
export GEMINI_API_KEY="your-google-api-key-here"
```

#### 3. Run the MCP server

```bash
python -m vision_mcp
```

The server communicates over stdio using the MCP protocol. You can connect any MCP-compatible client to it.

### Option D: Deploy to Kubernetes

For production deployment on a Kubernetes cluster with kagent installed:

#### 1. Install kagent on your cluster

```bash
helm install kagent-crds oci://ghcr.io/kagent-dev/kagent/helm/kagent-crds \
  --namespace kagent --create-namespace

helm install kagent oci://ghcr.io/kagent-dev/kagent/helm/kagent \
  --namespace kagent \
  --set providers.default=gemini \
  --set providers.gemini.apiKey=$GEMINI_API_KEY
```

#### 2. Create the API key secret

```bash
kubectl create secret generic kagent-gemini -n kagent \
  --from-literal=GOOGLE_API_KEY="$GEMINI_API_KEY"
```

#### 3. Build and push the images

```bash
kagent build
docker tag localhost:5001/kagent-vision:latest your-registry/kagent-vision:latest
docker tag localhost:5001/kagent-vision-mcp:latest your-registry/kagent-vision-mcp:latest
docker push your-registry/kagent-vision:latest
docker push your-registry/kagent-vision-mcp:latest
```

#### 4. Apply the manifests

```bash
kubectl apply -f k8s/model-config.yaml
kubectl apply -f k8s/mcp-server.yaml
kubectl apply -f k8s/agent.yaml
```

#### 5. Access via the dashboard

```bash
kagent dashboard
```

**Note**: Webcam access from within Kubernetes pods requires node-level device passthrough configuration. For cluster deployments, the `list_images` tool with pre-staged photos is the more practical input method.

## MCP Tools Reference

| Tool | Description | Requires API Key |
|------|-------------|:---:|
| `list_cameras` | Probe camera indexes, report which are available | No |
| `vision_start` | Open a camera with configurable size/fps/backend | No |
| `vision_status` | Check if camera is open, show properties | No |
| `vision_capture` | Capture a single frame, save to disk | No |
| `vision_burst` | Capture N frames at interval, save to disk | No |
| `vision_stop` | Release the camera | No |
| `list_images` | Scan a directory for image files | No |
| `banana_generate` | AI image generation/transformation (Nano Banana) | Yes |
| `veo_generate_video` | AI video generation (Veo3) | Yes |
| `asl_understand` | ASL interpretation from frame sequence | Yes |

## Example Conversations

### Photo to AI Art to Video

```
User: List my cameras
Agent: [calls list_cameras] Found camera at index 0 (640x480, 30fps)

User: Open it and take a photo
Agent: [calls vision_start, vision_capture] Captured: frame_20260208_143022_001.jpg

User: Transform this into a watercolor painting
Agent: [calls banana_generate] Saved: banana_20260208_143025_001.png

User: Animate that painting into a video
Agent: [calls veo_generate_video] Saved: veo_20260208_143312_001.mp4

User: Stop the camera
Agent: [calls vision_stop] Camera released.
```

### Using Existing Photos

```
User: What images are in my current directory?
Agent: [calls list_images] Found 3 images: sunset.jpg, portrait.png, sketch.webp

User: Transform sunset.jpg into a Van Gogh style painting
Agent: [calls banana_generate with input_paths=["sunset.jpg"]]
       Saved: banana_20260208_150001_001.png

User: Make a cinematic video from it, 16:9 widescreen
Agent: [calls veo_generate_video with aspect_ratio="16:9"]
       Saved: veo_20260208_150245_001.mp4
```

### ASL Mode

```
User: Start the camera and let's chat in ASL
Agent: [calls vision_start, vision_burst] Captured 10 frames
       [calls asl_understand]
       Transcript: "Hello, what is your name?"
       Reply: "Hi! I'm KAgent Vision. Nice to meet you!"
       ASL Gloss: "HELLO ME NAME K-A-G-E-N-T V-I-S-I-O-N NICE MEET YOU"
```

## Platform Notes

| Platform | Camera Backend | Notes |
|----------|---------------|-------|
| macOS | `avfoundation` | Grant Camera permission in System Settings. iPhone cameras appear as extra indexes. |
| Linux | `v4l2` | User needs `/dev/video*` access (`sudo usermod -aG video $USER`). |
| Windows | `msmf` or `dshow` | Try both if `auto` fails. |
| WSL2 | `v4l2` | Requires USB device passthrough configuration. |
| Docker | varies | Linux: use `--device /dev/video0`. macOS/Windows: use `list_images` with static files. |

## Architecture

```
+---------------------------+       +---------------------------+
|   kagent_vision (Agent)   |       |   vision-mcp (MCP Server) |
|   Google ADK + Gemini     |<----->|   FastMCP + OpenCV        |
|   Port 8080               | HTTP  |   Port 3000 (internal)    |
|                           | /mcp  |                           |
|   System prompt defines   |       |   camera.py  (capture)    |
|   all workflows and       |       |   banana.py  (image gen)  |
|   tool orchestration      |       |   veo.py     (video gen)  |
|                           |       |   asl.py     (ASL)        |
|                           |       |   files.py   (file scan)  |
+---------------------------+       +---------------------------+
              |                                   |
              v                                   v
      Google Gemini API                    Webcam / Files
      (Image Gen, Veo3,                   (OpenCV capture)
       ASL Understanding)
```

## Safety

- Get consent before capturing or animating real people.
- Always stop the camera when done.
- Avoid prompts that generate personal likeness without permission.
- API keys are stored as environment variables or Kubernetes secrets -- never hardcode them.

## License

Apache 2.0 -- see [LICENSE](LICENSE).
