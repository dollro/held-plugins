# Render performance (HyperFrames on Linux)

Load this when `npx hyperframes render` is slow, ignores the GPU, or produces files much larger than expected. Measured with hyperframes 0.9.104 on a Linux hybrid-GPU laptop (Intel iGPU + NVIDIA dGPU); re-check the numbers after a HyperFrames or Chrome upgrade.

## 1. Read the log first

Render with the log kept (`... render ... > render.log 2>&1`). These lines name the slow path:

| Log line | Meaning | Section |
|---|---|---|
| `[HyperShader] page-side compositing requested but drawElementImage/WebGL is not available` | shader transitions blend on the slow Node-side path for the whole film | 2 |
| `capture_hdr_layered` in a `Render:trace` line (instead of `capture_disk`) | same; layered capture | 2 |
| `Reduced auto worker count … reasons: ["shader-transitions"]` | workers capped (6 → 2); expected while the film has a shader transition | 6 |
| `browserGpuMode probe → hardware (… renderer="ANGLE (Intel …")` | Chrome runs on the iGPU, not the dGPU | 3 |
| `No GPU encoder works on this machine; encoding with libx264` | `--gpu` silently fell back to the CPU encoder | 4 |
| `… can be changed by another user account, so HyperFrames will not install or run code from it` | cache dir permissions (`~/.cache` group-writable) | 7 |

Progress lines (`@hf-progress {"done":…,"total":…}`) and the `stage still running` heartbeats (`framesCompleted`, `stageElapsedMs`) give frames per second; compare runs at equal `stageElapsedMs`.

## 2. Shader transitions and Chrome 157+

`@hyperframes/shader-transitions` only composites in the page when the canvas exposes `layoutSubtree`, `drawElementImage` and WebGL. Chrome 157+ replaced the `layoutsubtree` attribute with `content="drawable"`, so the check fails on the Chrome that `hyperframes browser ensure` installs (158) and the whole render takes the Node-side layered path. Upstream: https://github.com/heygen-com/hyperframes/issues/9032.

Until that is fixed, pin a Chrome for Testing **headless shell ≤ 156** and point HyperFrames at it:

```bash
# pick a version from https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json
V=156.0.8078.80
mkdir -p ~/.cache/hyperframes-pinned/$V && cd ~/.cache/hyperframes-pinned/$V
curl -sSLO https://storage.googleapis.com/chrome-for-testing-public/$V/linux64/chrome-headless-shell-linux64.zip
unzip -q chrome-headless-shell-linux64.zip && rm chrome-headless-shell-linux64.zip
export HYPERFRAMES_BROWSER_PATH=~/.cache/hyperframes-pinned/$V/chrome-headless-shell-linux64/chrome-headless-shell
```

Check: the HyperShader warning is gone and capture runs as `capture_disk`. Measured: 1.5-5 fps → ~24 fps on a 5040-frame 1080p30 film (20-55 min → ~4 min). This is the change that matters; everything below is minor.

The pinned build gets no security updates; use it only for rendering local compositions. Drop the pin once the issue is fixed and the check passes on the default browser.

## 3. Chrome on the NVIDIA dGPU (hybrid laptops)

Headless Chrome opens the first render node (`/dev/dri/renderD128`, usually the iGPU). To use the NVIDIA card, set PRIME offload variables for the render:

```bash
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia \
__EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json \
npx hyperframes render --browser-gpu ...
```

Check: the probe line names the NVIDIA GPU, and `nvidia-smi pmon -c 1` lists `chrome-headless`. On its own this did not speed up capture measurably; it matters together with section 2.

## 4. `--gpu` falls back to libx264 (NVENC probe timeout)

HyperFrames probes each hardware encoder with a tiny ffmpeg encode and kills it after **2 s**. On hybrid laptops the dGPU runtime-suspends after a few idle seconds; a cold NVENC start took 3.2 s (warm: 0.4 s), so the probe times out and `--gpu` silently uses libx264. It looks intermittent because it passes whenever the GPU happens to be awake.

