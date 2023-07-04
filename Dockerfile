FROM public.ecr.aws/zinclabs/zinc:0.4.7@sha256:fefa9ee7256a3c9e7a4f95345265ddf03daa912c5662277860bcbbe77088e662 AS builder

FROM ubuntu:latest@sha256:0bced47fffa3361afa981854fcabcd4577cd43cebbb808cea2b1f33a3dd7f508
COPY --from=builder /go/bin/zincsearch /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
