FROM public.ecr.aws/zinclabs/zinc:0.3.5@sha256:647a5d6bbcb2e459f6ca6b11ad63daf31c22d33c99378f8394a11571813f7246 AS builder

FROM ubuntu:latest@sha256:4b1d0c4a2d2aaf63b37111f34eb9fa89fa1bf53dd6e4ca954d47caebca4005c2
COPY --from=builder /go/bin/zinc /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
