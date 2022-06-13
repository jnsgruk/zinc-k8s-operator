FROM public.ecr.aws/zinclabs/zinc:0.2.4 AS builder

FROM ubuntu:latest
COPY --from=builder /go/bin/zinc /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
