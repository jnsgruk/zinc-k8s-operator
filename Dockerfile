FROM public.ecr.aws/zinclabs/zinc:0.3.6@sha256:647a5d6bbcb2e459f6ca6b11ad63daf31c22d33c99378f8394a11571813f7246 AS builder

FROM ubuntu:latest@sha256:27cb6e6ccef575a4698b66f5de06c7ecd61589132d5a91d098f7f3f9285415a9
COPY --from=builder /go/bin/zinc /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
