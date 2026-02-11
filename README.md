# KAgent Vision

An AI-powered vision agent that captures photos from your webcam (or uploaded images), transforms them into artwork with Nano Banana, animates them into video clips with Veo3, and interprets American Sign Language.

Built with Google ADK and MCP for the [AI / MCP Hackathon](https://aihackathon.dev/). Includes a custom web UI.

## What It Does

KAgent Vision chains together four capabilities:

1. **Camera Control** -- Detect, open, and capture from webcams (including iPhone Continuity cameras)
2. **Nano Banana** -- Transform captures into AI-generated artwork via Gemini 3 Pro Image (20+ styles)
3. **Veo3 Video** -- Animate images into ~8 second AI video clips via Veo 3.1 (15+ effects)
4. **ASL Conversation** -- Sign in ASL via your webcam and the agent replies in natural language

You can also **upload any image** instead of using a webcam.

```
Webcam / Upload --> Capture --> Nano Banana (AI Image) --> Veo3 (AI Video)
       |
       +--> ASL Burst --> ASL Understand --> Transcript + Reply + Gloss
```

All outputs (photos, generated images, videos) are saved to the `outputs/` directory and displayed inline in the chat.

## Requirements

- **Python 3.11+** (3.12 recommended)
- **Google AI API key** with access to Gemini 3 Pro Image, Veo 3.1, and Gemini 2.0 Flash (a paid plan or credits may be required)
- **Webcam** (optional -- you can upload images instead)

## Quick Start

### 1. Clone and create virtual environment

```bash
git clone https://github.com/automateyournetwork/kagent_vision.git
cd kagent_vision
python3.12 -m venv .venv
source .venv/bin/activate
```

> **Note:** You must use Python 3.11 or higher. If `python3.12` is not available, use `python3.11` or `python3` (check with `python3 --version`).

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -e .
pip install -e servers/
```

### 3. Set your Gemini API key

Get a key at [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

```bash
export GEMINI_API_KEY="your-google-api-key-here"
```

### 4. Launch

```bash
GOOGLE_API_KEY="$GEMINI_API_KEY" python run_local.py
```

Open **http://localhost:5001** in your browser. That's it.

The launcher starts everything automatically:
- ADK api_server on port 8080 (backend)
- Custom web UI on port 5001 (frontend)
- MCP vision server as a subprocess (camera + AI tools)

## Using the Web UI

### Camera Setup

1. Click **Detect Cameras** to find available cameras
2. Select a camera from the dropdown
3. Click **Open** to start the camera

### Capture / Upload

- **Take a Photo** -- captures a frame from your webcam
- **Upload Image** -- upload any image from your computer

### Nano Banana (20+ styles)

Pick a style from the dropdown and click **Generate**:

Cyberpunk, Watercolor, Van Gogh, Pixar 3D, Anime, Comic Book, Pencil Sketch, Synthwave, Renaissance, Pop Art, Studio Ghibli, Vintage Poster, Stained Glass, Low-Poly, Surrealist, Pixel Art, Japanese Woodblock, Gothic Fantasy, Line Art, Cinematic Movie Still

### Veo3 Video (15+ effects)

Pick an effect from the dropdown and click **Generate**:

Gentle Camera Pan, Dramatic Zoom, Cinematic Dolly, Subtle Motion, Rain & Moody Lighting, Magical Sparkles, Ocean Waves, Timelapse Sunrise, Falling Snow, Fire & Embers, Music Video, Dreamy Lens Flares, Drone Flyover, Vintage Film, Glitch / VHS

### ASL Conversation

Select a recording duration (30, 90, or 120 seconds), click **Record**, and sign in ASL via your webcam. The agent reads your signing and replies in natural language.

### Free-Form Chat

Type anything in the input bar -- the agent understands natural language:

```
Transform this photo into a Van Gogh painting
Make a cinematic video of this image, 16:9 widescreen
What images do I have in the outputs folder?
Open camera 1 with avfoundation backend
```

## How It Works

`run_local.py` is a FastAPI app that:
1. Spawns the ADK api_server as a subprocess with `MCP_LOCAL=1` (enables direct webcam access)
2. Waits for the ADK server to be ready
3. Serves the custom web UI at `/`
4. Proxies all API calls (`/api/*`) to the ADK backend, including SSE streaming
5. Serves generated files from `/outputs/` and handles image uploads

The web UI (`static/index.html`) is a single-file app using Tailwind CSS with:
- Camera controls and image upload
- Dropdown menus with pre-built prompts for Nano Banana and Veo3
- Chat interface with SSE streaming
- Inline display of generated images and videos
- Tool call indicators showing when the agent is calling AI tools

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
