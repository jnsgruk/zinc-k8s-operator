FROM public.ecr.aws/zinclabs/zinc:0.3.6@sha256:12bcf58b10705717e26d19e08db91f443de769c030537e5cf4eec5678ed9db76 AS builder

FROM ubuntu:latest@sha256:27cb6e6ccef575a4698b66f5de06c7ecd61589132d5a91d098f7f3f9285415a9
COPY --from=builder /go/bin/zinc /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
