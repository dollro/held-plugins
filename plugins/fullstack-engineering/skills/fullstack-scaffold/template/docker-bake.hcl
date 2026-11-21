# Production images, built once per commit by CI (task release:build-ci):
#   REGISTRY=registry.example.com/acme IMAGETAG=<sha> CACHE_REF=<branch> \
#     docker buildx bake --push ci
# Group `ci` adds the test image (stage `test`, FROM the production django
# stage) in the same run, so the shared layers are built once. The version is
# not baked in: a release copies the tested digest to its tag, and the deploy
# sets APP_VERSION at runtime. GIT_SHA is the image's only identity.
variable "REGISTRY" { default = "localhost:5000" }
variable "IMAGE_NAME" { default = "__PROJECT__" }
variable "IMAGETAG" { default = "dev" }
variable "GIT_SHA" { default = "unknown" }
# Comma-separated, e.g. "linux/amd64,linux/arm64" for ARM hosts. Buildx pushes one
# multi-platform image per tag; no manifest merging needed.
variable "PLATFORMS" { default = "linux/amd64" }
# Registry build cache per branch (slug), mode=max: cache-<ref>-<stage> in each
# image repository. Read the branch's own, then the integration branches'; write
# only the own. Empty (local builds): no registry cache. Never per commit: such
# refs always miss and fill the registry.
variable "CACHE_REF" { default = "" }
variable "CACHE_FALLBACK" { default = "develop,main" }

function "image" {
  params = [service]
  result = "${REGISTRY}/${IMAGE_NAME}-${service}"
}

function "cache_from" {
  params = [service, stage]
  result = CACHE_REF == "" ? [] : [
    for ref in distinct(concat([CACHE_REF], split(",", CACHE_FALLBACK))) :
    "type=registry,ref=${image(service)}:cache-${ref}-${stage}"
  ]
}

function "cache_to" {
  params = [service, stage]
  result = CACHE_REF == "" ? [] : [
    "type=registry,ref=${image(service)}:cache-${CACHE_REF}-${stage},mode=max"
  ]
}

group "default" {
  targets = [
    "django",
    # >>> realtime
    "realtime",
    # <<< realtime
  ]
}

# CI: the production images plus the test image of the same build.
group "ci" {
  targets = [
    "django",
    # >>> realtime
    "realtime",
    # <<< realtime
    "django-test",
  ]
}

target "_common" {
  context    = "."
  dockerfile = "docker/app/Dockerfile"
  platforms  = split(",", PLATFORMS)
  args       = { GIT_SHA = "${GIT_SHA}" }
  labels     = { "org.opencontainers.image.revision" = "${GIT_SHA}" }
}

target "django" {
  inherits   = ["_common"]
  target     = "django"
  tags       = ["${image("django")}:${IMAGETAG}"]
  cache-from = cache_from("django", "django")
  cache-to   = cache_to("django", "django")
}

# Never promoted or deployed; same repository, tag test-<sha>.
target "django-test" {
  inherits   = ["_common"]
  target     = "test"
  tags       = ["${image("django")}:test-${IMAGETAG}"]
  cache-from = cache_from("django", "test")
  cache-to   = cache_to("django", "test")
}

# >>> realtime
target "realtime" {
  inherits   = ["_common"]
  target     = "realtime"
  tags       = ["${image("realtime")}:${IMAGETAG}"]
  cache-from = cache_from("realtime", "realtime")
  cache-to   = cache_to("realtime", "realtime")
}
# <<< realtime
