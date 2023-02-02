FROM public.ecr.aws/zinclabs/zinc:0.3.6@sha256:12bcf58b10705717e26d19e08db91f443de769c030537e5cf4eec5678ed9db76 AS builder

FROM ubuntu:latest@sha256:9a0bdde4188b896a372804be2384015e90e3f84906b750c1a53539b585fbbe7f
COPY --from=builder /go/bin/zinc /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
