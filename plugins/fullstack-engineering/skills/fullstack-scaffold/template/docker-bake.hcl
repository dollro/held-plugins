# Production images. Built by CI on a version tag:
#   REGISTRY=ghcr.io/org IMAGETAG=v1.2.3 docker buildx bake --push
variable "REGISTRY" { default = "localhost:5000" }
variable "IMAGE_NAME" { default = "__PROJECT__" }
variable "IMAGETAG" { default = "dev" }
# Comma-separated, e.g. "linux/amd64,linux/arm64" for ARM hosts. Buildx pushes one
# multi-platform image per tag; no manifest merging needed.
variable "PLATFORMS" { default = "linux/amd64" }

function "image" {
  params = [service]
  result = "${REGISTRY}/${IMAGE_NAME}-${service}"
}

group "default" {
  targets = [
    "django",
    # >>> realtime
    "realtime",
    # <<< realtime
  ]
}

target "_common" {
  context    = "."
  dockerfile = "docker/app/Dockerfile"
  platforms  = split(",", PLATFORMS)
  args       = { APP_VERSION = "${IMAGETAG}" }
  labels     = { "org.opencontainers.image.version" = "${IMAGETAG}" }
}

target "django" {
  inherits   = ["_common"]
  target     = "django"
  tags       = ["${image("django")}:${IMAGETAG}"]
  cache-from = ["type=registry,ref=${image("django")}:buildcache"]
  cache-to   = ["type=registry,ref=${image("django")}:buildcache,mode=max"]
}

# >>> realtime
target "realtime" {
  inherits   = ["_common"]
  target     = "realtime"
  tags       = ["${image("realtime")}:${IMAGETAG}"]
  cache-from = ["type=registry,ref=${image("realtime")}:buildcache"]
  cache-to   = ["type=registry,ref=${image("realtime")}:buildcache,mode=max"]
}
# <<< realtime
