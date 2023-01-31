FROM public.ecr.aws/zinclabs/zinc:0.3.6@sha256:12bcf58b10705717e26d19e08db91f443de769c030537e5cf4eec5678ed9db76 AS builder

FROM ubuntu:latest@sha256:f05532b6a1dec5f7a77a8d684af87bc9cd1f2b32eab301c109f8ad151b5565d1
COPY --from=builder /go/bin/zinc /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
