FROM public.ecr.aws/zinclabs/zinc:0.4.7@sha256:fefa9ee7256a3c9e7a4f95345265ddf03daa912c5662277860bcbbe77088e662 AS builder

FROM ubuntu:latest@sha256:6120be6a2b7ce665d0cbddc3ce6eae60fe94637c6a66985312d1f02f63cc0bcd
COPY --from=builder /go/bin/zincsearch /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
