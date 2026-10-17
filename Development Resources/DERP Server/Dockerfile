FROM golang:1.26-alpine AS build

ARG TAILSCALE_VERSION=v1.102.5

RUN CGO_ENABLED=0 go install tailscale.com/cmd/derper@${TAILSCALE_VERSION} \
    && CGO_ENABLED=0 go install tailscale.com/cmd/stunc@${TAILSCALE_VERSION}

FROM alpine:3.22

RUN apk add --no-cache ca-certificates

COPY --from=build /go/bin/derper /usr/local/bin/derper
COPY --from=build /go/bin/stunc /usr/local/bin/stunc

ENTRYPOINT ["/usr/local/bin/derper"]
