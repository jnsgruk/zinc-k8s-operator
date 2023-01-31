FROM public.ecr.aws/zinclabs/zinc:0.3.6@sha256:12bcf58b10705717e26d19e08db91f443de769c030537e5cf4eec5678ed9db76 AS builder

FROM ubuntu:latest@sha256:9dc05cf19a5745c33b9327dba850480dae80310972dea9b05052162e7c7f2763
COPY --from=builder /go/bin/zinc /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