Diagnose with `HYPERFRAMES_DEBUG_GPU_PROBE=1` (logs VAAPI/QSV errors, but a timed-out NVENC probe prints nothing) and by timing the probe yourself:

```bash
cat /sys/bus/pci/devices/0000:01:00.0/power/runtime_status   # suspended = cold
time ffmpeg -hide_banner -loglevel error -f lavfi -i color=size=320x240:rate=1:duration=1 \
  -frames:v 1 -an -c:v h264_nvenc -f null -
```

Workaround: run that same ffmpeg line immediately before `npx hyperframes render --gpu`, so the dGPU is awake when the probe runs. (Alternatives: NVIDIA persistence mode, or `power/control=on`; both need root and cost battery.) Check: the encoder ffmpeg process runs `-c:v h264_nvenc`.

## 5. NVENC file size: set `--crf`

HyperFrames hands the same quality number to every encoder: `--quality high` → `-crf 15` for libx264 (with `aq-mode=3` and deblock tuning), `-cq 15` for NVENC (`-preset p4 -bf 0`, no AQ). The numbers are not equivalent; NVENC at cq 15 spends far more bits for the same quality. Measured on a 40 s excerpt against a lossless reference:

| Encoder setting | Bitrate | SSIM |
|---|---|---|
| libx264 crf 15 | 5.3 Mbit/s | 0.9874 |
| NVENC cq 15 (default) | 9.2 Mbit/s | 0.9881 |
| NVENC cq 19 | 6.5 Mbit/s | 0.9875 |
| NVENC cq 21 | 5.1 Mbit/s | 0.9870 |
| NVENC cq 23 | 3.9 Mbit/s | 0.9865 |

`--crf N` overrides the quality number and so becomes `-cq N` on NVENC. With `--gpu`, pass `--crf 21` to match libx264 crf 15 in size and measured quality. If the NVENC probe fails (section 4), libx264 then also gets crf 21, a step below the default. Tuned NVENC options (p7, spatial/temporal AQ, lookahead, B-frames) gained under 0.001 SSIM and cannot be passed through the CLI anyway. Judge the result by eye at phone and full size; SSIM is a guide, not the sign-off.

Expected gain from NVENC: small (~11 % total time, 3:59 → 3:32), because encoding already runs alongside capture and capture is the bottleneck.

## 6. Worker count

A composition with a shader transition caps auto workers at 2 ("compositor starvation"). Forcing more with `--workers` risks stalls. If render time matters more than the effect, a CSS crossfade instead of the shader transition lifts the cap; that changes the look, so it is a direction decision for the user, not a silent swap.

## 7. Cache directory permissions

HyperFrames refuses to install or run Chrome from a cache directory other accounts can write to. If `~/.cache` is group- or world-writable and owned by the user: `chmod go-w ~/.cache`, then `npx hyperframes browser ensure`. Otherwise set `HYPERFRAMES_CACHE_DIR` to a private directory.

## 8. One script for the project

Put the working combination into the project's `package.json` so every render uses it:

```json
"render:fast": "ffmpeg -hide_banner -loglevel error -f lavfi -i color=size=320x240:rate=1:duration=1 -frames:v 1 -an -c:v h264_nvenc -f null - ; HYPERFRAMES_BROWSER_PATH=$HOME/.cache/hyperframes-pinned/156.0.8078.80/chrome-headless-shell-linux64/chrome-headless-shell __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json npx --yes hyperframes@<pinned-version> render --gpu --browser-gpu --quality high --crf 21 -o ./renders/<cut>-vN.mp4"
```

Drop the parts that do not apply (no NVIDIA dGPU: remove the ffmpeg warm-up, the PRIME variables, `--gpu` and `--crf 21`). When bumping the HyperFrames pin, bump it here too and re-check sections 2 and 4.
