FROM public.ecr.aws/zinclabs/zinc:0.4.0@sha256:5cc7698024a0b9dce9b7f4d365de22b6694f91d04770eaecfd708ee9bbca7056 AS builder

FROM ubuntu:latest@sha256:9a0bdde4188b896a372804be2384015e90e3f84906b750c1a53539b585fbbe7f
COPY --from=builder /go/bin/zinc /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
