############
# HOW TO RUN
# tgoodwin@cerulean:~/projects $ docker buildx build --build-arg VERSION=1.24 -t k8ssandra/cass-operator:1.24 -f controllers/cass-operator/sleeve/Dockerfile . --load
############
# Build the manager binary
FROM golang:1.23 AS builder
ARG TARGETOS
ARG TARGETARCH

WORKDIR /workspace
# Copy the Go Modules manifests
COPY controllers/cass-operator/go.mod go.mod
COPY controllers/cass-operator/go.sum go.sum
COPY sleeve/ sleeve/
# Remove the last line of go.mod
RUN sed -i '$ d' go.mod
RUN echo "replace github.com/tgoodwin/sleeve => ./sleeve" >> go.mod
# cache deps before building and copying source so that we don't need to re-download as much
# and so that source changes don't invalidate our downloaded layer
RUN go mod download

# Copy the go source
COPY controllers/cass-operator/cmd/ cmd/
COPY controllers/cass-operator/apis/ apis/
COPY controllers/cass-operator/pkg/ pkg/
COPY controllers/cass-operator/internal/ internal/

# Build
RUN CGO_ENABLED=0 GOOS=${TARGETOS:-linux} GOARCH=${TARGETARCH} go build -a -o manager cmd/main.go

# Build the UBI image
FROM redhat/ubi9-micro:latest

ARG VERSION

LABEL maintainer="DataStax, Inc <info@datastax.com>"
LABEL name="cass-operator"
LABEL vendor="DataStax, Inc"
LABEL sleeve="true"
LABEL release="${VERSION}"
LABEL version="${VERSION}"
LABEL summary="DataStax Kubernetes Operator for Apache Cassandra "
LABEL description="The DataStax Kubernetes Operator for Apache Cassandra®. This operator handles the provisioning and day to day management of Apache Cassandra based clusters. Features include configuration deployment, node remediation, and automatic upgrades."

WORKDIR /
COPY --from=builder /workspace/manager /manager
COPY controllers/cass-operator/LICENSE.txt /licenses/

USER 65532:65532

ENTRYPOINT ["/manager"]
