# KAgent Vision

An AI-powered vision agent that captures photos from your webcam, transforms them into artwork with Nano Banana, animates them into video clips with Veo3, and interprets American Sign Language.

Built with Google ADK and MCP. Includes a custom web UI for demo and development.

## What It Does

KAgent Vision chains together four capabilities:

1. **Camera Control** -- Detect, open, and capture from webcams (including iPhone Continuity cameras)
2. **Nano Banana** -- Transform captures into AI-generated artwork via Gemini 3 Pro Image
3. **Veo3 Video** -- Animate images into ~8 second AI video clips via Veo 3.1
4. **ASL Interpreter** -- Understand American Sign Language from frame sequences, respond in ASL gloss

```
Webcam --> Capture --> Nano Banana (AI Image) --> Veo3 (AI Video)
  |
  +--> ASL Burst --> ASL Understand --> Transcript + Reply + Gloss
```

All outputs (photos, generated images, videos) are saved to the `outputs/` directory.

## Quick Start

### 1. Clone and set up the virtual environment

```bash
git clone https://github.com/automateyournetwork/kagent_vision.git
cd kagent_vision
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -e .
pip install -e servers/
```

### 3. Set your Gemini API key

```bash
export GEMINI_API_KEY="your-google-api-key-here"
```

You need a Google AI API key with access to:
- **Gemini 3 Pro Image Preview** (Nano Banana image generation)
- **Veo 3.1 Generate Preview** (video generation)
- **Gemini 2.0 Flash** (agent reasoning + ASL understanding)

Get a key at [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### 4. Launch

```bash
GOOGLE_API_KEY="$GEMINI_API_KEY" python run_local.py
```

Open **http://localhost:5001** in your browser.

That's it. The launcher starts everything automatically:
- ADK api_server on port 8080 (backend)
- Custom web UI on port 5001 (frontend)
- MCP vision server as a subprocess (camera + AI tools)

## How It Works

`run_local.py` is a FastAPI app that:
1. Spawns the ADK api_server as a subprocess with `MCP_LOCAL=1` (enables direct webcam access)
2. Waits for the ADK server to be ready
3. Serves the custom web UI at `/`
4. Proxies all API calls (`/api/*`) to the ADK backend, including SSE streaming
5. Serves generated files from `/outputs/`

The web UI (`static/index.html`) is a single-file app using Tailwind CSS with:
- Camera controls (detect, select, open)
- Quick action buttons for common workflows
- Chat interface with SSE streaming
- Inline display of generated images and videos
- Tool call indicators showing when the agent is calling AI tools

## Using the Web UI

### Camera Setup

1. Click **Detect Cameras** to find available cameras
2. Select a camera from the dropdown
3. Click **Open** to start the camera

### Quick Actions

| Button | What it does |
|--------|-------------|
| Take a photo | Captures a frame and saves to `outputs/` |
| Cyberpunk art | Transforms your latest photo into cyberpunk digital art |
| Watercolor | Transforms your latest photo into a watercolor painting |
| Make a video | Creates a short AI video from your latest image |
| Read ASL | Captures frames and interprets ASL signing |
| Stop camera | Releases the camera |

### Chat

Type any message in the input bar. The agent understands natural language and will pick the right tools. Examples:

```
Transform this photo into a Van Gogh painting
Make a cinematic video of this image, 16:9 widescreen
What images do I have in the outputs folder?
Open camera 0 with 1920x1080 resolution
```

## Project Structure

```
kagent-vision/
|-- run_local.py              # FastAPI launcher (starts everything)
|-- static/
|   |-- index.html            # Custom web UI (single file)
|-- kagent_vision/             # Agent package (Google ADK)
|   |-- agent.py               # Agent definition + system prompt
|   |-- mcp_tools.py           # MCP server wiring
|-- servers/                   # Vision MCP server
|   |-- vision_mcp/
|   |   |-- server.py          # FastMCP server (registers all tools)
|   |   |-- camera.py          # Camera control (OpenCV)
|   |   |-- banana.py          # Nano Banana image generation
|   |   |-- veo.py             # Veo3 video generation
|   |   |-- asl.py             # ASL understanding
|   |   |-- files.py           # Image file detection
|-- outputs/                   # All generated files land here
|-- pyproject.toml             # Agent dependencies
```

## MCP Tools

| Tool | Description | Requires API Key |
|------|-------------|:---:|
| `list_cameras` | Probe camera indexes, report which are available | No |
| `vision_start` | Open a camera with configurable size/fps/backend | No |
| `vision_status` | Check if camera is open, show properties | No |
| `vision_capture` | Capture a single frame to `outputs/` | No |
| `vision_burst` | Capture N frames at interval to `outputs/` | No |
| `vision_stop` | Release the camera | No |
| `list_images` | Scan a directory for image files | No |
| `banana_generate` | AI image generation/transformation (Gemini 3 Pro Image) | Yes |
| `veo_generate_video` | AI video generation (Veo 3.1) | Yes |
| `asl_understand` | ASL interpretation from frame sequence | Yes |

## Platform Notes

| Platform | Notes |
|----------|-------|
| macOS | Grant Camera permission to your terminal app. iPhone cameras appear as extra indexes. |
| Linux | User needs `/dev/video*` access (`sudo usermod -aG video $USER`). |
| Windows | Try `msmf` or `dshow` backends if `auto` fails. |

## License

Apache 2.0 -- see [LICENSE](LICENSE).
